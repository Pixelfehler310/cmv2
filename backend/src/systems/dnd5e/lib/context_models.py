from __future__ import annotations

from sqlalchemy import JSON, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.common.mixins import TimestampMixin, UUIDMixin
from src.database import Base


class SceneCatalogRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_scene_catalog"

    campaign_id: Mapped[str] = mapped_column(String, index=True)
    scene_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("campaign_id", "scene_id",
                         name="uq_dnd5e_scene_catalog_campaign_scene"),
    )


class EncounterCatalogRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dnd5e_encounter_catalog"

    campaign_id: Mapped[str] = mapped_column(String, index=True)
    scene_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    encounter_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, default="fixture")
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "scene_id",
            "encounter_id",
            name="uq_dnd5e_encounter_catalog_campaign_scene_encounter",
        ),
    )


Index(
    "ix_dnd5e_encounter_catalog_campaign_scene",
    EncounterCatalogRecord.campaign_id,
    EncounterCatalogRecord.scene_id,
)
