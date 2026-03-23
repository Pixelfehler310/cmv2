from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.sessions.models import SessionContext, UserRole
from src.systems.dnd5e.application.action_execution_service import (
    ActionExecutionApplicationService,
    ActionExecutionRequest,
)
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.services.combat_service import CombatService


@pytest.fixture
def dm_ctx() -> SessionContext:
    return SessionContext(
        campaign_id="camp_test",
        user_id="dm_user",
        display_name="DM",
        role=UserRole.DM,
        game_system="dnd5e",
    )


@pytest.fixture
def empty_encounter() -> EncounterState:
    return EncounterState(id="enc_test", campaign_id="camp_test", combatants=[])


@pytest.mark.anyio
async def test_action_execution_service_success_with_repository_mocked_combat_service(
    dm_ctx: SessionContext,
    empty_encounter: EncounterState,
):
    db = AsyncMock(spec=AsyncSession)
    service = CombatService(
        db,
        context_read_repository=AsyncMock(),
        encounter_session_repository=AsyncMock(),
        action_catalog_repository=AsyncMock(),
        action_execution_repository=AsyncMock(),
    )
    service.execute_action = AsyncMock(
        return_value=[
            {
                "type": "action_authorized",
                "payload": {"actor_id": "fighter_1", "action_type": "action"},
            }
        ]
    )

    app_service = ActionExecutionApplicationService(service)
    request = ActionExecutionRequest(
        actor_id="fighter_1",
        action_type="attack",
        action_name="canonical_longsword",
        target_ids=["goblin_1"],
        request_id="req_1",
        raw_payload={"actor_id": "fighter_1"},
        require_canonical_action_id=True,
    )

    result = await app_service.execute(request, empty_encounter, encounter_session=None, ctx=dm_ctx)

    assert len(result.events) == 1
    assert result.events[0]["type"] == "action_authorized"
    service.execute_action.assert_awaited_once()
    kwargs = service.execute_action.await_args.kwargs
    assert kwargs["actor_id"] == "fighter_1"
    assert kwargs["action_name"] == "canonical_longsword"
    assert kwargs["action_type"] == "action"
    assert kwargs["target_ids"] == ["goblin_1"]
    assert kwargs["request_id"] == "req_1"
    assert kwargs["raw_payload"] == {"actor_id": "fighter_1"}
    assert kwargs["ctx"] == dm_ctx
    assert kwargs["encounter"] == empty_encounter
    assert kwargs["encounter_session"] is None
    assert kwargs["require_canonical_action_id"] is True


@pytest.mark.anyio
async def test_action_execution_service_denied_passthrough(
    dm_ctx: SessionContext,
    empty_encounter: EncounterState,
):
    db = AsyncMock(spec=AsyncSession)
    service = CombatService(
        db,
        context_read_repository=AsyncMock(),
        encounter_session_repository=AsyncMock(),
        action_catalog_repository=AsyncMock(),
        action_execution_repository=AsyncMock(),
    )
    service.execute_action = AsyncMock(
        return_value=[
            {
                "type": "denied",
                "reason_code": "not_your_turn",
                "message": "This actor is not the active turn",
                "actor_id": "fighter_1",
                "action_type": "action",
            }
        ]
    )

    app_service = ActionExecutionApplicationService(service)
    request = ActionExecutionRequest(
        actor_id="fighter_1",
        action_type="action",
        action_name="canonical_longsword",
        request_id="req_2",
        raw_payload={"actor_id": "fighter_1"},
    )

    result = await app_service.execute(request, empty_encounter, encounter_session=None, ctx=dm_ctx)

    assert len(result.events) == 1
    assert result.events[0]["type"] == "denied"
    assert result.events[0]["reason_code"] == "not_your_turn"
    kwargs = service.execute_action.await_args.kwargs
    assert kwargs["action_type"] == "action"


@pytest.mark.anyio
async def test_action_execution_service_invalid_action_passthrough(
    dm_ctx: SessionContext,
    empty_encounter: EncounterState,
):
    db = AsyncMock(spec=AsyncSession)
    service = CombatService(
        db,
        context_read_repository=AsyncMock(),
        encounter_session_repository=AsyncMock(),
        action_catalog_repository=AsyncMock(),
        action_execution_repository=AsyncMock(),
    )
    service.execute_action = AsyncMock(
        return_value=[
            {
                "type": "denied",
                "reason_code": "invalid_action",
                "message": "Unknown canonical action_id for actor",
                "actor_id": "fighter_1",
                "action_type": "action",
            }
        ]
    )

    app_service = ActionExecutionApplicationService(service)
    request = ActionExecutionRequest(
        actor_id="fighter_1",
        action_type="action",
        action_name="unknown_action",
        request_id="req_3",
        raw_payload={"actor_id": "fighter_1"},
    )

    result = await app_service.execute(request, empty_encounter, encounter_session=None, ctx=dm_ctx)

    assert len(result.events) == 1
    assert result.events[0]["type"] == "denied"
    assert result.events[0]["reason_code"] == "invalid_action"
    kwargs = service.execute_action.await_args.kwargs
    assert kwargs["action_name"] == "unknown_action"
