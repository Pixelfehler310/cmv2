from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

JSON_PAYLOAD_TYPE = JSON().with_variant(JSONB, "postgresql")


class CharacterSheetProjectionModel(Base):
    __tablename__ = "dnd5e_character_sheet_projections"

    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    catalog_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sheet_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolution_status: Mapped[str] = mapped_column(String, nullable=False, default="invalidated")
    denial_reason_code: Mapped[str | None] = mapped_column(String, nullable=True)
    unresolved_reference_ids: Mapped[list[str]] = mapped_column(
        JSON_PAYLOAD_TYPE,
        nullable=False,
        default=list,
    )
    computed_fields: Mapped[dict] = mapped_column(
        JSON_PAYLOAD_TYPE,
        nullable=False,
        default=dict,
    )
    last_resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "resolution_status IN ('resolved','denied','invalidated')",
            name="ck_dnd5e_character_sheet_projections_resolution_status",
        ),
        CheckConstraint(
            "sheet_revision >= 0",
            name="ck_dnd5e_character_sheet_projections_sheet_revision",
        ),
        CheckConstraint(
            "catalog_revision >= 0",
            name="ck_dnd5e_character_sheet_projections_catalog_revision",
        ),
    )
