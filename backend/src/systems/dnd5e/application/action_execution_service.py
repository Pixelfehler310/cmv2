from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.core.sessions.models import SessionContext
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.services.combat_service import CombatService


class ActionExecutionRequest(BaseModel):
    actor_id: str
    action_type: str
    action_name: str
    target_ids: list[str] = Field(default_factory=list)
    action_payload: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    require_canonical_action_id: bool = True


class ActionExecutionResult(BaseModel):
    events: list[dict[str, Any]] = Field(default_factory=list)


class ActionExecutionApplicationService:
    """Application-layer orchestration for action execution command flow."""

    def __init__(self, combat_service: CombatService):
        self._combat_service = combat_service

    async def execute(
        self,
        request: ActionExecutionRequest,
        encounter: EncounterState,
        encounter_session,
        ctx: SessionContext,
    ) -> ActionExecutionResult:
        events = await self._combat_service.execute_action(
            encounter=encounter,
            encounter_session=encounter_session,
            actor_id=request.actor_id,
            action_type=self._combat_service.normalize_action_type(request.action_type),
            action_name=request.action_name,
            target_ids=request.target_ids,
            action_payload=request.action_payload,
            request_id=request.request_id,
            ctx=ctx,
            raw_payload=request.raw_payload,
            require_canonical_action_id=request.require_canonical_action_id,
        )
        return ActionExecutionResult(events=events)
