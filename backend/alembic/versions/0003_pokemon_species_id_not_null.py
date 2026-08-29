"""tighten pokemon.species_id to NOT NULL after backfill

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-29

Run only after jobs/batch_load_pokemon.py has backfilled species_id on every
existing pokemon row (migration 0002 added it nullable for exactly this reason).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("pokemon", "species_id", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    op.alter_column("pokemon", "species_id", existing_type=sa.Integer(), nullable=True)
