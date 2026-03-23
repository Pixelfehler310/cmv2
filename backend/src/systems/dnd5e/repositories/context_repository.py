from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.campaigns.lib.campaign import Campaign
from src.systems.dnd5e.lib.context_models import EncounterCatalogRecord, SceneCatalogRecord


class ContextReadRepositoryProtocol(Protocol):
    """Read-only context repository.

    Scene is the canonical domain entity. Encounter APIs are retained as
    compatibility projections for existing transport/service surfaces.
    """

    async def get_campaign_with_characters(self, campaign_id: str) -> Campaign | None:
        ...

    async def list_scenes(self, campaign_id: str) -> list[SceneCatalogRecord]:
        ...

    async def list_campaign_encounters(self, campaign_id: str) -> list[EncounterCatalogRecord]:
        ...

    async def list_scene_encounters(self, campaign_id: str, scene_id: str) -> list[EncounterCatalogRecord]:
        ...

    async def get_scene_encounter(
        self,
        campaign_id: str,
        scene_id: str,
        encounter_id: str,
    ) -> EncounterCatalogRecord | None:
        ...

    async def encounter_exists(self, campaign_id: str, scene_id: str, encounter_id: str) -> bool:
        ...


class ContextReadRepository(ContextReadRepositoryProtocol):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_campaign_with_characters(self, campaign_id: str) -> Campaign | None:
        result = await self._db.execute(
            select(Campaign)
            .options(selectinload(Campaign.characters))
            .where(Campaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def list_scenes(self, campaign_id: str) -> list[SceneCatalogRecord]:
        result = await self._db.execute(
            select(SceneCatalogRecord)
            .where(SceneCatalogRecord.campaign_id == campaign_id)
            .order_by(SceneCatalogRecord.name.asc())
        )
        return list(result.scalars().all())

    async def list_campaign_encounters(self, campaign_id: str) -> list[EncounterCatalogRecord]:
        result = await self._db.execute(
            select(EncounterCatalogRecord)
            .where(EncounterCatalogRecord.campaign_id == campaign_id)
            .order_by(EncounterCatalogRecord.encounter_id.asc())
        )
        return list(result.scalars().all())

    async def list_scene_encounters(self, campaign_id: str, scene_id: str) -> list[EncounterCatalogRecord]:
        result = await self._db.execute(
            select(EncounterCatalogRecord)
            .where(
                EncounterCatalogRecord.campaign_id == campaign_id,
                EncounterCatalogRecord.scene_id == scene_id,
            )
            .order_by(EncounterCatalogRecord.name.asc())
        )
        return list(result.scalars().all())

    async def get_scene_encounter(
        self,
        campaign_id: str,
        scene_id: str,
        encounter_id: str,
    ) -> EncounterCatalogRecord | None:
        result = await self._db.execute(
            select(EncounterCatalogRecord).where(
                EncounterCatalogRecord.campaign_id == campaign_id,
                EncounterCatalogRecord.scene_id == scene_id,
                EncounterCatalogRecord.encounter_id == encounter_id,
            )
        )
        return result.scalar_one_or_none()

    async def encounter_exists(self, campaign_id: str, scene_id: str, encounter_id: str) -> bool:
        return (await self.get_scene_encounter(campaign_id, scene_id, encounter_id)) is not None
