"""add character sheet projection cache table

Revision ID: 20260408_01
Revises: 20260407_01
Create Date: 2026-04-08 00:00:00

"""

from typing import Sequence, Union

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260408_01"
down_revision: Union[str, Sequence[str], None] = "20260407_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dnd5e_character_sheet_projections",
        sa.Column("character_id", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("catalog_revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sheet_revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolution_status", sa.String(), nullable=False, server_default="invalidated"),
        sa.Column("denial_reason_code", sa.String(), nullable=True),
        sa.Column("unresolved_reference_ids", sa.JSON(), nullable=False),
        sa.Column("computed_fields", sa.JSON(), nullable=False),
        sa.Column("last_resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "resolution_status IN ('resolved','denied','invalidated')",
            name="ck_dnd5e_character_sheet_projections_resolution_status",
        ),
        sa.CheckConstraint(
            "catalog_revision >= 0",
            name="ck_dnd5e_character_sheet_projections_catalog_revision",
        ),
        sa.CheckConstraint(
            "sheet_revision >= 0",
            name="ck_dnd5e_character_sheet_projections_sheet_revision",
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            ondelete="CASCADE",
            name="fk_dnd5e_character_sheet_projections_character",
        ),
        sa.PrimaryKeyConstraint("character_id"),
    )
    op.create_index(
        "ix_dnd5e_character_sheet_projections_campaign_id",
        "dnd5e_character_sheet_projections",
        ["campaign_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dnd5e_character_sheet_projections_campaign_id",
        table_name="dnd5e_character_sheet_projections",
    )
    op.drop_table("dnd5e_character_sheet_projections")
