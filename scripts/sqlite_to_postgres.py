"""
Migrate data from local SQLite (data/alcopt.db) to a PostgreSQL server.

Usage:
    python scripts/sqlite_to_postgres.py <POSTGRES_URL> [--wipe]

The postgres URL should be in the format:
    postgresql://user:password@host:port/dbname

You can copy this from the Railway dashboard (DATABASE_URL).
If the URL starts with postgres://, it will be converted to postgresql://.

Pass --wipe to DROP SCHEMA public CASCADE on the target before migrating.
Required when the target has a stale schema (e.g. pre-containers-refactor
tables) or existing rows that would conflict on primary key.
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path so we can import models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alcopt.database.models import (
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

# Order matters: parents before children (foreign key dependencies)
TABLES_IN_ORDER = [
    Ingredient,
    Fermentation,
    Container,
    ContainerFermentationLog,
    IngredientAddition,
    SpecificGravityMeasurement,
    MassMeasurement,
    Review,
]

SQLITE_PATH = Path(__file__).resolve().parent.parent / "data" / "alcopt.db"


def migrate(postgres_url: str, wipe: bool = False):
    # Normalize postgres:// to postgresql://
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

    sqlite_engine = create_engine(
        f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False}
    )
    pg_engine = create_engine(postgres_url)

    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=pg_engine)

    if wipe:
        print("Wiping target: DROP SCHEMA public CASCADE")
        with pg_engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))

    # Create all tables on postgres
    Base.metadata.create_all(bind=pg_engine)

    sqlite_db = SqliteSession()
    pg_db = PgSession()

    try:
        for model in TABLES_IN_ORDER:
            table_name = model.__tablename__
            rows = sqlite_db.query(model).all()

            if not rows:
                print(f"  {table_name}: 0 rows (skipped)")
                continue

            # Get column names from the model (exclude relationships)
            columns = [c.key for c in model.__table__.columns]

            # Insert rows
            for row in rows:
                data = {col: getattr(row, col) for col in columns}
                pg_db.execute(model.__table__.insert().values(**data))

            pg_db.commit()
            print(f"  {table_name}: {len(rows)} rows migrated")

            # Reset the auto-increment sequence to max id
            max_id = max(row.id for row in rows)
            seq_name = f"{table_name}_id_seq"
            pg_db.execute(text(f"SELECT setval('{seq_name}', :val)"), {"val": max_id})
            pg_db.commit()

        print("\nMigration complete!")

    except Exception as e:
        pg_db.rollback()
        print(f"\nMigration failed: {e}")
        raise
    finally:
        sqlite_db.close()
        pg_db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate data/alcopt.db into a Postgres server."
    )
    parser.add_argument("postgres_url", help="Target Postgres URL")
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="DROP SCHEMA public CASCADE on the target before migrating. "
        "Required when the target has a stale schema or conflicting rows.",
    )
    args = parser.parse_args()

    postgres_url = args.postgres_url
    redacted = (
        f"{postgres_url.split('://', 1)[0]}://***@{postgres_url.split('@', 1)[-1]}"
    )
    print(f"Source: {SQLITE_PATH}")
    print(f"Target: {redacted}")
    print(f"Wipe:   {args.wipe}")
    print()

    if args.wipe:
        prompt = (
            "This will DROP ALL TABLES on the target and replace them "
            "with data from the local SQLite DB. Continue? [y/N] "
        )
    else:
        prompt = "This will INSERT data into the target database. Continue? [y/N] "

    confirm = input(prompt)
    if confirm.lower() != "y":
        print("Aborted.")
        sys.exit(0)

    print()
    migrate(postgres_url, wipe=args.wipe)
