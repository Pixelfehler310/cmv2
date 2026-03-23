from sqlalchemy.ext.asyncio import AsyncSession

from src.systems.dnd5e.services.combat_service import CombatService


class CampaignContextApplicationService:
    """Application-layer facade for campaign context use-cases.

    This is an extraction seam so transport handlers can depend on a stable
    use-case API while combat internals are migrated to domain/repository layers.
    """

    def __init__(self, db: AsyncSession):
        self._combat_service = CombatService(db)

    async def get_context(self, campaign_id: str):
        return await self._combat_service.get_context(campaign_id)

    async def list_scenes(self, campaign_id: str):
        return await self._combat_service.list_scenes(campaign_id)

    async def list_encounters(self, campaign_id: str, scene_id: str):
        return await self._combat_service.list_encounters(campaign_id, scene_id)

    async def select_context(self, campaign_id: str, scene_id: str, encounter_id: str):
        return await self._combat_service.select_context(campaign_id, scene_id, encounter_id)
