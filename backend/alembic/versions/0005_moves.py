"""add move and pokemon_movepool

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "move",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("damage_class", sa.String(), nullable=False),
        sa.Column("power", sa.Integer(), nullable=True),
        sa.Column("accuracy", sa.Integer(), nullable=True),
        sa.Column("pp", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("effect_chance", sa.Integer(), nullable=True),
        sa.Column(
            "last_fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "pokemon_movepool",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pokemon_id",
            sa.Integer(),
            sa.ForeignKey("pokemon.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "move_id", sa.Integer(), sa.ForeignKey("move.id", ondelete="CASCADE"), nullable=False
        ),
        sa.UniqueConstraint("pokemon_id", "move_id", name="uq_pokemon_movepool_pokemon_move"),
    )
    op.create_index("ix_pokemon_movepool_pokemon_id", "pokemon_movepool", ["pokemon_id"])
    op.create_index("ix_pokemon_movepool_move_id", "pokemon_movepool", ["move_id"])


def downgrade() -> None:
    op.drop_index("ix_pokemon_movepool_move_id", table_name="pokemon_movepool")
    op.drop_index("ix_pokemon_movepool_pokemon_id", table_name="pokemon_movepool")
    op.drop_table("pokemon_movepool")
    op.drop_table("move")
