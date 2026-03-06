"""
Tests for D&D 5e state filter (fog of war).
"""

from src.core.sessions.models import SessionContext, UserRole
from src.systems.dnd5e.state_filter import filter_state_for_role, _health_descriptor
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.schemas.instances import ActorInstance
from src.systems.dnd5e.schemas.enums import ActorType
from src.systems.dnd5e.schemas.common import AbilityScores


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_encounter() -> EncounterState:
    return EncounterState(
        id="enc_1",
        campaign_id="c1",
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
            ActorInstance(
                id="dragon_1",
                name="Young Red Dragon",
                actor_type=ActorType.MONSTER,
                current_hp=80,
                max_hp=178,
                armor_class=18,
                abilities=AbilityScores(strength=23, dexterity=10, constitution=21,
                                        intelligence=14, wisdom=11, charisma=19),
            ),
        ],
    )


def _dm_ctx() -> SessionContext:
    return SessionContext(campaign_id="c1", user_id="dm_1", role=UserRole.DM)


def _player_ctx() -> SessionContext:
    return SessionContext(campaign_id="c1", user_id="player_1", role=UserRole.PLAYER)


# ---------------------------------------------------------------------------
# Health descriptor tests
# ---------------------------------------------------------------------------

class TestHealthDescriptor:

    def test_healthy(self):
        assert _health_descriptor(45, 45) == "healthy"

    def test_lightly_wounded(self):
        assert _health_descriptor(36, 45) == "lightly wounded"

    def test_bloodied(self):
        assert _health_descriptor(25, 45) == "bloodied"

    def test_badly_wounded(self):
        assert _health_descriptor(12, 45) == "badly wounded"  # 12/45 ≈ 0.267

    def test_near_death(self):
        assert _health_descriptor(2, 45) == "near death"

    def test_dead(self):
        assert _health_descriptor(0, 45) == "dead"


# ---------------------------------------------------------------------------
# DM view tests
# ---------------------------------------------------------------------------

class TestDmView:

    def test_dm_sees_full_state(self):
        enc = _make_encounter()
        data = filter_state_for_role(enc, _dm_ctx())

        # DM sees all combatants with full stats
        combatants = data["combatants"]
        assert len(combatants) == 3

        goblin = next(c for c in combatants if c["id"] == "goblin_1")
        assert goblin["current_hp"] == 7
        assert goblin["max_hp"] == 7
        assert "abilities" in goblin


# ---------------------------------------------------------------------------
# Player view tests
# ---------------------------------------------------------------------------

class TestPlayerView:

    def test_player_sees_health_descriptor_not_hp(self):
        enc = _make_encounter()
        data = filter_state_for_role(enc, _player_ctx())

        goblin = next(c for c in data["combatants"] if c["id"] == "goblin_1")
        assert "current_hp" not in goblin
        assert "max_hp" not in goblin
        assert "temp_hp" not in goblin
        assert goblin["health_status"] == "healthy"

    def test_player_sees_own_pc_full_stats(self):
        enc = _make_encounter()
        data = filter_state_for_role(enc, _player_ctx())

        fighter = next(c for c in data["combatants"] if c["id"] == "fighter_1")
        # PCs keep their HP visible
        assert fighter["current_hp"] == 45
        assert fighter["max_hp"] == 45

    def test_player_monster_has_no_abilities(self):
        enc = _make_encounter()
        data = filter_state_for_role(enc, _player_ctx())

        dragon = next(c for c in data["combatants"] if c["id"] == "dragon_1")
        assert "abilities" not in dragon

    def test_player_monster_bloodied_hp(self):
        enc = _make_encounter()
        data = filter_state_for_role(enc, _player_ctx())

        dragon = next(c for c in data["combatants"] if c["id"] == "dragon_1")
        # 80/178 ≈ 0.449 → below 0.50 bloodied, above 0.25 → badly wounded
        assert dragon["health_status"] == "badly wounded"
