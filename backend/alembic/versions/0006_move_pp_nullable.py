"""relax move.pp to nullable

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-30

Z-Moves/Max Moves (PokeAPI move ids 10001+) have no pp of their own — they
inherit it from the move they're derived from, so PokeAPI returns null.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("move", "pp", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column("move", "pp", existing_type=sa.Integer(), nullable=False)
