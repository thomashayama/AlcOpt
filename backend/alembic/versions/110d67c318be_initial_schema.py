"""initial schema

Revision ID: 110d67c318be
Revises:
Create Date: 2026-04-12 21:45:05.908001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '110d67c318be'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NOW = datetime(2026, 4, 12).isoformat()

_TABLES_NEEDING_TIMESTAMPS = [
    "containers",
    "ingredients",
    "fermentations",
    "container_fermentation_logs",
    "ingredient_additions",
    "specific_gravity_measurements",
    "mass_measurements",
    "reviews",
]


def upgrade() -> None:
    # New table
    op.create_table(
        "oauth_states",
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("state"),
    )

    # Add created_at/updated_at with a server_default so existing rows get a value
    for table in _TABLES_NEEDING_TIMESTAMPS:
        with op.batch_alter_table(table) as batch:
            batch.add_column(
                sa.Column("created_at", sa.DateTime(), nullable=False, server_default=_NOW)
            )
            batch.add_column(
                sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=_NOW)
            )

    # Fermentation date columns: DATE -> DateTime (SQLite stores both as text)
    with op.batch_alter_table("fermentations") as batch:
        batch.alter_column(
            "start_date",
            existing_type=sa.DATE(),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
        batch.alter_column(
            "end_date",
            existing_type=sa.DATE(),
            type_=sa.DateTime(),
            existing_nullable=True,
        )


def downgrade() -> None:
    for table in reversed(_TABLES_NEEDING_TIMESTAMPS):
        with op.batch_alter_table(table) as batch:
            batch.drop_column("updated_at")
            batch.drop_column("created_at")

    with op.batch_alter_table("fermentations") as batch:
        batch.alter_column(
            "start_date",
            existing_type=sa.DateTime(),
            type_=sa.DATE(),
            existing_nullable=False,
        )
        batch.alter_column(
            "end_date",
            existing_type=sa.DateTime(),
            type_=sa.DATE(),
            existing_nullable=True,
        )

    op.drop_table("oauth_states")
