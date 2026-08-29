"""add pokemon_species and pokemon.species_id / is_default

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-29

species_id starts nullable since `pokemon` already has live rows with no species
to point at yet; it's backfilled by re-running jobs/batch_load_pokemon.py, then
tightened to NOT NULL in migration 0003.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pokemon_species",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("national_dex_number", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_pokemon_species_national_dex_number", "pokemon_species", ["national_dex_number"]
    )

    op.add_column("pokemon", sa.Column("species_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_pokemon_species_id", "pokemon", "pokemon_species", ["species_id"], ["id"]
    )
    op.create_index("ix_pokemon_species_id", "pokemon", ["species_id"])

    op.add_column(
        "pokemon",
        sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("pokemon", "is_default")
    op.drop_index("ix_pokemon_species_id", table_name="pokemon")
    op.drop_constraint("fk_pokemon_species_id", "pokemon", type_="foreignkey")
    op.drop_column("pokemon", "species_id")
    op.drop_index("ix_pokemon_species_national_dex_number", table_name="pokemon_species")
    op.drop_table("pokemon_species")
