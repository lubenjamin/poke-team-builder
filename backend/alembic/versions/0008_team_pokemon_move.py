"""add team_pokemon_move

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team_pokemon_move",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "team_pokemon_id",
            sa.Integer(),
            sa.ForeignKey("team_pokemon.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("move_id", sa.Integer(), sa.ForeignKey("move.id"), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.UniqueConstraint("team_pokemon_id", "slot", name="uq_team_pokemon_move_slot"),
    )
    op.create_index(
        "ix_team_pokemon_move_team_pokemon_id", "team_pokemon_move", ["team_pokemon_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_team_pokemon_move_team_pokemon_id", table_name="team_pokemon_move")
    op.drop_table("team_pokemon_move")
