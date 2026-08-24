"""create vehicles table

Revision ID: 0001_create_vehicles
Revises:
Create Date: 2026-08-20 17:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_vehicles"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("make", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("city", sa.String(length=64), nullable=False),
        sa.Column("condition", sa.Text(), nullable=False),
        sa.Column("transmission", sa.Text(), nullable=False),
        sa.Column("body_type", sa.Text(), nullable=False),
        sa.Column("fuel_type", sa.Text(), nullable=False),
        sa.Column("engine_capacity", sa.Integer(), nullable=True),
        sa.Column("mileage_km", sa.Integer(), nullable=False),
        sa.Column("fuel_average_kmpl", sa.Float(), nullable=True),
        sa.Column("resale_rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicles_make", "vehicles", ["make"], unique=False)
    op.create_index("ix_vehicles_model", "vehicles", ["model"], unique=False)
    op.create_index("ix_vehicles_year", "vehicles", ["year"], unique=False)
    op.create_index("ix_vehicles_price", "vehicles", ["price"], unique=False)
    op.create_index("ix_vehicles_city", "vehicles", ["city"], unique=False)
    op.create_index("ix_vehicles_condition", "vehicles", ["condition"], unique=False)
    op.create_index("ix_vehicles_transmission", "vehicles", ["transmission"], unique=False)
    op.create_index("ix_vehicles_body_type", "vehicles", ["body_type"], unique=False)
    op.create_index("ix_vehicles_fuel_type", "vehicles", ["fuel_type"], unique=False)
    op.create_index("ix_vehicles_make_model", "vehicles", ["make", "model"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vehicles_make_model", table_name="vehicles")
    op.drop_index("ix_vehicles_fuel_type", table_name="vehicles")
    op.drop_index("ix_vehicles_body_type", table_name="vehicles")
    op.drop_index("ix_vehicles_transmission", table_name="vehicles")
    op.drop_index("ix_vehicles_condition", table_name="vehicles")
    op.drop_index("ix_vehicles_city", table_name="vehicles")
    op.drop_index("ix_vehicles_price", table_name="vehicles")
    op.drop_index("ix_vehicles_year", table_name="vehicles")
    op.drop_index("ix_vehicles_model", table_name="vehicles")
    op.drop_index("ix_vehicles_make", table_name="vehicles")
    op.drop_table("vehicles")
