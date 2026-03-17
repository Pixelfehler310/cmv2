"""
Integration tests for D&D 5e WebSocket handler.

Tests the full event handling pipeline: envelope → permissions → handler → outbound events.
Uses the handler directly (no real WebSocket connection needed).
"""

import pytest
from unittest.mock import AsyncMock

from src.core.ws_protocol import WsEnvelope, WsOutbound, Visibility
from src.core.sessions.models import SessionContext, UserRole
from src.core.sessions.manager import SessionManager

from src.systems.dnd5e.ws_handler import Dnd5eWsHandler, set_encounter, clear_encounters
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.schemas.instances import ActorInstance, ConditionInstance
from src.systems.dnd5e.schemas.enums import ActorType, ConditionType, DamageType
from src.systems.dnd5e.schemas.common import AbilityScores
from src.systems.dnd5e.services.combat_service import CombatService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup_encounters():
    """Clear encounter storage before each test."""
    clear_encounters()
    yield
    clear_encounters()


@pytest.fixture
def handler():
    return Dnd5eWsHandler()


@pytest.fixture
def dm_ctx():
    return SessionContext(
        campaign_id="test_campaign",
        user_id="dm_user",
        display_name="DM",
        role=UserRole.DM,
        game_system="dnd5e",
    )


@pytest.fixture
def player_ctx():
    return SessionContext(
        campaign_id="test_campaign",
        user_id="player_1",
        display_name="Player 1",
        role=UserRole.PLAYER,
        game_system="dnd5e",
    )


@pytest.fixture
def mgr():
    return SessionManager()


@pytest.fixture
def combat_encounter():
    """An encounter with combatants ready for combat."""
    enc = EncounterState(
        id="enc_test",
        campaign_id="test_campaign",
        combatants=[
            ActorInstance(
                id="fighter_1",
                name="Theron",
                owner_user_id="player_1",
                actor_type=ActorType.PLAYER_CHARACTER,
                current_hp=45,
                max_hp=45,
                armor_class=18,
                abilities=AbilityScores(strength=18, dexterity=14, constitution=14,
                                        intelligence=10, wisdom=12, charisma=8),
            ),
            ActorInstance(
                id="goblin_1",
                name="Goblin",
                owner_user_id="player_2",
                actor_type=ActorType.MONSTER,
                current_hp=7,
                max_hp=7,
                armor_class=15,
                abilities=AbilityScores(strength=8, dexterity=14, constitution=10,
                                        intelligence=10, wisdom=8, charisma=8),
            ),
        ],
    )
    set_encounter("test_campaign", enc)
    return enc


# ---------------------------------------------------------------------------
# Connection Tests
# ---------------------------------------------------------------------------

