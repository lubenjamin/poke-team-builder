"""add move_change_log, alert move fields

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "move_change_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("move_id", sa.Integer(), sa.ForeignKey("move.id"), nullable=False),
        sa.Column("field_name", sa.String(), nullable=False),
        sa.Column("old_value", sa.String(), nullable=False),
        sa.Column("new_value", sa.String(), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.alter_column("alerts", "change_log_id", new_column_name="pokemon_change_log_id")
    op.alter_column("alerts", "pokemon_change_log_id", nullable=True)
    op.add_column("alerts", sa.Column("move_id", sa.Integer(), sa.ForeignKey("move.id"), nullable=True))
    op.add_column(
        "alerts",
        sa.Column(
            "move_change_log_id",
            sa.Integer(),
            sa.ForeignKey("move_change_log.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("alerts", "move_change_log_id")
    op.drop_column("alerts", "move_id")
    op.alter_column("alerts", "pokemon_change_log_id", nullable=False)
    op.alter_column("alerts", "pokemon_change_log_id", new_column_name="change_log_id")
    op.drop_table("move_change_log")
