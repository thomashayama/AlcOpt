from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from alcopt.database.models import Base, ContainerFermentationLog, MassMeasurement
from alcopt.config import DATABASE_URL

DATABASE_URI = DATABASE_URL

connect_args = {}
if DATABASE_URI.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URI, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()
    _ensure_open_log_unique_index()


def _ensure_open_log_unique_index():
    """Ensure the partial unique index on open container logs exists.

    create_all() won't add an index to a table that already exists on older
    databases, so we issue the DDL directly. The syntax is identical between
    SQLite 3.8+ and Postgres.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "container_fermentation_logs" not in inspector.get_table_names():
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "ix_container_fermentation_logs_one_open_per_container "
                "ON container_fermentation_logs (container_id) "
                "WHERE end_date IS NULL"
            )
        )


def _add_missing_columns():
    """Add columns that exist in models but not in the database.

    create_all() only creates new tables — it won't ALTER existing ones.
    This handles the gap so that adding columns to models doesn't require
    a manual migration on every deployment target.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    tables_with_timestamps = [
        "containers",
        "ingredients",
        "fermentations",
        "container_fermentation_logs",
        "ingredient_additions",
        "specific_gravity_measurements",
        "mass_measurements",
        "reviews",
    ]
    for table_name in tables_with_timestamps:
        if table_name not in inspector.get_table_names():
            continue
        existing = {c["name"] for c in inspector.get_columns(table_name)}
        with engine.begin() as conn:
            if "created_at" not in existing:
                conn.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        "ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )
                )
            if "updated_at" not in existing:
                conn.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        "ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )
                )


def close_open_log(
    db: Session, container_id: int, at: datetime
) -> Optional[ContainerFermentationLog]:
    """Close any currently-open fermentation log for `container_id` at time `at`.

    Returns the row that was closed, or None if there was no open log. Caller is
    responsible for committing.
    """
    open_log = (
        db.query(ContainerFermentationLog)
        .filter(
            ContainerFermentationLog.container_id == container_id,
            ContainerFermentationLog.end_date.is_(None),
        )
        .order_by(ContainerFermentationLog.start_date.desc())
        .first()
    )
    if open_log is not None:
        open_log.end_date = at
    return open_log


def current_fermentation_log(
    db: Session, container_id: int, at: Optional[datetime] = None
) -> Optional[ContainerFermentationLog]:
    """Return the fermentation log row for `container_id` active at `at`.

    If `at` is None, returns the currently-open log (end_date IS NULL). If
    multiple windows match, returns the one with the latest start_date.
    """
    q = db.query(ContainerFermentationLog).filter(
        ContainerFermentationLog.container_id == container_id
    )
    if at is None:
        q = q.filter(ContainerFermentationLog.end_date.is_(None))
    else:
        q = q.filter(ContainerFermentationLog.start_date <= at).filter(
            (ContainerFermentationLog.end_date.is_(None))
            | (ContainerFermentationLog.end_date >= at)
        )
    return q.order_by(ContainerFermentationLog.start_date.desc()).first()


def latest_fermentation_log(
    db: Session, container_id: int
) -> Optional[ContainerFermentationLog]:
    """Return the most recent log row for `container_id` regardless of state.

    Useful for resolving "what fermentation does this bottle hold" when the
    bottle's log was never explicitly closed.
    """
    return (
        db.query(ContainerFermentationLog)
        .filter(ContainerFermentationLog.container_id == container_id)
        .order_by(ContainerFermentationLog.start_date.desc())
        .first()
    )


def all_mass_measurement_info(db):
    return [
        {
            "ID": m.id,
            "Fermentation ID": m.fermentation_id,
            "Date": m.measurement_date,
            "Mass (g)": m.mass,
        }
        for m in db.query(MassMeasurement).all()
    ]
