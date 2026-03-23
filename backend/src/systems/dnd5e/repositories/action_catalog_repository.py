from __future__ import annotations

from typing import Protocol

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.systems.dnd5e.lib.content_models import (
    AbilityBindingRecord,
    ActionDefinitionRecord,
    EffectDefinitionRecord,
)


class ActionCatalogRepositoryProtocol(Protocol):
    async def list_bindings_for_actor(
        self,
        actor_id: str,
        template_candidates: list[str],
    ) -> list[AbilityBindingRecord]:
        ...

    async def list_action_definitions_by_ids(
        self,
        action_ids: list[str],
    ) -> list[ActionDefinitionRecord]:
        ...

    async def get_effect_definition(self, effect_id: str) -> EffectDefinitionRecord | None:
        ...


class ActionCatalogRepository(ActionCatalogRepositoryProtocol):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def list_bindings_for_actor(
        self,
        actor_id: str,
        template_candidates: list[str],
    ) -> list[AbilityBindingRecord]:
        binding_filters = [AbilityBindingRecord.actor_id == actor_id]
        if template_candidates:
            binding_filters.append(
                AbilityBindingRecord.actor_template_id.in_(template_candidates)
            )

        stmt = select(AbilityBindingRecord).where(
            AbilityBindingRecord.system == "dnd5e",
            or_(*binding_filters),
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_action_definitions_by_ids(
        self,
        action_ids: list[str],
    ) -> list[ActionDefinitionRecord]:
        if not action_ids:
            return []

        stmt = select(ActionDefinitionRecord).where(
            ActionDefinitionRecord.system == "dnd5e",
            ActionDefinitionRecord.enabled.is_(True),
            ActionDefinitionRecord.action_id.in_(action_ids),
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_effect_definition(self, effect_id: str) -> EffectDefinitionRecord | None:
        stmt = select(EffectDefinitionRecord).where(
            EffectDefinitionRecord.system == "dnd5e",
            EffectDefinitionRecord.effect_id == effect_id,
            EffectDefinitionRecord.enabled.is_(True),
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
