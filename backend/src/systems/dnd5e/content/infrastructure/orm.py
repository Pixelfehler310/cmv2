from __future__ import annotations
__production_status__ = "gold"

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.common.mixins import TimestampMixin, UUIDMixin
from src.database import Base

JSON_PAYLOAD_TYPE = JSON().with_variant(JSONB, "postgresql")


class ContentPackModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_content_packs"

    author_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(
        String, nullable=False, default="draft", index=True)
    is_homebrew: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    pack_key: Mapped[str | None] = mapped_column(String, nullable=True)
    compatibility_target: Mapped[str | None] = mapped_column(
        String, nullable=True)
    published_version: Mapped[int | None] = mapped_column(
        Integer, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "lifecycle_state IN ('draft','published','archived')",
            name="ck_dnd5e_content_packs_lifecycle_state",
        ),
        UniqueConstraint("pack_key", name="uq_dnd5e_content_packs_pack_key"),
        Index("ix_dnd5e_content_packs_lifecycle_homebrew",
              "lifecycle_state", "is_homebrew"),
    )


class CompendiumDefinitionModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_compendium_definitions"

    family: Mapped[str] = mapped_column(String, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(
        String, nullable=False, default="draft", index=True)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    pack_id: Mapped[str] = mapped_column(
        ForeignKey("dnd5e_content_packs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provenance_source: Mapped[str] = mapped_column(String, nullable=False)
    provenance_author: Mapped[str | None] = mapped_column(
        String, nullable=True)
    provenance_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSON_PAYLOAD_TYPE, nullable=False, default=dict)

    __table_args__ = (
        CheckConstraint("content_version >= 1",
                        name="ck_dnd5e_compendium_definitions_content_version"),
        CheckConstraint(
            "lifecycle_state IN ('draft','published','archived','superseded')",
            name="ck_dnd5e_compendium_definitions_lifecycle_state",
        ),
        UniqueConstraint(
            "pack_id",
            "family",
            "slug",
            "content_version",
            name="uq_dnd5e_compendium_definitions_pack_family_slug_version",
        ),
        Index(
            "ix_dnd5e_compendium_definitions_pack_family_state",
            "pack_id",
            "family",
            "lifecycle_state",
        ),
        Index(
            "ix_dnd5e_compendium_definitions_payload_gin",
            "payload",
            postgresql_using="gin",
        ),
    )


class SearchIndexModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_search_index"

    definition_id: Mapped[str] = mapped_column(
        ForeignKey("dnd5e_compendium_definitions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    family: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pack_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    name_normalized: Mapped[str] = mapped_column(
        String, nullable=False, index=True)
    search_blob: Mapped[str] = mapped_column(String, nullable=False, default="")
    visibility_state: Mapped[str] = mapped_column(
        String, nullable=False, default="draft", index=True)

    __table_args__ = (
        Index(
            "ix_dnd5e_search_index_family_visibility",
            "family",
            "visibility_state",
        ),
    )


class LinkedEntryModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_linked_entries"

    source_definition_id: Mapped[str] = mapped_column(
        ForeignKey("dnd5e_compendium_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_path: Mapped[str] = mapped_column(
        String, nullable=False, default="$")
    target_definition_id: Mapped[str] = mapped_column(
        ForeignKey("dnd5e_compendium_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    target_family: Mapped[str] = mapped_column(String, nullable=False)
    relation_kind: Mapped[str] = mapped_column(String, nullable=False)
    required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True)
    resolve_mode: Mapped[str] = mapped_column(
        String, nullable=False, default="strict")

    __table_args__ = (
        UniqueConstraint(
            "source_definition_id",
            "source_path",
            "target_definition_id",
            "relation_kind",
            name="uq_dnd5e_linked_entries_source_target_relation",
        ),
        Index("ix_dnd5e_linked_entries_source_relation",
              "source_definition_id", "relation_kind"),
        Index("ix_dnd5e_linked_entries_target", "target_definition_id"),
    )
