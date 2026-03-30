"""
Migrate data from local SQLite (data/alcopt.db) to a PostgreSQL server.

Usage:
    python scripts/sqlite_to_postgres.py <POSTGRES_URL>

The postgres URL should be in the format:
    postgresql://user:password@host:port/dbname

You can copy this from the Railway dashboard (DATABASE_URL).
If the URL starts with postgres://, it will be converted to postgresql://.
"""

import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path so we can import models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alcopt.database.models import (
    Base,
    Vessel,
    Ingredient,
    Fermentation,
    FermentationVesselLog,
    FermentationIngredient,
    SpecificGravityMeasurement,
    MassMeasurement,
    Bottle,
    BottleIngredient,
    BottleLog,
    Review,
)

# Order matters: parents before children (foreign key dependencies)
TABLES_IN_ORDER = [
    Ingredient,
    Fermentation,
    Vessel,
    FermentationVesselLog,
    FermentationIngredient,
    SpecificGravityMeasurement,
    MassMeasurement,
    Bottle,
    BottleIngredient,
    BottleLog,
    Review,
]

SQLITE_PATH = Path(__file__).resolve().parent.parent / "alcopt.db"


def migrate(postgres_url: str):
    # Normalize postgres:// to postgresql://
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

    sqlite_engine = create_engine(
        f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False}
    )
    pg_engine = create_engine(postgres_url)

    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=pg_engine)

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
    if len(sys.argv) != 2:
        print("Usage: python scripts/sqlite_to_postgres.py <POSTGRES_URL>")
        sys.exit(1)

    postgres_url = sys.argv[1]
    print(f"Source: {SQLITE_PATH}")
    print(
        f"Target: {postgres_url.split('@')[0].split('://')[0]}://***@{postgres_url.split('@')[-1]}"
    )
    print()

    confirm = input("This will INSERT data into the target database. Continue? [y/N] ")
    if confirm.lower() != "y":
        print("Aborted.")
        sys.exit(0)

    print()
    migrate(postgres_url)
