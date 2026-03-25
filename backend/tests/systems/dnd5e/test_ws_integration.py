from __future__ import annotations
"""
Integration tests for D&D 5e WebSocket handler.

Tests the full event handling pipeline: envelope → permissions → handler → outbound events.
Uses the handler directly (no real WebSocket connection needed).
"""

import pytest
from unittest.mock import AsyncMock
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import re
from src.config import settings
from src.database import Base
from src.core.ws_protocol import WsEnvelope, WsOutbound, Visibility
from src.core.sessions.models import ConnectedUser, SessionContext, UserRole
from src.core.sessions.manager import SessionManager

import src.systems.dnd5e.ws_handler as ws_handler_module
from src.campaigns.lib.campaign import Campaign
from src.systems.dnd5e.ws_handler import Dnd5eWsHandler
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.schemas.instances import ActorInstance, ConditionInstance, EffectInstance
from src.systems.dnd5e.schemas.enums import ActorType, ConditionType, DamageType, DurationType
from src.systems.dnd5e.schemas.common import AbilityScores
from src.systems.dnd5e.lib.combat_models import EncounterSession
from src.systems.dnd5e.lib.context_models import SceneCatalogRecord, EncounterCatalogRecord
from src.systems.dnd5e.lib.content_models import EffectDefinitionRecord, EffectInstanceRecord
from src.systems.dnd5e.services.combat_service import CombatService
from src import database as db_module

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Override the real DB with an in-memory one for all tests in this module."""
    # Patch both the original and the one imported by ws_handler
    monkeypatch.setattr(db_module, "AsyncSessionLocal", TestAsyncSessionLocal)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(
        "src.systems.dnd5e.ws_handler.AsyncSessionLocal", TestAsyncSessionLocal)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def cleanup_db():
    """Ensure a clean database before each test using the test engine."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed baseline campaign + context catalog so ws connect and command tests
    # have a valid backend-authoritative selection context.
    async with TestAsyncSessionLocal() as db:
        db.add(
            Campaign(
                id="test_campaign",
                name="WS Integration Campaign",
                current_scene="scene.default",
                active_encounter_id="enc_test_campaign",
                context_version=1,
            )
        )
        db.add(
            SceneCatalogRecord(
                campaign_id="test_campaign",
                scene_id="scene.default",
                name="Default Scene",
            )
        )
        db.add(
            EncounterCatalogRecord(
                campaign_id="test_campaign",
                scene_id="scene.default",
                encounter_id="enc_test_campaign",
                name="Initial Encounter",
                source="test",
                state_json=EncounterState(
                    id="enc_test_campaign",
                    campaign_id="test_campaign",
                    combatants=[],
                ).model_dump(mode="json"),
            )
        )
        await db.commit()

    yield


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
async def combat_encounter(dm_ctx):
    """An encounter with combatants ready for combat, saved to the real DB."""
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

    async with db_module.AsyncSessionLocal() as db:
        service = CombatService(db)
        # Use our updated service to save the state
        session, _ = await service.load_or_create_encounter_state("test_campaign")
        await service.save_full_state(session, enc)

        # Keep campaign context selection aligned with the test encounter.
        campaign = await db.get(Campaign, "test_campaign")
        if campaign is not None:
            campaign.current_scene = "scene.default"
            campaign.active_encounter_id = enc.id

        existing = await db.execute(
            select(EncounterCatalogRecord).where(
                EncounterCatalogRecord.campaign_id == "test_campaign",
                EncounterCatalogRecord.scene_id == "scene.default",
                EncounterCatalogRecord.encounter_id == enc.id,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                EncounterCatalogRecord(
                    campaign_id="test_campaign",
                    scene_id="scene.default",
                    encounter_id=enc.id,
                    name="Combat Encounter",
                    source="test",
                    state_json=enc.model_dump(mode="json"),
                )
            )

        await db.commit()
        return enc


async def refresh_encounter(campaign_id="test_campaign"):
    async with TestAsyncSessionLocal() as db:
        service = CombatService(db)
        _, encounter = await service.load_or_create_encounter_state(campaign_id)
        return encounter


def _canonical_candidate(
    action_id: str,
    label: str,
    *,
    family: str = "attack",
    action_type_cost: str = "action",
    targeting_mode: str = "single_target",
    range_value: int | None = 5,
    save_context: dict | None = None,
    attack_context: dict | None = None,
    effect_intents: list | None = None,
) -> dict:
    return {
        "action_id": action_id,
        "name": label,
        "label": label,
        "family": family,
        "action_type_cost": action_type_cost,
        "targeting_mode": targeting_mode,
        "range": range_value,
        "save_context": save_context,
        "attack_context": attack_context,
        "effect_intents": list(effect_intents or []),
        "tags": [],
        "source_ref": "custom",
        "content_version": "1",
        "enabled": True,
    }


# ---------------------------------------------------------------------------
# Connection Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
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

@pytest.mark.anyio
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

@pytest.mark.anyio
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
    async def test_player_request_action_is_routed(self, handler, dm_ctx, player_ctx, mgr, combat_encounter, monkeypatch):
        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != "fighter_1":
                return []
            return [
                {
                    "action_id": "attack",
                    "name": "Attack",
                    "label": "Attack",
                    "family": "attack",
                    "action_type_cost": "action",
                    "targeting_mode": "single_target",
                    "range": 5,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_before_player_request"), dm_ctx, mgr)
        envelope = WsEnvelope(
            type="request_action",
            request_id="req_player_request_action",
            payload={"actor_id": "fighter_1",
                     "action_type": "action", "action_name": "attack"},
        )
        try:
            events = await handler.handle(envelope, player_ctx, mgr)
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        assert len(events) >= 1
        event_types = {event.type for event in events}
        assert event_types & {"action_authorized", "action_denied", "error"}

    @pytest.mark.anyio
    async def test_request_action_unknown_action_id_denied_in_strict_mode(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        monkeypatch.setattr(settings, "ALLOW_LEGACY_ACTION_NAMES", True)
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_strict_unknown_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        events = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_strict_unknown_action",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "action",
                    "action_name": "legacy_attack_name",
                    "payload": {"target_ids": [c.id for c in combat_encounter.combatants if c.id != active_actor_id]},
                },
            ),
            dm_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "invalid_action"

    @pytest.mark.anyio
    async def test_request_action_roll_override_denied_by_policy(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        monkeypatch.setattr(settings, "ALLOW_CLIENT_ROLL_OVERRIDES", False)

        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != combat_encounter.combatants[combat_encounter.active_index].id:
                return []
            return [_canonical_candidate("canonical_policy_attack", "Canonical Policy Attack")]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        try:
            await handler.handle(WsEnvelope(type="start_combat", request_id="req_roll_policy_start"), dm_ctx, mgr)
            active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
            target_actor_id = next(
                actor.id for actor in combat_encounter.combatants if actor.id != active_actor_id
            )

            events = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_roll_policy_denied",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "action",
                        "action_name": "canonical_policy_attack",
                        "payload": {
                            "target_ids": [target_actor_id],
                            "roll_override": 20,
                        },
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "roll_override_not_allowed"

    @pytest.mark.anyio
    async def test_request_action_event_order_authorized_before_results(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != combat_encounter.combatants[combat_encounter.active_index].id:
                return []
            return [
                {
                    "action_id": "canonical_order_attack",
                    "name": "Canonical Order Attack",
                    "label": "Canonical Order Attack",
                    "family": "attack",
                    "action_type_cost": "action",
                    "targeting_mode": "single_target",
                    "range": 30,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        try:
            await handler.handle(WsEnvelope(type="start_combat", request_id="req_order_start"), dm_ctx, mgr)
            active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
            target_actor_id = next(
                actor.id for actor in combat_encounter.combatants if actor.id != active_actor_id
            )

            events = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_order_action",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "action",
                        "action_name": "canonical_order_attack",
                        "payload": {"target_ids": [target_actor_id]},
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        event_types = [event.type for event in events]
        assert "action_authorized" in event_types
        assert "attack_result" in event_types
        assert event_types.index(
            "action_authorized") < event_types.index("attack_result")

    @pytest.mark.anyio
    async def test_dm_can_delegate_to_player_for_request_action(self, handler, dm_ctx, mgr, combat_encounter):
        mgr.register_connection(
            dm_ctx.campaign_id,
            ConnectedUser(user_id="dm_user", display_name="DM",
                          role=UserRole.DM, ws=object()),
        )
        mgr.register_connection(
            dm_ctx.campaign_id,
            ConnectedUser(user_id="player_1", display_name="Player 1",
                          role=UserRole.PLAYER, ws=object()),
        )

        start_events = await handler.handle(
            WsEnvelope(
                type="delegate_start",
                request_id="req_delegate_start_action",
                payload={"target_user_id": "player_1"},
            ),
            dm_ctx,
            mgr,
        )
        assert len(start_events) == 1
        assert start_events[0].type == "delegation_started"

        events = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_dm_delegated_denied",
                payload={
                    "actor_id": "goblin_1",
                    "action_type": "action",
                    "action_name": "attack",
                },
            ),
            dm_ctx,
            mgr,
        )

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
    async def test_player_cannot_start_delegation(self, handler, player_ctx, mgr):
        events = await handler.handle(
            WsEnvelope(
                type="delegate_start",
                request_id="req_delegate_start_player_denied",
                payload={"target_user_id": "player_2"},
            ),
            player_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "unauthorized"

    @pytest.mark.anyio
    async def test_mutating_command_denied_when_encounter_session_missing(self, handler, dm_ctx, mgr, monkeypatch):
        original_load = CombatService.load_or_create_encounter_state

        async def _missing_session(self, campaign_id: str):
            return None, EncounterState(id="enc_missing", campaign_id=campaign_id, combatants=[])

        monkeypatch.setattr(
            CombatService, "load_or_create_encounter_state", _missing_session)

        try:
            events = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_missing_session_denied",
                    payload={
                        "actor_id": "fighter_1",
                        "action_type": "action",
                        "action_name": "attack",
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "load_or_create_encounter_state", original_load)

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "encounter_session_required"

    @pytest.mark.anyio
    async def test_dm_delegation_status_and_stop(self, handler, dm_ctx, mgr):
        mgr.register_connection(
            dm_ctx.campaign_id,
            ConnectedUser(user_id="dm_user", display_name="DM",
                          role=UserRole.DM, ws=object()),
        )
        mgr.register_connection(
            dm_ctx.campaign_id,
            ConnectedUser(user_id="player_1", display_name="Player 1",
                          role=UserRole.PLAYER, ws=object()),
        )

        started = await handler.handle(
            WsEnvelope(
                type="delegate_start",
                request_id="req_delegate_status_start",
                payload={"target_user_id": "player_1"},
            ),
            dm_ctx,
            mgr,
        )
        assert len(started) == 1
        assert started[0].type == "delegation_started"

        status = await handler.handle(
            WsEnvelope(type="delegate_status", payload={}),
            dm_ctx,
            mgr,
        )
        assert len(status) == 1
        assert status[0].type == "delegation_status"
        assert status[0].payload["active_delegation"]["target_user_id"] == "player_1"

        stopped = await handler.handle(
            WsEnvelope(type="delegate_stop",
                       request_id="req_delegate_status_stop", payload={}),
            dm_ctx,
            mgr,
        )
        assert len(stopped) == 1
        assert stopped[0].type == "delegation_stopped"

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

@pytest.mark.anyio
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

@pytest.mark.anyio
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

@pytest.mark.anyio
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
        from src.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            db.add(
                Campaign(
                    id="test_campaign_empty",
                    name="Empty Campaign",
                    current_scene="scene.default",
                    active_encounter_id="enc_test_campaign_empty",
                    context_version=1,
                )
            )
            db.add(
                SceneCatalogRecord(
                    campaign_id="test_campaign_empty",
                    scene_id="scene.default",
                    name="Default Scene",
                )
            )
            db.add(
                EncounterCatalogRecord(
                    campaign_id="test_campaign_empty",
                    scene_id="scene.default",
                    encounter_id="enc_test_campaign_empty",
                    name="Empty Encounter",
                    source="test",
                    state_json=EncounterState(
                        id="enc_test_campaign_empty",
                        campaign_id="test_campaign_empty",
                        combatants=[],
                    ).model_dump(mode="json"),
                )
            )
            await db.commit()

            service = CombatService(db)
            session, _ = await service.load_or_create_encounter_state("test_campaign_empty")
            empty_enc = EncounterState(
                id="enc_empty", campaign_id="test_campaign_empty", combatants=[])
            await service.save_full_state(session, empty_enc)
            await db.commit()

        envelope = WsEnvelope(type="start_combat",
                              request_id="req_start_combat_empty")
        ctx = SessionContext(
            campaign_id="test_campaign_empty",
            user_id="dm_user",
            role=UserRole.DM,
            game_system="dnd5e"
        )
        events = await handler.handle(envelope, ctx, mgr)
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

@pytest.mark.anyio
class TestMovement:

    @pytest.mark.anyio
    async def test_request_attack_preview_returns_eligible_targets(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_attack_preview"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [_canonical_candidate("canonical_preview_attack", "Canonical Preview Attack")]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

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
    async def test_request_attack_preview_non_owner_denied(self, handler, player_ctx, mgr, combat_encounter, monkeypatch):
        async def canonical_only(self, actor):
            if actor.id != "goblin_1":
                return []
            return [_canonical_candidate("canonical_goblin_attack", "Canonical Goblin Attack")]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        events = await handler.handle(
            WsEnvelope(
                type="request_attack_preview",
                request_id="req_attack_preview_denied",
                payload={"actor_id": "goblin_1",
                         "action_id": "canonical_goblin_attack"},
            ),
            player_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "unauthorized"

    @pytest.mark.anyio
    async def test_request_attack_preview_unknown_action_id_denied_in_canonical_mode(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_unknown_attack_preview"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [_canonical_candidate("canonical_preview_attack", "Canonical Preview Attack")]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        events = await handler.handle(
            WsEnvelope(
                type="request_attack_preview",
                request_id="req_attack_preview_unknown_action",
                payload={"actor_id": active_actor_id,
                         "action_id": "legacy_attack_name"},
            ),
            dm_ctx,
            mgr,
        )

        assert len(events) == 1
        assert events[0].type == "command_denied"
        assert events[0].payload["reason_code"] == "invalid_action"

    @pytest.mark.anyio
    async def test_request_action_ineligible_target_denied(self, handler, dm_ctx, mgr, combat_encounter):
        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            return [
                {
                    "action_id": "canonical_melee",
                    "name": "Canonical Melee",
                    "label": "Canonical Melee",
                    "family": "attack",
                    "action_type_cost": "action",
                    "targeting_mode": "single_target",
                    "range": 5,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                }
            ]

        setattr(CombatService, "_build_bound_action_candidates", canonical_only)
        try:
            await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_ineligible_target"), dm_ctx, mgr)

            active_actor = combat_encounter.combatants[combat_encounter.active_index]
            target = next(
                c for c in combat_encounter.combatants if c.id != active_actor.id)
            target.position.x = active_actor.position.x + 20
            target.position.y = active_actor.position.y

            from src.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                service = CombatService(db)
                session, _ = await service.load_or_create_encounter_state("test_campaign")
                await service.save_full_state(session, combat_encounter)
                await db.commit()

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
        finally:
            setattr(CombatService, "_build_bound_action_candidates",
                    original_builder)

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "invalid_target"

    @pytest.mark.anyio
    async def test_request_action_aoe_rejects_target_hint_outside_derived_template(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        original_builder = CombatService._build_bound_action_candidates

        async def fake_builder(self, actor):
            return [
                {
                    "action_id": "frost_burst",
                    "name": "Frost Burst",
                    "label": "Frost Burst",
                    "family": "save",
                    "action_type_cost": "action",
                    "targeting_mode": "aoe",
                    "range": 8,
                    "aoe_shape": "cube",
                    "aoe_size": 1,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", fake_builder)

        try:
            await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_for_aoe_hint_check"), dm_ctx, mgr)
            active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
            target_actor = next(
                c for c in combat_encounter.combatants if c.id != active_actor_id)

            events = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_action_aoe_invalid_hint",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "action",
                        "action_name": "frost_burst",
                        "payload": {
                            "template_origin": {
                                "x": int(target_actor.position.x),
                                "y": int(target_actor.position.y),
                            },
                            "target_ids": ["unknown_target_hint"],
                        },
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "target_not_in_template"

    @pytest.mark.anyio
    async def test_request_action_aoe_template_origin_out_of_range_denied(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        original_builder = CombatService._build_bound_action_candidates

        async def fake_builder(self, actor):
            return [
                {
                    "action_id": "burning_cone",
                    "name": "Burning Cone",
                    "label": "Burning Cone",
                    "family": "save",
                    "action_type_cost": "action",
                    "targeting_mode": "aoe",
                    "range": 2,
                    "aoe_shape": "cone",
                    "aoe_size": 3,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", fake_builder)

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
                CombatService, "_build_bound_action_candidates", original_builder)

        assert len(events) == 1
        assert events[0].type == "action_denied"
        assert events[0].payload["reason_code"] == "template_out_of_range"

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
        assert all(str(action.get("action_id") or "").strip()
                   for action in events[0].payload.get("actions", []))
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

        latest = await refresh_encounter()
        goblin = next(
            c for c in latest.combatants if c.id == "goblin_1")
        assert goblin.position.x == 12
        assert goblin.position.y == 14

        goblin_token = next(
            t for t in latest.map.tokens if t.actor_id == "goblin_1")
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
    async def test_dm_can_delegate_to_player_for_move_token(self, handler, dm_ctx, mgr, combat_encounter):
        mgr.register_connection(
            dm_ctx.campaign_id,
            ConnectedUser(user_id="dm_user", display_name="DM",
                          role=UserRole.DM, ws=object()),
        )
        mgr.register_connection(
            dm_ctx.campaign_id,
            ConnectedUser(user_id="player_1", display_name="Player 1",
                          role=UserRole.PLAYER, ws=object()),
        )

        start_events = await handler.handle(
            WsEnvelope(
                type="delegate_start",
                request_id="req_delegate_start_move",
                payload={"target_user_id": "player_1"},
            ),
            dm_ctx,
            mgr,
        )
        assert len(start_events) == 1
        assert start_events[0].type == "delegation_started"

        events = await handler.handle(
            WsEnvelope(
                type="move_token",
                request_id="req_move_delegated_denied",
                payload={
                    "actor_id": "goblin_1",
                    "path": [{"x": 8, "y": 8}],
                },
            ),
            dm_ctx,
            mgr,
        )

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

@pytest.mark.anyio
class TestActionEconomy:

    @pytest.mark.anyio
    async def test_action_budget_exhaustion_in_memory_mode(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_action_economy"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        target_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [_canonical_candidate("canonical_longsword", "Canonical Longsword")]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        first = await handler.handle(
            WsEnvelope(
                type="action",
                request_id="req_action_first",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "attack",
                    "action_name": "canonical_longsword",
                    "target_ids": [target_actor_id],
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
                    "action_name": "canonical_longsword",
                    "target_ids": [target_actor_id],
                },
            ),
            dm_ctx,
            mgr,
        )

        assert len(second) == 1
        assert second[0].type == "action_denied"
        assert second[0].payload["reason_code"] == "action_exhausted"

    @pytest.mark.anyio
    async def test_bonus_action_budget_exhaustion_in_memory_mode(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_bonus_economy"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                _canonical_candidate(
                    "canonical_second_wind",
                    "Canonical Second Wind",
                    family="healing",
                    action_type_cost="bonus_action",
                    targeting_mode="self",
                    range_value=0,
                )
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        first = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_bonus_first",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "bonus",
                    "action_name": "canonical_second_wind",
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
                    "action_name": "canonical_second_wind",
                },
            ),
            dm_ctx,
            mgr,
        )

        assert len(second) == 1
        assert second[0].type == "action_denied"
        assert second[0].payload["reason_code"] == "bonus_action_exhausted"

    @pytest.mark.anyio
    async def test_reaction_budget_exhaustion_in_memory_mode(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_start_reaction_economy"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                _canonical_candidate(
                    "canonical_opportunity_attack",
                    "Canonical Opportunity Attack",
                    family="utility",
                    action_type_cost="reaction",
                )
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        first = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_reaction_first",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "reaction",
                    "action_name": "canonical_opportunity_attack",
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
                    "action_name": "canonical_opportunity_attack",
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

@pytest.mark.anyio
class TestActionResolutionPhase3:

    @pytest.mark.anyio
    async def test_attack_family_publishes_result_and_damage(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_attack_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        target_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [_canonical_candidate("canonical_longsword_strike", "Canonical Longsword Strike")]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        events = await handler.handle(
            WsEnvelope(
                type="action",
                request_id="req_phase3_attack",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "action",
                    "action_name": "canonical_longsword_strike",
                    "target_ids": [target_actor_id],
                },
            ),
            dm_ctx,
            mgr,
        )

        event_types = {event.type for event in events}
        assert "action_authorized" in event_types
        assert "attack_result" in event_types

    @pytest.mark.anyio
    async def test_save_family_publishes_save_result(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_save_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                _canonical_candidate(
                    "canonical_fire_breath",
                    "Canonical Fire Breath",
                    family="save",
                    save_context={"ability": "dexterity", "dc": 18,
                                  "damage_dice": "3d6", "damage_type": "fire"},
                )
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        events = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_phase3_save",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "action",
                    "action_name": "canonical_fire_breath",
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
    async def test_healing_family_publishes_effect_and_heal(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_heal_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                _canonical_candidate(
                    "canonical_second_wind_phase3",
                    "Canonical Second Wind",
                    family="healing",
                    action_type_cost="bonus_action",
                    targeting_mode="self",
                    range_value=0,
                )
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

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
                    "action_name": "canonical_second_wind_phase3",
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
    async def test_utility_family_publishes_effect_and_condition(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_utility_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        target_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                _canonical_candidate(
                    "canonical_trip",
                    "Canonical Trip",
                    family="utility",
                    action_type_cost="reaction",
                )
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

        events = await handler.handle(
            WsEnvelope(
                type="request_action",
                request_id="req_phase3_utility",
                payload={
                    "actor_id": active_actor_id,
                    "action_type": "reaction",
                    "action_name": "canonical_trip",
                    "payload": {
                        "family": "utility",
                        "condition": "Prone",
                        "target_ids": [target_actor_id],
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

    @pytest.mark.anyio
    async def test_request_action_uses_canonical_family_metadata(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase3_canonical_family_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        target_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                {
                    "action_id": "canonical_fire_breath",
                    "name": "Canonical Fire Breath",
                    "label": "Canonical Fire Breath",
                    "family": "save",
                    "action_type_cost": "action",
                    "targeting_mode": "single_target",
                    "range": 30,
                    "save_context": {"ability": "dexterity", "dc": 14, "damage_dice": "2d6", "damage_type": "fire"},
                    "attack_context": None,
                    "effect_intents": [],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                    "aoe_shape": None,
                    "aoe_size": None,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)
        try:
            events = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_phase3_canonical_family",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "action",
                        "action_name": "canonical_fire_breath",
                        "payload": {
                            "target_ids": [target_actor_id],
                            "save_ability": "dexterity",
                            "save_dc": 14,
                            "damage_dice": "2d6",
                            "damage_type": "fire",
                        },
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        event_types = {event.type for event in events}
        assert "action_authorized" in event_types
        assert "save_result" in event_types

    @pytest.mark.anyio
    async def test_request_action_applies_canonical_effect_intent_with_provenance(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase4_effect_apply_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        target_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                {
                    "action_id": "canonical_burning_strike",
                    "name": "Canonical Burning Strike",
                    "label": "Canonical Burning Strike",
                    "family": "utility",
                    "action_type_cost": "action",
                    "targeting_mode": "single_target",
                    "range": 5,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [{"operation": "apply_condition", "condition": "Poisoned"}],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                    "aoe_shape": None,
                    "aoe_size": None,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)
        try:
            events = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_phase4_effect_apply",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "action",
                        "action_name": "canonical_burning_strike",
                        "payload": {"target_ids": [target_actor_id]},
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        applied = [
            event for event in events
            if event.type == "effect_applied" and event.payload.get("effect_id") == "inline:apply_condition:Poisoned"
        ]
        assert applied
        assert applied[0].payload["provenance"]["command_request_id"] == "req_phase4_effect_apply"
        assert applied[0].payload["provenance"]["action_id"] == "canonical_burning_strike"

        event_types = {event.type for event in events}
        assert "condition_added" in event_types

    @pytest.mark.anyio
    async def test_end_turn_emits_effect_tick_and_expiry_events(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_phase4_tick_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id
        target_actor_id = next(
            c.id for c in combat_encounter.combatants if c.id != active_actor_id)

        async with db_module.AsyncSessionLocal() as db:
            service = CombatService(db)
            session, encounter = await service.load_or_create_encounter_state("test_campaign")
            target = next(
                c for c in encounter.combatants if c.id == target_actor_id)
            target.effects.append(
                EffectInstance(
                    id="phase4_tick_effect_1",
                    effect_id="phase4_tick_effect",
                    source_id=active_actor_id,
                    target_id=target_actor_id,
                    duration_type=DurationType.ROUNDS,
                    remaining_rounds=1,
                    tick_intent={"damage": 5}
                )
            )
            await service.sync_effect_instance_records(service.db, session, encounter)
            await service.save_full_state(session, encounter)
            await db.commit()

        end_turn_events = await handler.handle(
            WsEnvelope(
                type="end_turn",
                request_id="req_phase4_tick_end_turn",
                payload={"actor_id": active_actor_id},
            ),
            dm_ctx,
            mgr,
        )

        event_types = [event.type for event in end_turn_events]
        assert "effect_tick_resolved" in event_types
        assert "effect_removed" in event_types
        assert "turn_advanced" in event_types

        tick_event = next(
            event for event in end_turn_events if event.type == "effect_tick_resolved")
        removed_event = next(
            event for event in end_turn_events if event.type == "effect_removed")

        assert tick_event.request_id == "req_phase4_tick_end_turn"
        assert tick_event.payload["provenance"]["command_request_id"] == "req_phase4_tick_end_turn"
        assert tick_event.payload["provenance"]["action_id"] is None

        assert removed_event.request_id == "req_phase4_tick_end_turn"
        assert removed_event.payload["provenance"]["command_request_id"] == "req_phase4_tick_end_turn"
        assert removed_event.payload["provenance"]["action_id"] is None


@pytest.mark.anyio
class TestEffectExecutionPhase4DbMode:

    @staticmethod
    async def _configure_sqlite_db_mode(monkeypatch):
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        monkeypatch.setattr(ws_handler_module,
                            "AsyncSessionLocal", session_factory)
        return session_factory, engine

    @staticmethod
    async def _insert_effect_definition(session_factory, effect_id: str, *, stacking: dict, duration: dict) -> None:
        async with session_factory() as db:
            await db.execute(
                delete(EffectDefinitionRecord).where(
                    EffectDefinitionRecord.system == "dnd5e",
                    EffectDefinitionRecord.effect_id == effect_id,
                )
            )
            db.add(
                EffectDefinitionRecord(
                    system="dnd5e",
                    effect_id=effect_id,
                    name=effect_id,
                    family="utility",
                    duration=duration,
                    stacking=stacking,
                    tags=[],
                    modifiers=[],
                    grants_conditions=[],
                    periodic=[],
                    removal_triggers=[],
                    metadata_json={"source_system": "dnd5e",
                                   "content_version": "1"},
                    enabled=True,
                )
            )
            await db.commit()

    @staticmethod
    async def _seed_campaign_context(session_factory, campaign_id: str) -> None:
        async with session_factory() as db:
            db.add(
                Campaign(
                    id=campaign_id,
                    name=f"Campaign {campaign_id}",
                    current_scene="scene.default",
                    active_encounter_id=f"enc_{campaign_id}",
                    context_version=1,
                )
            )
            db.add(
                SceneCatalogRecord(
                    campaign_id=campaign_id,
                    scene_id="scene.default",
                    name="Default Scene",
                )
            )
            db.add(
                EncounterCatalogRecord(
                    campaign_id=campaign_id,
                    scene_id="scene.default",
                    encounter_id=f"enc_{campaign_id}",
                    name="Seed Encounter",
                    source="test",
                    state_json=EncounterState(
                        id=f"enc_{campaign_id}",
                        campaign_id=campaign_id,
                        combatants=[
                            ActorInstance(
                                id="hero_1",
                                name="Hero",
                                owner_user_id="dm_user",
                                actor_type=ActorType.PLAYER_CHARACTER,
                                current_hp=30,
                                max_hp=30,
                            ),
                            ActorInstance(
                                id="goblin_1",
                                name="Goblin",
                                actor_type=ActorType.MONSTER,
                                current_hp=7,
                                max_hp=7,
                            ),
                        ],
                    ).model_dump(mode="json"),
                )
            )
            await db.commit()

    @staticmethod
    async def _load_effect_rows(session_factory, campaign_id: str) -> list[EffectInstanceRecord]:
        async with session_factory() as db:
            session_stmt = select(EncounterSession).where(
                EncounterSession.campaign_id == campaign_id)
            encounter_session = (await db.execute(session_stmt)).scalar_one()
            rows_stmt = select(EffectInstanceRecord).where(
                EffectInstanceRecord.encounter_session_id == encounter_session.id)
            return list((await db.execute(rows_stmt)).scalars().all())

    @pytest.mark.anyio
    async def test_db_mode_canonical_concentration_replacement_persists_and_emits_provenance(self, handler, mgr, monkeypatch):
        session_factory, engine = await self._configure_sqlite_db_mode(monkeypatch)
        campaign_id = "db_phase4_concentration"
        await self._seed_campaign_context(session_factory, campaign_id)
        dm_ctx = SessionContext(
            campaign_id=campaign_id,
            user_id="dm_user",
            display_name="DM",
            role=UserRole.DM,
            game_system="dnd5e",
        )

        await self._insert_effect_definition(
            session_factory,
            "phase4_focus_a",
            stacking={"mode": "replace"},
            duration={"type": "concentration", "timing": "immediate"},
        )
        await self._insert_effect_definition(
            session_factory,
            "phase4_focus_b",
            stacking={"mode": "replace"},
            duration={"type": "concentration", "timing": "immediate"},
        )

        start = await handler.handle(
            WsEnvelope(type="start_combat", request_id="req_db_focus_start"),
            dm_ctx,
            mgr,
        )
        active_actor_id = start[0].payload["initiative_order"][0]["actor_id"]
        target_actor_id = "goblin_1" if active_actor_id != "goblin_1" else "hero_1"

        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                {
                    "action_id": "canonical_focus_action_a",
                    "name": "Focus A",
                    "label": "Focus A",
                    "family": "utility",
                    "action_type_cost": "free",
                    "targeting_mode": "single_target",
                    "range": 30,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [{"effect_id": "phase4_focus_a"}],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                    "aoe_shape": None,
                    "aoe_size": None,
                },
                {
                    "action_id": "canonical_focus_action_b",
                    "name": "Focus B",
                    "label": "Focus B",
                    "family": "utility",
                    "action_type_cost": "free",
                    "targeting_mode": "single_target",
                    "range": 30,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [{"effect_id": "phase4_focus_b"}],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                    "aoe_shape": None,
                    "aoe_size": None,
                },
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)
        try:
            await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_db_focus_a",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "free",
                        "action_name": "canonical_focus_action_a",
                        "payload": {"target_ids": [target_actor_id]},
                    },
                ),
                dm_ctx,
                mgr,
            )

            second = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_db_focus_b",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "free",
                        "action_name": "canonical_focus_action_b",
                        "payload": {"target_ids": [target_actor_id]},
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        removed = next(
            event for event in second if event.type == "effect_removed")
        reapplied = next(
            event for event in second
            if event.type == "effect_applied" and event.payload.get("effect_id") == "phase4_focus_b"
        )
        assert removed.request_id == "req_db_focus_b"
        assert removed.payload["reason"] == "concentration_replaced"
        assert removed.payload["provenance"]["command_request_id"] == "req_db_focus_b"
        assert removed.payload["provenance"]["action_id"] == "canonical_focus_action_b"

        assert reapplied.request_id == "req_db_focus_b"
        assert reapplied.payload["provenance"]["command_request_id"] == "req_db_focus_b"
        assert reapplied.payload["provenance"]["action_id"] == "canonical_focus_action_b"

        rows = await self._load_effect_rows(session_factory, campaign_id)
        assert len(rows) == 1
        assert rows[0].effect_id == "phase4_focus_b"
        assert rows[0].provenance["command_request_id"] == "req_db_focus_b"
        assert rows[0].provenance["action_id"] == "canonical_focus_action_b"
        await engine.dispose()

    @pytest.mark.anyio
    async def test_db_mode_canonical_stack_limit_denial_emits_provenance_and_keeps_single_row(self, handler, mgr, monkeypatch):
        session_factory, engine = await self._configure_sqlite_db_mode(monkeypatch)
        campaign_id = "db_phase4_stack_limit"
        await self._seed_campaign_context(session_factory, campaign_id)
        dm_ctx = SessionContext(
            campaign_id=campaign_id,
            user_id="dm_user",
            display_name="DM",
            role=UserRole.DM,
            game_system="dnd5e",
        )

        await self._insert_effect_definition(
            session_factory,
            "phase4_stack_once",
            stacking={"mode": "stack", "max_stacks": 1},
            duration={"type": "rounds", "value": 3, "timing": "end_of_turn"},
        )

        start = await handler.handle(
            WsEnvelope(type="start_combat", request_id="req_db_stack_start"),
            dm_ctx,
            mgr,
        )
        active_actor_id = start[0].payload["initiative_order"][0]["actor_id"]
        target_actor_id = "goblin_1" if active_actor_id != "goblin_1" else "hero_1"

        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                {
                    "action_id": "canonical_stack_action",
                    "name": "Stack Action",
                    "label": "Stack Action",
                    "family": "utility",
                    "action_type_cost": "free",
                    "targeting_mode": "single_target",
                    "range": 30,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [{"effect_id": "phase4_stack_once"}],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                    "aoe_shape": None,
                    "aoe_size": None,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)
        try:
            await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_db_stack_apply",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "free",
                        "action_name": "canonical_stack_action",
                        "payload": {"target_ids": [target_actor_id]},
                    },
                ),
                dm_ctx,
                mgr,
            )

            second = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_db_stack_deny",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "free",
                        "action_name": "canonical_stack_action",
                        "payload": {"target_ids": [target_actor_id]},
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        denied = next(event for event in second if event.type ==
                      "effect_denied")
        assert denied.request_id == "req_db_stack_deny"
        assert denied.payload["reason_code"] == "stacking_limit_reached"
        assert denied.payload["provenance"]["command_request_id"] == "req_db_stack_deny"
        assert denied.payload["provenance"]["action_id"] == "canonical_stack_action"

        rows = await self._load_effect_rows(session_factory, campaign_id)
        assert len(rows) == 1
        assert rows[0].effect_id == "phase4_stack_once"
        assert rows[0].stack_count == 1
        await engine.dispose()

    @pytest.mark.anyio
    async def test_db_mode_effect_refresh_emits_provenance(self, handler, mgr, monkeypatch):
        session_factory, engine = await self._configure_sqlite_db_mode(monkeypatch)
        campaign_id = "db_phase4_refresh"
        await self._seed_campaign_context(session_factory, campaign_id)
        dm_ctx = SessionContext(
            campaign_id=campaign_id,
            user_id="dm_user",
            display_name="DM",
            role=UserRole.DM,
            game_system="dnd5e",
        )

        await self._insert_effect_definition(
            session_factory,
            "phase4_refresh_duration",
            stacking={"mode": "refresh_duration"},
            duration={"type": "rounds", "value": 2, "timing": "end_of_turn"},
        )

        start = await handler.handle(
            WsEnvelope(type="start_combat", request_id="req_db_refresh_start"),
            dm_ctx,
            mgr,
        )
        active_actor_id = start[0].payload["initiative_order"][0]["actor_id"]
        target_actor_id = "goblin_1" if active_actor_id != "goblin_1" else "hero_1"

        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                {
                    "action_id": "canonical_refresh_action",
                    "name": "Refresh Action",
                    "label": "Refresh Action",
                    "family": "utility",
                    "action_type_cost": "free",
                    "targeting_mode": "single_target",
                    "range": 30,
                    "save_context": None,
                    "attack_context": None,
                    "effect_intents": [{"effect_id": "phase4_refresh_duration"}],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                    "aoe_shape": None,
                    "aoe_size": None,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)
        try:
            await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_db_refresh_apply",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "free",
                        "action_name": "canonical_refresh_action",
                        "payload": {"target_ids": [target_actor_id]},
                    },
                ),
                dm_ctx,
                mgr,
            )

            second = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_db_refresh_refresh",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "free",
                        "action_name": "canonical_refresh_action",
                        "payload": {"target_ids": [target_actor_id]},
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        refreshed = next(
            event for event in second if event.type == "effect_refreshed")
        assert refreshed.request_id == "req_db_refresh_refresh"
        assert refreshed.payload["provenance"]["command_request_id"] == "req_db_refresh_refresh"
        assert refreshed.payload["provenance"]["action_id"] == "canonical_refresh_action"
        await engine.dispose()

    @pytest.mark.anyio
    async def test_db_mode_aoe_effect_intent_uses_canonical_effect_id_for_derived_targets(self, handler, mgr, monkeypatch):
        session_factory, engine = await self._configure_sqlite_db_mode(monkeypatch)
        campaign_id = "db_phase5_aoe_effect_id"
        await self._seed_campaign_context(session_factory, campaign_id)
        dm_ctx = SessionContext(
            campaign_id=campaign_id,
            user_id="dm_user",
            display_name="DM",
            role=UserRole.DM,
            game_system="dnd5e",
        )

        await self._insert_effect_definition(
            session_factory,
            "phase5_aoe_mark",
            stacking={"mode": "replace"},
            duration={"type": "rounds", "value": 2, "timing": "end_of_turn"},
        )

        start = await handler.handle(
            WsEnvelope(type="start_combat", request_id="req_db_phase5_start"),
            dm_ctx,
            mgr,
        )
        active_actor_id = start[0].payload["initiative_order"][0]["actor_id"]
        target_actor_id = "goblin_1" if active_actor_id != "goblin_1" else "hero_1"
        async with session_factory() as db:
            service = CombatService(db)
            _, runtime_encounter = await service.load_or_create_encounter_state(campaign_id)
        target_actor = next(
            c for c in runtime_encounter.combatants if c.id == target_actor_id)
        template_origin = {
            "x": int(target_actor.position.x),
            "y": int(target_actor.position.y),
        }

        original_builder = CombatService._build_bound_action_candidates

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [
                {
                    "action_id": "canonical_phase5_aoe_mark",
                    "name": "Phase5 Aoe Mark",
                    "label": "Phase5 Aoe Mark",
                    "family": "utility",
                    "action_type_cost": "free",
                    "targeting_mode": "aoe",
                    "range": 30,
                    "save_context": None,
                    "attack_context": {"aoe_shape": "cube", "aoe_size": 1},
                    "effect_intents": [{"effect_id": "phase5_aoe_mark"}],
                    "tags": [],
                    "source_ref": "custom",
                    "content_version": "1",
                    "enabled": True,
                    "aoe_shape": "cube",
                    "aoe_size": 1,
                }
            ]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)
        try:
            events = await handler.handle(
                WsEnvelope(
                    type="request_action",
                    request_id="req_db_phase5_execute",
                    payload={
                        "actor_id": active_actor_id,
                        "action_type": "free",
                        "action_name": "canonical_phase5_aoe_mark",
                        "payload": {
                            "template_origin": template_origin,
                        },
                    },
                ),
                dm_ctx,
                mgr,
            )
        finally:
            monkeypatch.setattr(
                CombatService, "_build_bound_action_candidates", original_builder)

        applied = [
            event for event in events
            if event.type == "effect_applied" and event.payload.get("effect_id") == "phase5_aoe_mark"
        ]
        assert applied
        assert all(event.payload.get("effect_id") ==
                   "phase5_aoe_mark" for event in applied)
        assert any(event.payload.get("target_actor_id") ==
                   target_actor_id for event in applied)

        rows = await self._load_effect_rows(session_factory, campaign_id)
        assert rows
        assert all(row.effect_id == "phase5_aoe_mark" for row in rows)
        await engine.dispose()


# ---------------------------------------------------------------------------
# Actor Spawn Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
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
        refreshed_encounter = await refresh_encounter()
        added_actor = next(
            c for c in refreshed_encounter.combatants if c.id == added_actor_id)
        assert added_actor.position.x == 9
        assert added_actor.position.y == 10

        added_token = next(
            t for t in refreshed_encounter.map.tokens if t.actor_id == added_actor_id)
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

@pytest.mark.anyio
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

        refreshed_encounter = await refresh_encounter()
        assert all(c.id != "goblin_1" for c in refreshed_encounter.combatants)
        assert all(
            t.actor_id != "goblin_1" for t in refreshed_encounter.map.tokens)

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

@pytest.mark.anyio
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

@pytest.mark.anyio
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
        combat_encounter = await refresh_encounter()
        goblin = next(
            c for c in combat_encounter.combatants if c.id == "goblin_1")
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
        combat_encounter = await refresh_encounter()
        goblin = next(
            c for c in combat_encounter.combatants if c.id == "goblin_1")
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

@pytest.mark.anyio
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

@pytest.mark.anyio
class TestCommandTerminalGuaranteesStageE:

    @pytest.mark.anyio
    async def test_preview_commands_emit_terminal_outbound_on_success(self, handler, dm_ctx, mgr, combat_encounter, monkeypatch):
        await handler.handle(WsEnvelope(type="start_combat", request_id="req_stage_e_start"), dm_ctx, mgr)
        active_actor_id = combat_encounter.combatants[combat_encounter.active_index].id

        async def canonical_only(self, actor):
            if actor.id != active_actor_id:
                return []
            return [_canonical_candidate("canonical_stage_e_attack", "Canonical Stage E Attack")]

        monkeypatch.setattr(
            CombatService, "_build_bound_action_candidates", canonical_only)

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