class TestOnConnect:

    @pytest.mark.anyio
    async def test_connect_receives_state_sync(self, handler, dm_ctx, mgr):
        events = await handler.on_connect(dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "state_sync"
        assert "id" in events[0].payload


# ---------------------------------------------------------------------------
# Ping/Pong Tests
# ---------------------------------------------------------------------------

class TestPingPong:

    @pytest.mark.anyio
    async def test_ping_returns_pong(self, handler, dm_ctx, mgr):
        envelope = WsEnvelope(type="ping")
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "pong"


# ---------------------------------------------------------------------------
# Permission Tests (via handler)
# ---------------------------------------------------------------------------

class TestPermissions:

    @pytest.mark.anyio
    async def test_player_cannot_send_dm_only_actions(self, handler, player_ctx, mgr):
        envelope = WsEnvelope(
            type="apply_damage",
            request_id="req_dm_only_denied",
            payload={"actor_id": "goblin_1",
                     "amount": 10, "damage_type": "slashing"},
        )
        events = await handler.handle(envelope, player_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "unauthorized"

    @pytest.mark.anyio
    async def test_player_request_action_is_routed(self, handler, dm_ctx, player_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_before_player_request"), dm_ctx, mgr)
        envelope = WsEnvelope(
            type="request_action",
            request_id="req_player_request_action",
            payload={"actor_id": "fighter_1",
                     "action_type": "action", "action_name": "attack"},
        )
        events = await handler.handle(envelope, player_ctx, mgr)
        assert len(events) >= 1
        event_types = {event.type for event in events}
        assert event_types & {"action_authorized", "action_denied", "error"}

    @pytest.mark.anyio
    async def test_dm_can_impersonate_player_for_request_action(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="request_action",
            request_id="req_dm_impersonated_denied",
            payload={
                "actor_id": "goblin_1",
                "action_type": "action",
                "action_name": "attack",
                "acting_as_user_id": "player_1",
            },
        )

        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "unauthorized"

    @pytest.mark.anyio
    async def test_player_cannot_spoof_ownership_via_acting_as_user_id(self, handler, player_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="request_action",
            request_id="req_player_spoof_denied",
            payload={
                "actor_id": "goblin_1",
                "action_type": "action",
                "action_name": "attack",
                "acting_as_user_id": "player_2",
            },
        )

        events = await handler.handle(envelope, player_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "unauthorized"

    @pytest.mark.anyio
    async def test_command_requires_request_id(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="move_token",
            payload={"actor_id": "goblin_1", "path": [{"x": 3, "y": 3}]},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].payload["code"] == "invalid_message"

    @pytest.mark.anyio
    async def test_utility_event_allows_missing_request_id(self, handler, dm_ctx, mgr):
        envelope = WsEnvelope(type="ping")
        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "pong"


# ---------------------------------------------------------------------------
# Roll Dice Tests
# ---------------------------------------------------------------------------

class TestRollDice:

    @pytest.mark.anyio
    async def test_roll_dice_returns_result(self, handler, dm_ctx, mgr):
        envelope = WsEnvelope(
            type="roll_dice",
            payload={"expression": "1d20", "purpose": "attack"},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "dice_rolled"
        assert 1 <= events[0].payload["result"] <= 20
        assert events[0].payload["expression"] == "1d20"
        assert events[0].payload["purpose"] == "attack"


# ---------------------------------------------------------------------------
# Chat Tests
# ---------------------------------------------------------------------------

class TestChat:

    @pytest.mark.anyio
    async def test_chat_message_broadcasts_sanitized_payload(self, handler, dm_ctx, mgr):
        envelope = WsEnvelope(
            type="chat_message",
            payload={"message": "  Hold the line!  "},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "chat_message"
        assert events[0].payload["sender_id"] == "dm_user"
        assert events[0].payload["sender_name"] == "DM"
        assert events[0].payload["sender_role"] == "dm"
        assert events[0].payload["message"] == "Hold the line!"

    @pytest.mark.anyio
    async def test_chat_message_empty_text_returns_error(self, handler, dm_ctx, mgr):
        envelope = WsEnvelope(
            type="chat_message",
            payload={"message": "   "},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].payload["code"] == "invalid_message"

    @pytest.mark.anyio
    async def test_player_can_send_chat_message(self, handler, player_ctx, mgr):
        envelope = WsEnvelope(
            type="chat_message",
            payload={"message": "Ready."},
        )
        events = await handler.handle(envelope, player_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "chat_message"
        assert events[0].payload["sender_role"] == "player"


# ---------------------------------------------------------------------------
# Combat Tests
# ---------------------------------------------------------------------------

class TestCombat:

    @pytest.mark.anyio
    async def test_start_combat(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(type="start_combat",
                              request_id="req_start_combat")
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "combat_started"
        assert len(events[0].payload["initiative_order"]) == 2

    @pytest.mark.anyio
    async def test_start_combat_no_combatants(self, handler, dm_ctx, mgr):
        """Starting combat with no combatants returns an error."""
        set_encounter(
            "test_campaign",
            EncounterState(
                id="enc_empty", campaign_id="test_campaign", combatants=[]),
        )
        envelope = WsEnvelope(type="start_combat",
                              request_id="req_start_combat_empty")
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "error"

    @pytest.mark.anyio
    async def test_end_turn_advances(self, handler, dm_ctx, mgr, combat_encounter):
        # Start combat first
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_end_turn"), dm_ctx, mgr)

        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        # End turn
        envelope = WsEnvelope(type="end_turn", request_id="req_end_turn", payload={
                              "actor_id": active_actor_id})
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "turn_advanced"

    @pytest.mark.anyio
    async def test_end_combat(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_end_combat"), dm_ctx, mgr)
        events = await handler.handle(WsEnvelope(type="end_combat", request_id="req_end_combat"), dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "combat_ended"

    @pytest.mark.anyio
    async def test_end_turn_inactive_phase_returns_denied(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(type="end_turn", request_id="req_end_turn_inactive", payload={
                              "actor_id": "fighter_1"})
        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "invalid_turn_phase"

    @pytest.mark.anyio
    async def test_end_turn_wrong_actor_returns_not_your_turn(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_wrong_end_turn"), dm_ctx, mgr)

        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        wrong_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        envelope = WsEnvelope(
            type="end_turn",
            request_id="req_end_turn_wrong_actor",
            payload={"actor_id": wrong_actor_id},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "not_your_turn"


# ---------------------------------------------------------------------------
# Movement Tests
# ---------------------------------------------------------------------------

class TestMovement:

    @pytest.mark.anyio
    async def test_request_attack_preview_returns_eligible_targets(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_attack_preview"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        snapshot_events = await handler.handle(
            WsEnvelope(
                type="request_executable_actions",
                request_id="req_actions_for_attack_preview",
                payload={"actor_id": active_actor_id},
            ),
            dm_ctx,
            mgr,
        )
        assert len(snapshot_events) == 1
        assert snapshot_events[0].type == "executable_actions_snapshot"
        action_id = snapshot_events[0].payload["actions"][0]["action_id"]

        events = await handler.handle(
            WsEnvelope(
                type="request_attack_preview",
                request_id="req_attack_preview_success",
                payload={"actor_id": active_actor_id, "action_id": action_id},
            ),
            dm_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "attack_preview"
        assert events[0].payload["actor_id"] == active_actor_id
        assert events[0].payload["action_id"] == action_id
        assert isinstance(events[0].payload.get("eligible_target_ids"), list)

    @pytest.mark.anyio
    async def test_request_attack_preview_non_owner_denied(self, handler, player_ctx, mgr, combat_encounter):
        events = await handler.handle(
            WsEnvelope(
                type="request_attack_preview",
                request_id="req_attack_preview_denied",
                payload={"actor_id": "goblin_1", "action_id": "basic_attack"},
            ),
            player_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "unauthorized"

    @pytest.mark.anyio
    async def test_request_action_ineligible_target_denied(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_ineligible_target"), dm_ctx, mgr)

        active_actor = combat_encounter.combatants[combat_encounter.active_index]
        target = next(
            c for c in combat_encounter.combatants if c.id != active_actor.id)
        target.position.x = active_actor.position.x + 20
        target.position.y = active_actor.position.y

        snapshot_events = await handler.handle(
            WsEnvelope(
                type="request_executable_actions",
                request_id="req_actions_for_ineligible_target",
                payload={"actor_id": active_actor.id},
            ),
            dm_ctx,
            mgr,
        )
        assert len(snapshot_events) == 1
        assert snapshot_events[0].type == "executable_actions_snapshot"
        action_id = snapshot_events[0].payload["actions"][0]["action_id"]

        events = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_action_ineligible_target",
                payload={
                    "actor_id": active_actor.id,
                    "action_type": "action",
                    "action_name": action_id,
                    "payload": {"target_ids": [target.id]},
                },
            ),
            dm_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "invalid_target"

    @pytest.mark.anyio
    async def test_request_action_aoe_template_origin_out_of_range_denied(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        original_builder = CombatService._build_action_candidates

        def fake_builder(self, actor, monster):
            return [
                {
                    "action_id": "burning_cone",
                    "label": "Burning Cone",
                    "family": "save",
                    "action_type_cost": "action",
                    "targeting_mode": "aoe",
                    "range": 2,
                    "aoe_shape": "cone",
                    "aoe_size": 3,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_action_candidates", fake_builder)

        try:
            await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_aoe_origin_check"), dm_ctx, mgr)
            active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

            events = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_action_aoe_origin_denied",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "action",
                        "action_name": "burning_cone",
                        "payload": {
                            "template_origin": {"x": 30, "y": 30},
                        },
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_action_candidates", original_builder)

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "invalid_target"

    @pytest.mark.anyio
    async def test_request_executable_actions_returns_snapshot(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_action_snapshot"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        events = await handler.handle(
            WsEnvelope(
                type="request_executable_actions",
                request_id="req_executable_actions_success",
                payload={"actor_id": active_actor_id},
            ),
            dm_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "executable_actions_snapshot"
        assert events[0].payload["actor_id"] == active_actor_id
        assert isinstance(events[0].payload.get("actions"), list)
        assert "turn_budget" in events[0].payload

    @pytest.mark.anyio
    async def test_request_executable_actions_non_owner_denied(self, handler, player_ctx, mgr, combat_encounter):
        events = await handler.handle(
            WsEnvelope(
                type="request_executable_actions",
                request_id="req_executable_actions_denied",
                payload={"actor_id": "goblin_1"},
            ),
            player_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "unauthorized"

    @pytest.mark.anyio
    async def test_request_move_preview_returns_reachable_cells(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_move_preview"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        events = await handler.handle(
            WsEnvelope(
                type="request_move_preview",
                request_id="req_move_preview_success",
                payload={"actor_id": active_actor_id},
            ),
            dm_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "movement_preview"
        assert events[0].payload["actor_id"] == active_actor_id
        assert isinstance(events[0].payload["reachable"], list)

    @pytest.mark.anyio
    async def test_request_move_preview_non_active_actor_denied(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_move_preview_denied"), dm_ctx, mgr)

        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        non_active_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        events = await handler.handle(
            WsEnvelope(
                type="request_move_preview",
                request_id="req_move_preview_denied",
                payload={"actor_id": non_active_actor_id},
            ),
            dm_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "not_your_turn"

    @pytest.mark.anyio
    async def test_move_token_updates_actor_and_map_token(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="move_token",
            request_id="req_move_success",
            payload={"actor_id": "goblin_1", "path": [{"x": 12, "y": 14}]},
        )

        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "actor_moved"
        assert events[0].payload["actor_id"] == "goblin_1"
        assert events[0].payload["position"] == {"x": 12, "y": 14}

        goblin = next(
            c for c in combat_encounter.combatants if c.id == "goblin_1")
        assert goblin.position.x == 12
        assert goblin.position.y == 14

        goblin_token = next(
            t for t in combat_encounter.map.tokens if t.actor_id == "goblin_1")
        assert goblin_token.position.x == 12
        assert goblin_token.position.y == 14

    @pytest.mark.anyio
    async def test_move_token_invalid_target_returns_error(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="move_token",
            request_id="req_move_invalid_target",
            payload={"actor_id": "missing_actor", "path": [{"x": 2, "y": 2}]},
        )

        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].payload["code"] == "invalid_target"

    @pytest.mark.anyio
    async def test_player_can_send_move_token(self, handler, player_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="move_token",
            request_id="req_move_player",
            payload={"actor_id": "fighter_1", "path": [{"x": 8, "y": 8}]},
        )

        events = await handler.handle(envelope, player_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "actor_moved"

    @pytest.mark.anyio
    async def test_dm_can_impersonate_player_for_move_token(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="move_token",
            request_id="req_move_impersonated_denied",
            payload={
                "actor_id": "goblin_1",
                "path": [{"x": 8, "y": 8}],
                "acting_as_user_id": "player_1",
            },
        )

        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "unauthorized"

    @pytest.mark.anyio
    async def test_move_token_non_active_actor_denied_in_memory_mode(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_move_turn_check"), dm_ctx, mgr)

        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        non_active_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        envelope = WsEnvelope(
            type="move_token",
            request_id="req_move_non_active_denied",
            payload={"actor_id": non_active_actor_id,
                     "path": [{"x": 9, "y": 9}]},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "not_your_turn"

    @pytest.mark.anyio
    async def test_move_token_path_exceeding_budget_denied_in_memory_mode(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_move_budget"), dm_ctx, mgr)

        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        envelope = WsEnvelope(
            type="move_token",
            request_id="req_move_budget_denied",
            payload={"actor_id": active_actor_id,
                     "path": [{"x": 39, "y": 39}]},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "movement_exhausted"


# ---------------------------------------------------------------------------
# Action Economy Tests
# ---------------------------------------------------------------------------

class TestActionEconomy:

    @pytest.mark.anyio
    async def test_action_budget_exhaustion_in_memory_mode(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_action_economy"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        first = await handler.handle(
            WsEnvelope(
                type="action",
                request_id="req_action_first",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "attack",
                    "action_name": "Longsword",
                    "target_ids": ["goblin_1"],
                },
            ),
            dm_ctx,
            mgr,
        )

        first_types = {event.type for event in first}
        assert "action_authorized" in first_types
        assert "attack_result" in first_types

        second = await handler.handle(
            WsEnvelope(
                type="action",
                request_id="req_action_second",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "action",
                    "action_name": "Second Attack",
                    "target_ids": ["goblin_1"],
                },
            ),
            dm_ctx,
            mgr,
        )

        assert len(second) == 1
        assert second[0].type == "action_denied"
        assert second[0].payload["reason_code"] == "action_exhausted"

    @pytest.mark.anyio
    async def test_bonus_action_budget_exhaustion_in_memory_mode(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_bonus_economy"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        first = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_bonus_first",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "bonus",
                    "action_name": "Second Wind",
                },
            ),
            dm_ctx,
            mgr,
        )
        first_types = {event.type for event in first}
        assert "action_authorized" in first_types
        assert "effect_applied" in first_types

        second = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_bonus_second",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "bonus_action",
                    "action_name": "Second Wind Again",
                },
            ),
            dm_ctx,
            mgr,
        )

        assert len(second) == 1
        assert second[0].type == "action_denied"
        assert second[0].payload["reason_code"] == "bonus_action_exhausted"

    @pytest.mark.anyio
    async def test_reaction_budget_exhaustion_in_memory_mode(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_reaction_economy"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        first = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_reaction_first",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "reaction",
                    "action_name": "Opportunity Attack",
                },
            ),
            dm_ctx,
            mgr,
        )
        first_types = {event.type for event in first}
        assert "action_authorized" in first_types
        assert "effect_applied" in first_types

        second = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_reaction_second",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "reaction",
                    "action_name": "Second Opportunity Attack",
                },
            ),
            dm_ctx,
            mgr,
        )

        assert len(second) == 1
        assert second[0].type == "action_denied"
        assert second[0].payload["reason_code"] == "reaction_exhausted"


# ---------------------------------------------------------------------------
# Action Resolution Tests (Phase 3)
# ---------------------------------------------------------------------------

class TestActionResolutionPhase3:

    @pytest.mark.anyio
    async def test_attack_family_publishes_result_and_damage(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_attack_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        events = await handler.handle(
            WsEnvelope(
                type="action",
                request_id="req_phase3_attack",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "action",
                    "action_name": "Longsword Strike",
                    "target_ids": ["goblin_1"],
                },
            ),
            dm_ctx,
            mgr,
        )

        event_types = {event.type for event in events}
        assert "action_authorized" in event_types
        assert "attack_result" in event_types

    @pytest.mark.anyio
    async def test_save_family_publishes_save_result(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_save_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        events = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_phase3_save",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "action",
                    "action_name": "Fire Breath",
                    "payload": {
                        "family": "save",
                        "save_ability": "dexterity",
                        "save_dc": 18,
                        "damage_dice": "3d6",
                        "damage_type": "fire",
                        "target_ids": ["goblin_1"],
                    },
                },
            ),
            dm_ctx,
            mgr,
        )

        event_types = {event.type for event in events}
        assert "action_authorized" in event_types
        assert "save_result" in event_types

    @pytest.mark.anyio
    async def test_healing_family_publishes_effect_and_heal(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_heal_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        await handler.handle(
            WsEnvelope(
                type="apply_damage",
                request_id="req_phase3_heal_setup_damage",
                payload={"actor_id": active_actor_id,
                         "amount": 6, "damage_type": "slashing"},
            ),
            dm_ctx,
            mgr,
        )

        events = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_phase3_heal",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "bonus_action",
                    "action_name": "Second Wind",
                    "payload": {
                        "family": "healing",
                        "target_ids": [active_actor_id],
                        "heal_dice": "1d8",
                        "heal_bonus": 2,
                    },
                },
            ),
            dm_ctx,
            mgr,
        )

        event_types = {event.type for event in events}
        assert "action_authorized" in event_types
        assert "effect_applied" in event_types
        assert "actor_healed" in event_types

    @pytest.mark.anyio
    async def test_utility_family_publishes_effect_and_condition(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_utility_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        events = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_phase3_utility",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "reaction",
                    "action_name": "Trip",
                    "payload": {
                        "family": "utility",
                        "condition": "Prone",
                        "target_ids": ["goblin_1"],
                    },
                },
            ),
            dm_ctx,
            mgr,
        )

        event_types = {event.type for event in events}
        assert "action_authorized" in event_types
        assert "effect_applied" in event_types
        assert "condition_added" in event_types


# ---------------------------------------------------------------------------
# Actor Spawn Tests
# ---------------------------------------------------------------------------

class TestAddActor:

    @pytest.mark.anyio
    async def test_add_actor_adds_combatant_and_token(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="add_actor",
            request_id="req_add_actor",
            payload={
                "definition_slug": "orc-warrior",
                "name": "Orc Brute",
                "position": {"x": 9, "y": 10},
            },
        )

        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "actor_added"
        assert events[0].payload["actor"]["definition_slug"] == "orc-warrior"
        assert events[0].payload["actor"]["name"] == "Orc Brute"
        assert events[0].payload["actor"]["position"] == {
            "x": 9, "y": 10, "elevation": 0}

        added_actor_id = events[0].payload["actor"]["id"]
        added_actor = next(
            c for c in combat_encounter.combatants if c.id == added_actor_id)
        assert added_actor.position.x == 9
        assert added_actor.position.y == 10

        added_token = next(
            t for t in combat_encounter.map.tokens if t.actor_id == added_actor_id)
        assert added_token.position.x == 9
        assert added_token.position.y == 10

    @pytest.mark.anyio
    async def test_add_actor_invalid_position_returns_error(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="add_actor",
            request_id="req_add_actor_invalid_pos",
            payload={
                "definition_slug": "goblin",
                "position": {"x": 999, "y": 1},
            },
        )

        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].payload["code"] == "invalid_action"

    @pytest.mark.anyio
    async def test_player_cannot_add_actor(self, handler, player_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="add_actor",
            request_id="req_add_actor_player_denied",
            payload={"definition_slug": "goblin",
                     "position": {"x": 1, "y": 1}},
        )

        events = await handler.handle(envelope, player_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "unauthorized"


# ---------------------------------------------------------------------------
# Actor Removal Tests
# ---------------------------------------------------------------------------

class TestRemoveActor:

    @pytest.mark.anyio
    async def test_remove_actor_removes_combatant_and_token(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="remove_actor",
            request_id="req_remove_actor",
            payload={"actor_id": "goblin_1"},
        )

        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "actor_removed"
        assert events[0].payload["actor_id"] == "goblin_1"

        assert all(c.id != "goblin_1" for c in combat_encounter.combatants)
        assert all(t.actor_id != "goblin_1" for t in combat_encounter.map.tokens)

    @pytest.mark.anyio
    async def test_remove_actor_invalid_target_returns_error(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="remove_actor",
            request_id="req_remove_actor_invalid",
            payload={"actor_id": "missing_actor"},
        )

        events = await handler.handle(envelope, dm_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].payload["code"] == "invalid_target"

    @pytest.mark.anyio
    async def test_player_cannot_remove_actor(self, handler, player_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="remove_actor",
            request_id="req_remove_actor_player_denied",
            payload={"actor_id": "goblin_1"},
        )

        events = await handler.handle(envelope, player_ctx, mgr)

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "unauthorized"


# ---------------------------------------------------------------------------
# Damage / Healing Tests
# ---------------------------------------------------------------------------

class TestDamageHealing:

    @pytest.mark.anyio
    async def test_apply_damage(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="apply_damage",
            request_id="req_apply_damage",
            payload={"actor_id": "goblin_1",
                     "amount": 5, "damage_type": "slashing"},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert any(e.type == "actor_damaged" for e in events)
        damaged = next(e for e in events if e.type == "actor_damaged")
        assert damaged.payload["new_hp"] == 2

    @pytest.mark.anyio
    async def test_apply_lethal_damage(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="apply_damage",
            request_id="req_apply_lethal_damage",
            payload={"actor_id": "goblin_1",
                     "amount": 20, "damage_type": "slashing"},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert any(e.type == "actor_died" for e in events)

    @pytest.mark.anyio
    async def test_apply_healing(self, handler, dm_ctx, mgr, combat_encounter):
        # Damage first
        await handler.handle(
            WsEnvelope(type="apply_damage", payload={
                       "actor_id": "fighter_1", "amount": 10, "damage_type": "slashing"}, request_id="req_damage_before_heal"),
            dm_ctx, mgr,
        )

        # Heal
        envelope = WsEnvelope(
            type="apply_healing",
            request_id="req_apply_healing",
            payload={"actor_id": "fighter_1", "amount": 5},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "actor_healed"
        assert events[0].payload["new_hp"] == 40

    @pytest.mark.anyio
    async def test_healing_capped_at_max(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="apply_healing",
            request_id="req_heal_cap",
            payload={"actor_id": "fighter_1", "amount": 100},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert events[0].payload["new_hp"] == 45  # max_hp

    @pytest.mark.anyio
    async def test_damage_invalid_target(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="apply_damage",
            request_id="req_damage_invalid_target",
            payload={"actor_id": "nonexistent",
                     "amount": 5, "damage_type": "slashing"},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert events[0].type == "error"
        assert "not found" in events[0].payload["message"]


# ---------------------------------------------------------------------------
# Condition Tests
# ---------------------------------------------------------------------------

class TestConditions:

    @pytest.mark.anyio
    async def test_apply_condition(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="apply_condition",
            request_id="req_apply_condition",
            payload={"actor_id": "goblin_1", "condition": "Stunned"},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert events[0].type == "condition_added"
        assert events[0].payload["condition"] == "Stunned"

        # Verify it was actually applied
        goblin = combat_encounter.combatants[1]
        assert any(c.condition ==
                   ConditionType.STUNNED for c in goblin.conditions)

    @pytest.mark.anyio
    async def test_remove_condition(self, handler, dm_ctx, mgr, combat_encounter):
        # Apply first
        goblin = combat_encounter.combatants[1]
        goblin.conditions.append(
            ConditionInstance(condition=ConditionType.PRONE))

        envelope = WsEnvelope(
            type="remove_condition",
            request_id="req_remove_condition",
            payload={"actor_id": "goblin_1", "condition": "Prone"},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert events[0].type == "condition_removed"
        assert not any(
            c.condition == ConditionType.PRONE for c in goblin.conditions)

    @pytest.mark.anyio
    async def test_invalid_condition(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="apply_condition",
            request_id="req_invalid_condition",
            payload={"actor_id": "goblin_1", "condition": "NotACondition"},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert events[0].type == "error"


# ---------------------------------------------------------------------------
# Unknown event
# ---------------------------------------------------------------------------

class TestUnknownEvent:

    @pytest.mark.anyio
    async def test_unknown_event_returns_error(self, handler, dm_ctx, mgr):
        envelope = WsEnvelope(type="nonexistent_event")
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert events[0].type == "error"
        assert "Unknown" in events[0].payload["message"]


# ---------------------------------------------------------------------------
# Stage E terminal guarantees
# ---------------------------------------------------------------------------

class TestCommandTerminalGuaranteesStageE:

    @pytest.mark.anyio
    async def test_preview_commands_emit_terminal_outbound_on_success(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_stage_e_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        snapshot_events = await handler.handle(
            WsEnvelope(
                type="request_executable_actions",
                request_id="req_stage_e_actions_seed",
                payload={"actor_id": active_actor_id},
            ),
            dm_ctx,
            mgr,
        )
        assert len(snapshot_events) == 1
        assert snapshot_events[0].type == "executable_actions_snapshot"
        action_id = snapshot_events[0].payload["actions"][0]["action_id"]

        checks = [
            (
                WsEnvelope(
                    type="request_executable_actions",
                    request_id="req_stage_e_actions",
                    payload={"actor_id": active_actor_id},
                ),
                "executable_actions_snapshot",
            ),
            (
                WsEnvelope(
                    type="request_move_preview",
                    request_id="req_stage_e_move_preview",
                    payload={"actor_id": active_actor_id},
                ),
                "movement_preview",
            ),
            (
                WsEnvelope(
                    type="request_attack_preview",
                    request_id="req_stage_e_attack_preview",
                    payload={"actor_id": active_actor_id,
                             "action_id": action_id},
                ),
                "attack_preview",
            ),
        ]

        for envelope, expected_type in checks:
            events = await handler.handle(envelope, dm_ctx, mgr)
            assert len(events) >= 1
            assert events[0].type == expected_type
            assert events[0].request_id == envelope.request_id

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "event_type,payload",
        [
            ("request_executable_actions", {}),
            ("request_move_preview", {}),
            ("request_attack_preview", {"actor_id": "fighter_1"}),
        ],
    )
    async def test_preview_commands_emit_error_on_invalid_payload(self, handler, dm_ctx, mgr, combat_encounter, event_type, payload):
        request_id = f"req_stage_e_invalid_{event_type}"
        events = await handler.handle(
            WsEnvelope(type=event_type, request_id=request_id,
                       payload=payload),
            dm_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].payload["code"] == "invalid_message"
        assert events[0].request_id == request_id
