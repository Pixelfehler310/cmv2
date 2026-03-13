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
            payload={"actor_id": "goblin_1",
                     "amount": 10, "damage_type": "slashing"},
        )
        events = await handler.handle(envelope, player_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].payload["code"] == "unauthorized"


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
# Combat Tests
# ---------------------------------------------------------------------------

class TestCombat:

    @pytest.mark.anyio
    async def test_start_combat(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(type="start_combat")
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
        envelope = WsEnvelope(type="start_combat")
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "error"

    @pytest.mark.anyio
    async def test_end_turn_advances(self, handler, dm_ctx, mgr, combat_encounter):
        # Start combat first
        await handler.handle(WsEnvelope(type="start_combat"), dm_ctx, mgr)

        # End turn
        envelope = WsEnvelope(type="end_turn", payload={
                              "actor_id": "fighter_1"})
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "turn_advanced"

    @pytest.mark.anyio
    async def test_end_combat(self, handler, dm_ctx, mgr, combat_encounter):
        await handler.handle(WsEnvelope(type="start_combat"), dm_ctx, mgr)
        events = await handler.handle(WsEnvelope(type="end_combat"), dm_ctx, mgr)
        assert len(events) == 1
        assert events[0].type == "combat_ended"


# ---------------------------------------------------------------------------
# Damage / Healing Tests
# ---------------------------------------------------------------------------

class TestDamageHealing:

    @pytest.mark.anyio
    async def test_apply_damage(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="apply_damage",
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
                       "actor_id": "fighter_1", "amount": 10, "damage_type": "slashing"}),
            dm_ctx, mgr,
        )

        # Heal
        envelope = WsEnvelope(
            type="apply_healing",
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
            payload={"actor_id": "fighter_1", "amount": 100},
        )
        events = await handler.handle(envelope, dm_ctx, mgr)
        assert events[0].payload["new_hp"] == 45  # max_hp

    @pytest.mark.anyio
    async def test_damage_invalid_target(self, handler, dm_ctx, mgr, combat_encounter):
        envelope = WsEnvelope(
            type="apply_damage",
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
