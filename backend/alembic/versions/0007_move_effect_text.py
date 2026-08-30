"""add move.effect_text

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("move", sa.Column("effect_text", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("move", "effect_text")
