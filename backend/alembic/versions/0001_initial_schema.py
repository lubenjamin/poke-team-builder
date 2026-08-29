"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pokemon",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sprite_url", sa.String(), nullable=False),
        sa.Column("types", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("hp", sa.Integer(), nullable=False),
        sa.Column("attack", sa.Integer(), nullable=False),
        sa.Column("defense", sa.Integer(), nullable=False),
        sa.Column("special_attack", sa.Integer(), nullable=False),
        sa.Column("special_defense", sa.Integer(), nullable=False),
        sa.Column("speed", sa.Integer(), nullable=False),
        sa.Column(
            "last_fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_teams_client_id", "teams", ["client_id"])

    op.create_table(
        "team_pokemon",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pokemon_id", sa.Integer(), sa.ForeignKey("pokemon.id"), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.UniqueConstraint("team_id", "slot", name="uq_team_pokemon_team_slot"),
    )

    op.create_table(
        "pokemon_change_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pokemon_id", sa.Integer(), sa.ForeignKey("pokemon.id"), nullable=False),
        sa.Column("field_name", sa.String(), nullable=False),
        sa.Column("old_value", sa.String(), nullable=False),
        sa.Column("new_value", sa.String(), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pokemon_id", sa.Integer(), sa.ForeignKey("pokemon.id"), nullable=False),
        sa.Column(
            "change_log_id",
            sa.Integer(),
            sa.ForeignKey("pokemon_change_log.id"),
            nullable=False,
        ),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("dismissed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_alerts_client_id", "alerts", ["client_id"])

    op.create_table(
        "ingestion_errors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("ingestion_errors")
    op.drop_index("ix_alerts_client_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("pokemon_change_log")
    op.drop_table("team_pokemon")
    op.drop_index("ix_teams_client_id", table_name="teams")
    op.drop_table("teams")
    op.drop_table("pokemon")
