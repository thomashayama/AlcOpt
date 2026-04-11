"""One-shot migration: legacy schema → containers/events schema.

Reads ``data/alcopt.db`` (legacy: vessels, bottles, fermentation_vessel_logs,
bottle_log, fermentation_ingredients, bottle_ingredients) and writes a fresh
``data/alcopt_v2.db`` with the new schema (containers, container_fermentation_logs,
ingredient_additions). The source DB is never mutated.

After running, inspect the output and (if happy) swap manually:

    mv data/alcopt.db data/alcopt.db.pre-refactor
    mv data/alcopt_v2.db data/alcopt.db
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import date, datetime, time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from alcopt.database.models import (  # noqa: E402
    Base,
    Container,
    ContainerFermentationLog,
    Fermentation,
    Ingredient,
    IngredientAddition,
    MassMeasurement,
    Review,
    SpecificGravityMeasurement,
)

SOURCE_DB = ROOT / "data" / "alcopt.db"
TARGET_DB = ROOT / "data" / "alcopt_v2.db"

# Vessels keep their IDs; bottles are offset so vessel-1 and bottle-1 don't collide.
# Will be filled in at runtime once we read the source DB.
BOTTLE_ID_OFFSET = 0


def to_dt(value, default_time=time(12, 0, 0)):
    """Promote a date-or-datetime-or-iso-string to a datetime at noon UTC.

    SQLite stores DATE columns as ISO strings. The legacy schema uses DATE
    everywhere; the new schema uses DATETIME for event timestamps.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, default_time)
    if isinstance(value, str):
        # ISO date or datetime
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.combine(date.fromisoformat(value), default_time)
    raise TypeError(f"Cannot coerce {value!r} (type {type(value)}) to datetime")


def to_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return datetime.fromisoformat(value).date()
    raise TypeError(f"Cannot coerce {value!r} (type {type(value)}) to date")


