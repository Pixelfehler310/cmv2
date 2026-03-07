"""
Integration Test Suite 3: WebSocket Server-Client Integration.

Tests the full WebSocket pipeline using FastAPI's TestClient, including:
- JWT authentication
- Real WebSocket message transport
- DM/player role enforcement
- Full combat flow over WebSocket

These tests exercise the real ws_dispatcher → ws_handler → engine chain.
"""

import json
import pytest
from jose import jwt

from starlette.testclient import TestClient

from src.main import app
from src.config import settings
from src.systems.dnd5e.ws_handler import set_encounter, clear_encounters
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.schemas.instances import ActorInstance, ConditionInstance
from src.systems.dnd5e.schemas.enums import ActorType, ConditionType
from src.systems.dnd5e.schemas.common import AbilityScores


# ---------------------------------------------------------------------------
# JWT Helpers
# ---------------------------------------------------------------------------

def _make_jwt(username: str = "test_dm", display_name: str = "Test DM") -> str:
    """Create a valid JWT token for testing."""
    payload = {"sub": username, "display_name": display_name}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Encounter Setup
# ---------------------------------------------------------------------------

def _setup_combat_encounter(campaign_id: str = "ws_test_campaign") -> EncounterState:
    """Create and register an encounter for WebSocket tests."""
    enc = EncounterState(
        id="enc_ws_test",
        campaign_id=campaign_id,
        combatants=[
            ActorInstance(
                id="fighter_1",
                name="Theron",
                actor_type=ActorType.PLAYER_CHARACTER,
                current_hp=45,
                max_hp=45,
                armor_class=18,
                abilities=AbilityScores(
                    strength=18, dexterity=14, constitution=14,
                    intelligence=10, wisdom=12, charisma=8,
                ),
            ),
            ActorInstance(
                id="goblin_1",
                name="Goblin",
                actor_type=ActorType.MONSTER,
                current_hp=7,
                max_hp=7,
                armor_class=15,
                abilities=AbilityScores(
                    strength=8, dexterity=14, constitution=10,
                    intelligence=10, wisdom=8, charisma=8,
                ),
            ),
        ],
    )
    set_encounter(campaign_id, enc)
    return enc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup():
    """Clear encounters before and after each test."""
    clear_encounters()
    yield
    clear_encounters()


from src.core.ws_dispatcher import register_system_handler
from src.systems.dnd5e.ws_handler import Dnd5eWsHandler

@pytest.fixture
def client():
    """Synchronous TestClient for WebSocket testing."""
    register_system_handler("dnd5e", Dnd5eWsHandler())
    return TestClient(app)


# ---------------------------------------------------------------------------
# Test: Authentication
# ---------------------------------------------------------------------------

class TestWebSocketAuth:

    def test_connect_with_valid_jwt_receives_state_sync(self, client):
        """Valid JWT → accepted → receives state_sync message."""
        token = _make_jwt()
        _setup_combat_encounter()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            msg = ws.receive_json()
            assert msg["type"] == "state_sync"
            assert "payload" in msg

    def test_connect_without_jwt_is_rejected(self, client):
        """No token → connection closed with 4001."""
        try:
            with client.websocket_connect("/ws/test_campaign") as ws:
                # Should not reach here
                pytest.fail("Expected connection to be rejected")
        except Exception:
            # Connection rejected — success
            pass

    def test_connect_with_invalid_jwt_is_rejected(self, client):
        """Invalid/expired token → connection closed."""
        bad_token = jwt.encode(
            {"sub": "hacker"},
            "wrong_secret_key",
            algorithm="HS256",
        )
        try:
            with client.websocket_connect(
                f"/ws/test_campaign?token={bad_token}&role=dm"
            ) as ws:
                pytest.fail("Expected connection to be rejected")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Test: Full Combat Flow Over WebSocket
# ---------------------------------------------------------------------------

class TestCombatFlowOverWS:

    def test_full_combat_flow(self, client):
        """DM connects → starts combat → applies damage → ends turn."""
        token = _make_jwt()
        _setup_combat_encounter()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            # 1. Receive state_sync
            sync = ws.receive_json()
            assert sync["type"] == "state_sync"

            # 2. Start combat
            ws.send_json({"type": "start_combat"})
            result = ws.receive_json()
            assert result["type"] == "combat_started"
            assert len(result["payload"]["initiative_order"]) == 2

            # 3. Apply damage to goblin
            ws.send_json({
                "type": "apply_damage",
                "payload": {
                    "actor_id": "goblin_1",
                    "amount": 5,
                    "damage_type": "slashing",
                },
            })
            dmg_result = ws.receive_json()
            assert dmg_result["type"] == "actor_damaged"
            assert dmg_result["payload"]["new_hp"] == 2

            # 4. End turn
            ws.send_json({
                "type": "end_turn",
                "payload": {"actor_id": "fighter_1"},
            })
            turn_result = ws.receive_json()
            assert turn_result["type"] == "turn_advanced"

    def test_lethal_damage_over_ws(self, client):
        """Apply enough damage to kill a monster → actor_died event."""
        token = _make_jwt()
        _setup_combat_encounter()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            ws.receive_json()  # state_sync

            ws.send_json({
                "type": "apply_damage",
                "payload": {
                    "actor_id": "goblin_1",
                    "amount": 20,
                    "damage_type": "slashing",
                },
            })
            damaged_event = ws.receive_json()
            assert damaged_event["type"] == "actor_damaged"
            
            result = ws.receive_json()
            # Should get actor_died event
            assert result["type"] == "actor_died"


