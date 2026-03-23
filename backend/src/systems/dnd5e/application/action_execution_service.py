from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.core.sessions.models import SessionContext
from src.systems.dnd5e.domain.action_resolution_pipeline import (
    ActionResolutionContext,
    ActionResolutionRequest,
)
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
        domain_request = self._build_domain_request(request)
        domain_context = self._build_domain_context(request, encounter)

        events = await self._combat_service.execute_action(
            encounter=encounter,
            encounter_session=encounter_session,
            actor_id=domain_request.actor_id,
            action_type=domain_request.action_type_cost,
            action_name=domain_request.action_id,
            target_ids=domain_request.target_ids,
            action_payload=domain_request.payload,
            request_id=domain_context.request_id,
            ctx=ctx,
            raw_payload=request.raw_payload,
            require_canonical_action_id=request.require_canonical_action_id,
        )
        return ActionExecutionResult(events=events)

    def _build_domain_request(self, request: ActionExecutionRequest) -> ActionResolutionRequest:
        return ActionResolutionRequest(
            actor_id=request.actor_id,
            action_id=request.action_name,
            action_type_cost=self._combat_service.normalize_action_type(
                request.action_type),
            family="utility",
            targeting_mode="single_target",
            target_ids=list(request.target_ids),
            payload=dict(request.action_payload),
        )

    def _build_domain_context(
        self,
        request: ActionExecutionRequest,
        encounter: EncounterState,
    ) -> ActionResolutionContext:
        return ActionResolutionContext(
            campaign_id=encounter.campaign_id,
            request_id=request.request_id,
            round_number=encounter.round_number,
            active_actor_id=None,
        )