def fetch_all(src: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    cur = src.cursor()
    cur.execute(sql)
    return cur.fetchall()


def main():
    if not SOURCE_DB.exists():
        print(f"Source DB not found: {SOURCE_DB}", file=sys.stderr)
        sys.exit(1)

    if TARGET_DB.exists():
        print(f"Removing previous target DB: {TARGET_DB}")
        TARGET_DB.unlink()

    print(f"Source: {SOURCE_DB}")
    print(f"Target: {TARGET_DB}")
    print()

    src = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row

    target_engine = create_engine(f"sqlite:///{TARGET_DB}")
    Base.metadata.create_all(target_engine)
    Session = sessionmaker(bind=target_engine)
    db = Session()

    warnings: list[str] = []

    try:
        # ---------- 1. Copy unchanged tables ----------
        print("== Copying unchanged tables ==")

        for row in fetch_all(src, "SELECT * FROM ingredients"):
            db.add(
                Ingredient(
                    id=row["id"],
                    name=row["name"],
                    sugar_content=row["sugar_content"],
                    ingredient_type=row["ingredient_type"],
                    density=row["density"],
                    price=row["price"],
                    notes=row["notes"],
                )
            )
        db.flush()
        ingredient_count = db.query(Ingredient).count()
        print(f"  ingredients: {ingredient_count}")

        for row in fetch_all(src, "SELECT * FROM fermentations"):
            db.add(
                Fermentation(
                    id=row["id"],
                    start_date=to_date(row["start_date"]),
                    end_date=to_date(row["end_date"]),
                    end_mass=row["end_mass"],
                )
            )
        db.flush()
        fermentation_count = db.query(Fermentation).count()
        print(f"  fermentations: {fermentation_count}")

        for row in fetch_all(src, "SELECT * FROM specific_gravity_measurements"):
            db.add(
                SpecificGravityMeasurement(
                    id=row["id"],
                    fermentation_id=row["fermentation_id"],
                    measurement_date=to_date(row["measurement_date"]),
                    specific_gravity=row["specific_gravity"],
                )
            )
        db.flush()
        sg_count = db.query(SpecificGravityMeasurement).count()
        print(f"  specific_gravity_measurements: {sg_count}")

        for row in fetch_all(src, "SELECT * FROM mass_measurements"):
            db.add(
                MassMeasurement(
                    id=row["id"],
                    fermentation_id=row["fermentation_id"],
                    measurement_date=to_date(row["measurement_date"]),
                    mass=row["mass"],
                )
            )
        db.flush()
        mass_count = db.query(MassMeasurement).count()
        print(f"  mass_measurements: {mass_count}")

        # ---------- 2. Build containers from vessels + bottles ----------
        print()
        print("== Building containers ==")

        vessels = fetch_all(src, "SELECT * FROM vessels ORDER BY id")
        bottles = fetch_all(src, "SELECT * FROM bottles ORDER BY id")

        max_vessel_id = max((v["id"] for v in vessels), default=0)
        global BOTTLE_ID_OFFSET
        BOTTLE_ID_OFFSET = max_vessel_id
        print(f"  vessel id range: 1..{max_vessel_id}")
        print(f"  bottle id offset: +{BOTTLE_ID_OFFSET}")

        for v in vessels:
            db.add(
                Container(
                    id=v["id"],
                    container_type="carboy",
                    volume_liters=v["volume_liters"],
                    material=v["material"],
                    empty_mass=v["empty_mass"],
                    date_added=to_date(v["date_added"]),
                )
            )

        for b in bottles:
            db.add(
                Container(
                    id=b["id"] + BOTTLE_ID_OFFSET,
                    container_type="bottle",
                    volume_liters=b["volume_liters"],
                    material=None,
                    empty_mass=b["empty_mass"],
                    date_added=to_date(b["date_added"]),
                )
            )
        db.flush()
        container_count = db.query(Container).count()
        print(
            f"  containers: {container_count} (vessels {len(vessels)} + bottles {len(bottles)})"
        )

        # ---------- 3. Build container_fermentation_logs ----------
        print()
        print("== Building container_fermentation_logs ==")

        # 3a. Vessel logs with end_date backfill.
        # Group by vessel_id, sort by start_date, fill end_date = next start_date.
        # The very last row's end_date stays NULL only if vessels.fermentation_id is set.
        vessel_logs_raw = fetch_all(
            src,
            "SELECT * FROM fermentation_vessel_logs ORDER BY vessel_id, start_date, id",
        )
        vessel_current_ferm = {v["id"]: v["fermentation_id"] for v in vessels}

        # Bucket by vessel_id
        by_vessel: dict[int, list[sqlite3.Row]] = {}
        for r in vessel_logs_raw:
            by_vessel.setdefault(r["vessel_id"], []).append(r)

        vessel_log_inserted = 0
        for vessel_id, rows in by_vessel.items():
            for i, r in enumerate(rows):
                start = to_dt(r["start_date"])
                end = to_dt(r["end_date"])
                if end is None:
                    if i + 1 < len(rows):
                        # Backfill from next row
                        next_start = to_dt(rows[i + 1]["start_date"])
                        end = next_start
                        warnings.append(
                            f"Backfilled end_date for vessel_log id={r['id']} "
                            f"(vessel {vessel_id}) -> {end.isoformat()}"
                        )
                    else:
                        # Last row: leave open only if vessel currently holds this ferm
                        cur_ferm = vessel_current_ferm.get(vessel_id)
                        if cur_ferm != r["fermentation_id"]:
                            # Vessel is now empty or holds something else; close at start.
                            # Best we can do without more info: set end = start.
                            end = start
                            warnings.append(
                                f"Closed dangling final vessel_log id={r['id']} "
                                f"(vessel {vessel_id}) at start_date — vessel.fermentation_id "
                                f"({cur_ferm}) does not match log's fermentation_id "
                                f"({r['fermentation_id']})"
                            )
                db.add(
                    ContainerFermentationLog(
                        id=r["id"],
                        container_id=vessel_id,
                        fermentation_id=r["fermentation_id"],
                        start_date=start,
                        end_date=end,
                        source_container_id=None,
                        amount=None,
                        unit=None,
                        stage="primary",
                    )
                )
                vessel_log_inserted += 1

        # 3b. Bottle logs.
        max_vlog_id = max((r["id"] for r in vessel_logs_raw), default=0)
        bottle_logs_raw = fetch_all(src, "SELECT * FROM bottle_log ORDER BY id")
        bottle_current_ferm_by_bottle_id = {
            b["id"]: b["fermentation_id"] for b in bottles
        }
        bottle_log_inserted = 0
        for r in bottle_logs_raw:
            new_id = max_vlog_id + r["id"]
            container_id = r["bottle_id"] + BOTTLE_ID_OFFSET
            start = to_dt(r["bottling_date"])
            # Bottle log closes only if the bottle no longer holds this fermentation.
            cur_ferm = bottle_current_ferm_by_bottle_id.get(r["bottle_id"])
            end = None if cur_ferm == r["fermentation_id"] else start
            if end is not None:
                warnings.append(
                    f"Closed bottle_log id={r['id']} at start — bottle "
                    f"{r['bottle_id']} no longer holds fermentation {r['fermentation_id']}"
                )
            db.add(
                ContainerFermentationLog(
                    id=new_id,
                    container_id=container_id,
                    fermentation_id=r["fermentation_id"],
                    start_date=start,
                    end_date=end,
                    source_container_id=r["vessel_id"],
                    amount=r["amount"],
                    unit=r["unit"],
                    stage="bottled",
                )
            )
            bottle_log_inserted += 1

        db.flush()
        log_count = db.query(ContainerFermentationLog).count()
        print(
            f"  container_fermentation_logs: {log_count} (vessel {vessel_log_inserted} + bottle {bottle_log_inserted})"
        )

        # ---------- 4. Build ingredient_additions ----------
        print()
        print("== Building ingredient_additions ==")

        # For each old fermentation_ingredient row, find the container that held
        # the fermentation at added_at.
        all_logs = (
            db.query(ContainerFermentationLog)
            .order_by(
                ContainerFermentationLog.fermentation_id,
                ContainerFermentationLog.start_date,
            )
            .all()
        )
        logs_by_ferm: dict[int, list[ContainerFermentationLog]] = {}
        for log in all_logs:
            logs_by_ferm.setdefault(log.fermentation_id, []).append(log)

        def resolve_container(fermentation_id: int, added_at: datetime) -> int | None:
            candidates = logs_by_ferm.get(fermentation_id, [])
            if not candidates:
                return None
            # Containing window first
            containing = [
                log
                for log in candidates
                if log.start_date <= added_at
                and (log.end_date is None or added_at < log.end_date)
            ]
            if len(containing) == 1:
                return containing[0].container_id
            if len(containing) > 1:
                # Pick the latest start_date
                pick = max(containing, key=lambda log: log.start_date)
                warnings.append(
                    f"Multiple log windows match fermentation {fermentation_id} at "
                    f"{added_at.isoformat()}; chose container {pick.container_id}"
                )
                return pick.container_id
            # Fallback: nearest log row
            warnings.append(
                f"No log window contains fermentation {fermentation_id} at "
                f"{added_at.isoformat()}; falling back to nearest log row"
            )
            # Prefer the latest log starting at or before added_at; otherwise earliest.
            before = [log for log in candidates if log.start_date <= added_at]
            if before:
                return max(before, key=lambda log: log.start_date).container_id
            return min(candidates, key=lambda log: log.start_date).container_id

        ferm_ingredients = fetch_all(
            src, "SELECT * FROM fermentation_ingredients ORDER BY id"
        )
        ferm_ing_skipped = 0
        for r in ferm_ingredients:
            added_at = to_dt(r["added_at"])
            container_id = resolve_container(r["fermentation_id"], added_at)
            if container_id is None:
                warnings.append(
                    f"SKIPPED fermentation_ingredient id={r['id']}: no logs "
                    f"for fermentation {r['fermentation_id']}"
                )
                ferm_ing_skipped += 1
                continue
            db.add(
                IngredientAddition(
                    id=r["id"],
                    container_id=container_id,
                    ingredient_id=r["ingredient_id"],
                    added_at=added_at,
                    amount=r["amount"],
                    unit=r["unit"],
                )
            )

        # bottle_ingredients (currently 0 rows but handle defensively).
        max_fi_id = max((r["id"] for r in ferm_ingredients), default=0)
        bottle_ingredients = fetch_all(
            src, "SELECT * FROM bottle_ingredients ORDER BY id"
        )
        for r in bottle_ingredients:
            db.add(
                IngredientAddition(
                    id=max_fi_id + r["id"],
                    container_id=r["bottle_id"] + BOTTLE_ID_OFFSET,
                    ingredient_id=r["ingredient_id"],
                    added_at=to_dt(r["added_at"]),
                    amount=r["amount"],
                    unit=r["unit"],
                )
            )

        db.flush()
        addition_count = db.query(IngredientAddition).count()
        print(f"  ingredient_additions: {addition_count} (skipped {ferm_ing_skipped})")

        # ---------- 5. Reviews ----------
        print()
        print("== Building reviews ==")
        old_reviews = fetch_all(src, "SELECT * FROM reviews ORDER BY id")
        for r in old_reviews:
            db.add(
                Review(
                    id=r["id"],
                    container_id=r["bottle_id"] + BOTTLE_ID_OFFSET,
                    name=r["name"],
                    fermentation_id=r["fermentation_id"],
                    overall_rating=r["overall_rating"],
                    boldness=r["boldness"],
                    tannicity=r["tannicity"],
                    sweetness=r["sweetness"],
                    acidity=r["acidity"],
                    complexity=r["complexity"],
                    review_date=to_date(r["review_date"]),
                )
            )
        db.flush()
        review_count = db.query(Review).count()
        print(f"  reviews: {review_count}")

        db.commit()

        # ---------- 6. Assertions ----------
        print()
        print("== Verification ==")
        expected_containers = len(vessels) + len(bottles)
        expected_logs = len(vessel_logs_raw) + len(bottle_logs_raw)
        expected_additions = (
            len(ferm_ingredients) + len(bottle_ingredients) - ferm_ing_skipped
        )
        expected_reviews = len(old_reviews)

        assert container_count == expected_containers, (
            f"containers: expected {expected_containers}, got {container_count}"
        )
        assert log_count == expected_logs, (
            f"logs: expected {expected_logs}, got {log_count}"
        )
        assert addition_count == expected_additions, (
            f"ingredient_additions: expected {expected_additions}, got {addition_count}"
        )
        assert review_count == expected_reviews, (
            f"reviews: expected {expected_reviews}, got {review_count}"
        )

        # FK integrity
        container_ids = {c.id for c in db.query(Container).all()}
        for r in db.query(Review).all():
            assert r.container_id in container_ids, (
                f"review {r.id} → bad container_id {r.container_id}"
            )
        for a in db.query(IngredientAddition).all():
            assert a.container_id in container_ids, (
                f"addition {a.id} → bad container_id {a.container_id}"
            )

        print(
            f"  containers:                  {container_count} == {expected_containers} OK"
        )
        print(f"  container_fermentation_logs: {log_count} == {expected_logs} OK")
        print(
            f"  ingredient_additions:        {addition_count} == {expected_additions} OK"
        )
        print(f"  reviews:                     {review_count} == {expected_reviews} OK")
        print("  FK integrity:                OK")

        print()
        if warnings:
            print(f"== {len(warnings)} warning(s) ==")
            for w in warnings:
                print(f"  - {w}")
        else:
            print("== no warnings ==")

        print()
        print("Migration complete.")
        print(f"Inspect: sqlite3 {TARGET_DB}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        src.close()


if __name__ == "__main__":
    main()
