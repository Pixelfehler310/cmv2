"""v05 compendium foundation

Revision ID: 20260328_01
Revises:
Create Date: 2026-03-28 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260328_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dnd5e_content_packs",
        sa.Column("author_user_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("lifecycle_state", sa.String(), nullable=False),
        sa.Column("is_homebrew", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pack_key", sa.String(), nullable=True),
        sa.Column("compatibility_target", sa.String(), nullable=True),
        sa.Column("published_version", sa.Integer(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pack_key", name="uq_dnd5e_content_packs_pack_key"),
    )
    op.create_index(
        "ix_dnd5e_content_packs_lifecycle_homebrew",
        "dnd5e_content_packs",
        ["lifecycle_state", "is_homebrew"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_content_packs_lifecycle_state",
        "dnd5e_content_packs",
        ["lifecycle_state"],
        unique=False,
    )

    op.create_table(
        "dnd5e_compendium_definitions",
        sa.Column("family", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("lifecycle_state", sa.String(), nullable=False),
        sa.Column("content_version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("pack_id", sa.String(), nullable=False),
        sa.Column("provenance_source", sa.String(), nullable=False),
        sa.Column("provenance_author", sa.String(), nullable=True),
        sa.Column("provenance_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("content_version >= 1", name="ck_dnd5e_compendium_definitions_content_version"),
        sa.ForeignKeyConstraint(["pack_id"], ["dnd5e_content_packs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "pack_id",
            "family",
            "slug",
            "content_version",
            name="uq_dnd5e_compendium_definitions_pack_family_slug_version",
        ),
    )
    op.create_index(
        "ix_dnd5e_compendium_definitions_family",
        "dnd5e_compendium_definitions",
        ["family"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_compendium_definitions_slug",
        "dnd5e_compendium_definitions",
        ["slug"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_compendium_definitions_lifecycle_state",
        "dnd5e_compendium_definitions",
        ["lifecycle_state"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_compendium_definitions_pack_id",
        "dnd5e_compendium_definitions",
        ["pack_id"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_compendium_definitions_pack_family_state",
        "dnd5e_compendium_definitions",
        ["pack_id", "family", "lifecycle_state"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_compendium_definitions_payload_gin",
        "dnd5e_compendium_definitions",
        ["payload"],
        unique=False,
        postgresql_using="gin",
    )

    op.create_table(
        "dnd5e_linked_entries",
        sa.Column("source_definition_id", sa.String(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=False),
        sa.Column("target_definition_id", sa.String(), nullable=False),
        sa.Column("target_family", sa.String(), nullable=False),
        sa.Column("relation_kind", sa.String(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("resolve_mode", sa.String(), nullable=False, server_default=sa.text("'strict'")),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["source_definition_id"], ["dnd5e_compendium_definitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_definition_id"], ["dnd5e_compendium_definitions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_definition_id",
            "source_path",
            "target_definition_id",
            "relation_kind",
            name="uq_dnd5e_linked_entries_source_target_relation",
        ),
    )
    op.create_index(
        "ix_dnd5e_linked_entries_source_definition_id",
        "dnd5e_linked_entries",
        ["source_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_linked_entries_target_definition_id",
        "dnd5e_linked_entries",
        ["target_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_linked_entries_source_relation",
        "dnd5e_linked_entries",
        ["source_definition_id", "relation_kind"],
        unique=False,
    )
    op.create_index(
        "ix_dnd5e_linked_entries_target",
        "dnd5e_linked_entries",
        ["target_definition_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_dnd5e_linked_entries_target", table_name="dnd5e_linked_entries")
    op.drop_index("ix_dnd5e_linked_entries_source_relation", table_name="dnd5e_linked_entries")
    op.drop_index("ix_dnd5e_linked_entries_target_definition_id", table_name="dnd5e_linked_entries")
    op.drop_index("ix_dnd5e_linked_entries_source_definition_id", table_name="dnd5e_linked_entries")
    op.drop_table("dnd5e_linked_entries")

    op.drop_index("ix_dnd5e_compendium_definitions_payload_gin", table_name="dnd5e_compendium_definitions")
    op.drop_index("ix_dnd5e_compendium_definitions_pack_family_state", table_name="dnd5e_compendium_definitions")
    op.drop_index("ix_dnd5e_compendium_definitions_pack_id", table_name="dnd5e_compendium_definitions")
    op.drop_index("ix_dnd5e_compendium_definitions_lifecycle_state", table_name="dnd5e_compendium_definitions")
    op.drop_index("ix_dnd5e_compendium_definitions_slug", table_name="dnd5e_compendium_definitions")
    op.drop_index("ix_dnd5e_compendium_definitions_family", table_name="dnd5e_compendium_definitions")
    op.drop_table("dnd5e_compendium_definitions")

    op.drop_index("ix_dnd5e_content_packs_lifecycle_state", table_name="dnd5e_content_packs")
    op.drop_index("ix_dnd5e_content_packs_lifecycle_homebrew", table_name="dnd5e_content_packs")
    op.drop_table("dnd5e_content_packs")
