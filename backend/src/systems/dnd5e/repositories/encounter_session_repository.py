from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.campaigns.lib.campaign import Campaign


class EncounterSessionRepositoryProtocol(Protocol):
    """Write repository for campaign context session selection state."""

    async def persist_context_selection(
        self,
        campaign: Campaign,
        scene_id: str,
        encounter_id: str,
    ) -> Campaign:
        ...


class EncounterSessionRepository(EncounterSessionRepositoryProtocol):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def persist_context_selection(
        self,
        campaign: Campaign,
        scene_id: str,
        encounter_id: str,
    ) -> Campaign:
        campaign.current_scene = scene_id
        campaign.active_encounter_id = encounter_id
        campaign.context_version = int(campaign.context_version or 0) + 1

        await self._db.commit()
        await self._db.refresh(campaign)
        return campaign
