"""add type_effectiveness

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "type_effectiveness",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attacking_type", sa.String(), nullable=False),
        sa.Column("defending_type", sa.String(), nullable=False),
        sa.Column("multiplier", sa.Float(), nullable=False),
        sa.UniqueConstraint(
            "attacking_type", "defending_type", name="uq_type_effectiveness_pair"
        ),
    )
    op.create_index(
        "ix_type_effectiveness_attacking_type", "type_effectiveness", ["attacking_type"]
    )
    op.create_index(
        "ix_type_effectiveness_defending_type", "type_effectiveness", ["defending_type"]
    )


def downgrade() -> None:
    op.drop_index("ix_type_effectiveness_defending_type", table_name="type_effectiveness")
    op.drop_index("ix_type_effectiveness_attacking_type", table_name="type_effectiveness")
    op.drop_table("type_effectiveness")