# ---------------------------------------------------------------------------
# Test: DM/Player Role Enforcement
# ---------------------------------------------------------------------------

class TestRoleEnforcement:

    def test_player_cannot_apply_damage(self, client):
        """Player role → apply_damage rejected with unauthorized error."""
        token = _make_jwt(username="player_1", display_name="Player 1")
        _setup_combat_encounter()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=player"
        ) as ws:
            ws.receive_json()  # state_sync

            ws.send_json({
                "type": "apply_damage",
                "payload": {
                    "actor_id": "goblin_1",
                    "amount": 5,
                    "damage_type": "slashing",
                },
            })
            error = ws.receive_json()
            assert error["type"] == "error"
            assert error["payload"]["code"] == "unauthorized"


# ---------------------------------------------------------------------------
# Test: Dice Rolling Over WebSocket
# ---------------------------------------------------------------------------

class TestDiceRollingOverWS:

    def test_roll_dice_via_ws(self, client):
        """Roll dice and get a valid result back."""
        token = _make_jwt()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            ws.receive_json()  # state_sync

            ws.send_json({
                "type": "roll_dice",
                "payload": {
                    "expression": "2d6+3",
                    "purpose": "damage",
                },
            })
            result = ws.receive_json()
            assert result["type"] == "dice_rolled"
            assert 5 <= result["payload"]["result"] <= 15  # 2d6+3 = [5, 15]
            assert result["payload"]["expression"] == "2d6+3"

    def test_roll_d20_via_ws(self, client):
        """Roll a d20 and get result in valid range."""
        token = _make_jwt()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            ws.receive_json()  # state_sync

            ws.send_json({
                "type": "roll_dice",
                "payload": {"expression": "1d20", "purpose": "attack"},
            })
            result = ws.receive_json()
            assert result["type"] == "dice_rolled"
            assert 1 <= result["payload"]["result"] <= 20


# ---------------------------------------------------------------------------
# Test: Condition Management Over WebSocket
# ---------------------------------------------------------------------------

class TestConditionManagementOverWS:

    def test_apply_and_remove_condition(self, client):
        """DM applies Stunned condition, then removes it."""
        token = _make_jwt()
        _setup_combat_encounter()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            ws.receive_json()  # state_sync

            # Apply Stunned
            ws.send_json({
                "type": "apply_condition",
                "payload": {"actor_id": "goblin_1", "condition": "Stunned"},
            })
            result = ws.receive_json()
            assert result["type"] == "condition_added"
            assert result["payload"]["condition"] == "Stunned"

            # Remove Stunned
            ws.send_json({
                "type": "remove_condition",
                "payload": {"actor_id": "goblin_1", "condition": "Stunned"},
            })
            result = ws.receive_json()
            assert result["type"] == "condition_removed"

    def test_invalid_condition_returns_error(self, client):
        """Applying a non-existent condition returns an error."""
        token = _make_jwt()
        _setup_combat_encounter()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            ws.receive_json()  # state_sync

            ws.send_json({
                "type": "apply_condition",
                "payload": {"actor_id": "goblin_1", "condition": "FakeCondition"},
            })
            result = ws.receive_json()
            assert result["type"] == "error"


# ---------------------------------------------------------------------------
# Test: Healing Over WebSocket
# ---------------------------------------------------------------------------

class TestHealingOverWS:

    def test_heal_and_cap_at_max(self, client):
        """Damage fighter, then heal — verify HP capped at max."""
        token = _make_jwt()
        _setup_combat_encounter()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            ws.receive_json()  # state_sync

            # Damage fighter
            ws.send_json({
                "type": "apply_damage",
                "payload": {
                    "actor_id": "fighter_1",
                    "amount": 10,
                    "damage_type": "slashing",
                },
            })
            dmg = ws.receive_json()
            assert dmg["payload"]["new_hp"] == 35

            # Heal fighter
            ws.send_json({
                "type": "apply_healing",
                "payload": {"actor_id": "fighter_1", "amount": 5},
            })
            heal = ws.receive_json()
            assert heal["type"] == "actor_healed"
            assert heal["payload"]["new_hp"] == 40

            # Over-heal → cap at max_hp
            ws.send_json({
                "type": "apply_healing",
                "payload": {"actor_id": "fighter_1", "amount": 100},
            })
            heal2 = ws.receive_json()
            assert heal2["payload"]["new_hp"] == 45  # max HP


# ---------------------------------------------------------------------------
# Test: Error Handling
# ---------------------------------------------------------------------------

class TestWSErrorHandling:

    def test_unknown_event_returns_error(self, client):
        """Sending an unrecognized event type returns an error."""
        token = _make_jwt()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            ws.receive_json()  # state_sync

            ws.send_json({"type": "nonexistent_event"})
            result = ws.receive_json()
            assert result["type"] == "error"
            assert "Unknown" in result["payload"]["message"]

    def test_damage_invalid_target_returns_error(self, client):
        """Applying damage to a non-existent actor returns an error."""
        token = _make_jwt()
        _setup_combat_encounter()

        with client.websocket_connect(
            f"/ws/ws_test_campaign?token={token}&role=dm"
        ) as ws:
            ws.receive_json()  # state_sync

            ws.send_json({
                "type": "apply_damage",
                "payload": {
                    "actor_id": "nonexistent",
                    "amount": 5,
                    "damage_type": "slashing",
                },
            })
            result = ws.receive_json()
            assert result["type"] == "error"
            assert "not found" in result["payload"]["message"]
