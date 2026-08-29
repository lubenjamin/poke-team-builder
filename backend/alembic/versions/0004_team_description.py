"""add teams.description

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("description", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("teams", "description")
