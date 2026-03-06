"""
Tests for D&D 5e Damage Pipeline.

TDD: Tests written before implementation.
Validates the damage resolution pipeline: immunity → resistance →
vulnerability → temp HP → HP → death detection.
"""

import pytest

from src.systems.dnd5e.schemas.enums import ActorType, DamageType
from src.systems.dnd5e.schemas.instances import ActorInstance
from src.systems.dnd5e.engine.damage import apply_damage


def make_actor(**kwargs) -> ActorInstance:
    defaults = dict(id="test_1", max_hp=30)
    if "current_hp" not in kwargs:
        defaults["current_hp"] = defaults["max_hp"]
    defaults.update(kwargs)
    return ActorInstance(**defaults)


def make_actor_with(
    *,
    damage_immunities: list[str] | None = None,
    damage_resistances: list[str] | None = None,
    damage_vulnerabilities: list[str] | None = None,
    **kwargs,
) -> ActorInstance:
    """Create an actor with damage interaction strings (matching SRD format)."""
    actor = make_actor(**kwargs)
    if damage_immunities:
        actor._damage_immunities_list = damage_immunities
    if damage_resistances:
        actor._damage_resistances_list = damage_resistances
    if damage_vulnerabilities:
        actor._damage_vulnerabilities_list = damage_vulnerabilities
    return actor


# ---------------------------------------------------------------------------
# Immunity
# ---------------------------------------------------------------------------

class TestDamageImmunity:

    def test_immunity_negates_damage(self):
        result = apply_damage(
            make_actor(current_hp=30),
            amount=63,
            damage_type=DamageType.FIRE,
            damage_immunities=[DamageType.FIRE],
        )
        assert result.damage_dealt == 0
        assert result.remaining_hp == 30

    def test_non_immune_type_takes_full_damage(self):
        result = apply_damage(
            make_actor(current_hp=30),
            amount=10,
            damage_type=DamageType.SLASHING,
            damage_immunities=[DamageType.FIRE],
        )
        assert result.damage_dealt == 10


# ---------------------------------------------------------------------------
# Resistance
# ---------------------------------------------------------------------------

class TestDamageResistance:

    def test_resistance_halves_damage(self):
        result = apply_damage(
            make_actor(current_hp=30),
            amount=20,
            damage_type=DamageType.FIRE,
            damage_resistances=[DamageType.FIRE],
        )
        assert result.damage_dealt == 10

    def test_resistance_rounds_down(self):
        """Odd damage halved rounds down: 15 → 7."""
        result = apply_damage(
            make_actor(current_hp=30),
            amount=15,
            damage_type=DamageType.FIRE,
            damage_resistances=[DamageType.FIRE],
        )
        assert result.damage_dealt == 7


# ---------------------------------------------------------------------------
# Vulnerability
# ---------------------------------------------------------------------------

class TestDamageVulnerability:

    def test_vulnerability_doubles_damage(self):
        result = apply_damage(
            make_actor(current_hp=50, max_hp=50),
            amount=20,
            damage_type=DamageType.FIRE,
            damage_vulnerabilities=[DamageType.FIRE],
        )
        assert result.damage_dealt == 40


# ---------------------------------------------------------------------------
# Temp HP
# ---------------------------------------------------------------------------

class TestTempHP:

    def test_temp_hp_absorbs_first(self):
        actor = make_actor(current_hp=30, temp_hp=10)
        result = apply_damage(actor, amount=15, damage_type=DamageType.SLASHING)
        assert result.damage_absorbed_by_temp == 10
        assert result.remaining_hp == 25  # 15 - 10 temp = 5 to real HP → 30 - 5 = 25
        assert result.remaining_temp_hp == 0

    def test_temp_hp_fully_absorbs_small_hit(self):
        actor = make_actor(current_hp=30, temp_hp=20)
        result = apply_damage(actor, amount=10, damage_type=DamageType.SLASHING)
        assert result.damage_absorbed_by_temp == 10
        assert result.remaining_hp == 30
        assert result.remaining_temp_hp == 10


# ---------------------------------------------------------------------------
# Death Detection
# ---------------------------------------------------------------------------

class TestDeathDetection:

    def test_monster_dies_at_zero_hp(self):
        actor = make_actor(
            current_hp=5,
            actor_type=ActorType.MONSTER,
        )
        result = apply_damage(actor, amount=20, damage_type=DamageType.SLASHING)
        assert result.is_dead is True
        assert result.remaining_hp == 0

    def test_pc_falls_unconscious_not_dead(self):
        """PCs don't die outright at 0 HP (death saves happen separately)."""
        actor = make_actor(
            current_hp=5,
            actor_type=ActorType.PLAYER_CHARACTER,
        )
        result = apply_damage(actor, amount=20, damage_type=DamageType.SLASHING)
        assert result.is_dead is False
        assert result.is_unconscious is True
        assert result.remaining_hp == 0

    def test_hp_does_not_go_below_zero(self):
        actor = make_actor(current_hp=5)
        result = apply_damage(actor, amount=100, damage_type=DamageType.SLASHING)
        assert result.remaining_hp == 0


# ---------------------------------------------------------------------------
# Combined Pipeline
# ---------------------------------------------------------------------------

class TestDamagePipeline:

    def test_immunity_beats_resistance(self):
        """If immune, resistance doesn't matter."""
        result = apply_damage(
            make_actor(current_hp=30),
            amount=20,
            damage_type=DamageType.FIRE,
            damage_immunities=[DamageType.FIRE],
            damage_resistances=[DamageType.FIRE],
        )
        assert result.damage_dealt == 0

    def test_full_pipeline_resistance_then_temp_hp(self):
        """Resistance halves, then temp HP absorbs remainder."""
        actor = make_actor(current_hp=30, temp_hp=5)
        result = apply_damage(
            actor,
            amount=20,
            damage_type=DamageType.FIRE,
            damage_resistances=[DamageType.FIRE],
        )
        # 20 → 10 (resistance) → 5 absorbed by temp, 5 to HP → 25 remaining
        assert result.damage_dealt == 10
        assert result.damage_absorbed_by_temp == 5
        assert result.remaining_hp == 25
