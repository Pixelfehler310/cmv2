"""
Integration Test Suite 1: Combat Round Cross-Module Integration.

Tests that chain Phase 2 (stateless rules) + Phase 3 (combat state) +
Phase 4 (action resolver) engines together in realistic combat scenarios.

All tests use deterministic roll overrides — no randomness.
"""

import pytest

from src.systems.dnd5e.schemas.enums import (
    Ability,
    ActionType,
    ActorType,
    ConditionType,
    DamageType,
    DurationType,
    EffectType,
)
from src.systems.dnd5e.schemas.common import AbilityScores, SaveRequirement, SpeedBlock
from src.systems.dnd5e.schemas.instances import (
    ActorInstance,
    ConditionInstance,
    ConcentrationState,
    EffectInstance,
)
from src.systems.dnd5e.schemas.definitions import ActionDefinition
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.engine.initiative import InitiativeEntry
from src.systems.dnd5e.engine.combat_state import (
    start_combat,
    get_active_combatant,
    get_turn_budget,
    next_turn,
)
from src.systems.dnd5e.engine.action_resolver import (
    resolve_attack,
    resolve_save_action,
    resolve_healing,
    resolve_and_apply,
)
from src.systems.dnd5e.engine.damage import apply_damage, DamageResult
from src.systems.dnd5e.engine.effect_engine import (
    add_effect,
    remove_effect,
    has_effect,
    tick_effects,
)
from src.systems.dnd5e.engine.concentration import (
    concentration_dc,
    break_concentration,
    start_concentration,
    check_incapacitated_breaks_concentration,
)
from src.systems.dnd5e.engine.condition_engine import (
    apply_conditions,
    compute_attack_context,
    compute_save_context,
)
from src.systems.dnd5e.engine.stat_calculator import (
    compute_stats,
    compute_spell_save_dc,
    calculate_modifier,
)

from .conftest import (
    make_fighter,
    make_wizard,
    make_goblin,
    make_dragon,
    make_melee_attack,
    make_fire_breath,
    make_healing_action,
    make_encounter,
    start_combat_encounter,
)


# ---------------------------------------------------------------------------
# Test: Full Combat Round with Attacks
# ---------------------------------------------------------------------------

class TestFullCombatRound:
    """Start combat → each combatant attacks → verify HP, budget, round advancement."""

    def test_full_round_with_attacks(self):
        """Fighter attacks goblin, goblin attacks fighter, round advances."""
        fighter = make_fighter()
        goblin = make_goblin(id="goblin_1", current_hp=15, max_hp=15)
        enc = make_encounter(fighter, goblin)

        start_combat_encounter(enc, [
            ("fighter_1", 18, 14),  # Fighter goes first
            ("goblin_1", 12, 14),
        ])

        # Round 1: Fighter's turn
        assert get_active_combatant(enc).id == "fighter_1"
        assert enc.round_number == 1

        longsword = make_melee_attack(attack_bonus=7, damage_dice="1d8", damage_bonus=4)
        result = resolve_and_apply(enc, fighter, goblin, longsword, roll_override=15)
        # 15 + 7 = 22 vs AC 15 → hit
        assert result.hit is True
        assert goblin.current_hp < 15  # took some damage

        budget = get_turn_budget(enc, "fighter_1")
        assert budget.action_available is False  # consumed

        # Advance to goblin's turn
        next_turn(enc)
        assert get_active_combatant(enc).id == "goblin_1"

        scimitar = make_melee_attack(
            name="Scimitar", attack_bonus=4, damage_dice="1d6",
            damage_bonus=2, damage_type=DamageType.SLASHING,
        )
        result2 = resolve_and_apply(enc, goblin, fighter, scimitar, roll_override=16)
        # 16 + 4 = 20 vs AC 18 → hit
        assert result2.hit is True

        goblin_budget = get_turn_budget(enc, "goblin_1")
        assert goblin_budget.action_available is False

        # Advance to next round
        next_turn(enc)
        assert enc.round_number == 2
        assert get_active_combatant(enc).id == "fighter_1"

        # Fighter's budget should be reset
        new_budget = get_turn_budget(enc, "fighter_1")
        assert new_budget.action_available is True

    def test_miss_does_not_deal_damage(self):
        """Attack that misses leaves target HP unchanged."""
        fighter = make_fighter()
        goblin = make_goblin()
        enc = make_encounter(fighter, goblin)
        start_combat_encounter(enc, [("fighter_1", 20, 14), ("goblin_1", 5, 14)])

        action = make_melee_attack(attack_bonus=7)
        result = resolve_and_apply(enc, fighter, goblin, action, roll_override=3)
        # 3 + 7 = 10 vs AC 15 → miss
        assert result.hit is False
        assert goblin.current_hp == 7  # unchanged


# ---------------------------------------------------------------------------
# Test: Damage + Concentration Save Integration
# ---------------------------------------------------------------------------

class TestConcentrationIntegration:
    """Damage → concentration DC → break/keep based on save."""

    def test_damage_triggers_concentration_dc_calculation(self):
        """Verify concentration_dc uses max(10, damage/2) from Phase 3."""
        assert concentration_dc(damage=8) == 10   # floor(8/2) = 4, max(10,4) = 10
        assert concentration_dc(damage=30) == 15  # floor(30/2) = 15

    def test_damage_breaks_concentration_via_full_pipeline(self):
        """Wizard concentrating on Bless → takes damage → effect removed from encounter."""
        wizard = make_wizard()
        goblin = make_goblin()
        enc = make_encounter(wizard, goblin)

        # Wizard concentrates on Bless
        bless_effect = EffectInstance(
            id="bless_1",
            name="Bless",
            source_id="wizard_1",
            target_id="fighter_1",  # targeting someone else
            type=EffectType.BONUS,
            target_stat="attack_bonus",
            value=4,
            duration_type=DurationType.ROUNDS,
            remaining_rounds=10,
            requires_concentration=True,
        )
        start_concentration(wizard, bless_effect, enc)

        assert wizard.concentration.is_concentrating is True
        assert wizard.concentration.effect_id == "bless_1"

        # Damage the wizard (simulating a hit)
        dmg_result = apply_damage(
            wizard, amount=20, damage_type=DamageType.SLASHING,
        )
        assert dmg_result.damage_dealt == 20

        # DC = max(10, 20/2) = 10
        dc = concentration_dc(damage=20)
        assert dc == 10

        # Wizard fails the save — break concentration
        break_concentration(wizard, enc)
        assert wizard.concentration.is_concentrating is False
        assert wizard.concentration.effect_id is None

    def test_incapacitating_condition_breaks_concentration(self):
        """Stunning a concentrating wizard auto-breaks concentration."""
        wizard = make_wizard()
        goblin = make_goblin()
        enc = make_encounter(wizard, goblin)

        # Concentrate on Hold Person
        hold_effect = EffectInstance(
            id="hold_1",
            name="Hold Person",
            source_id="wizard_1",
            target_id="goblin_1",
            type=EffectType.GRANT_CONDITION,
            duration_type=DurationType.ROUNDS,
            remaining_rounds=10,
            requires_concentration=True,
        )
        start_concentration(wizard, hold_effect, enc)
        assert wizard.concentration.is_concentrating is True

        # Apply Stunned condition to wizard
        wizard.conditions.append(ConditionInstance(condition=ConditionType.STUNNED))
        check_incapacitated_breaks_concentration(wizard, enc)

        assert wizard.concentration.is_concentrating is False

    def test_new_concentration_replaces_old(self):
        """Casting a new concentration spell drops the previous one."""
        wizard = make_wizard()
        fighter = make_fighter()
        goblin = make_goblin()
        enc = make_encounter(wizard, fighter, goblin)

        # First: Bless
        bless = EffectInstance(
            id="bless_1", name="Bless", source_id="wizard_1",
            target_id="fighter_1", type=EffectType.BONUS,
            target_stat="attack_bonus", value=4,
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        start_concentration(wizard, bless, enc)
        assert has_effect(fighter, "bless_1")

        # Second: Hold Person (replaces Bless)
        hold = EffectInstance(
            id="hold_1", name="Hold Person", source_id="wizard_1",
            target_id="goblin_1", type=EffectType.GRANT_CONDITION,
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        start_concentration(wizard, hold, enc)

        # Bless should be gone, Hold Person active
        assert not has_effect(fighter, "bless_1")
        assert has_effect(goblin, "hold_1")
        assert wizard.concentration.effect_id == "hold_1"


# ---------------------------------------------------------------------------
# Test: Conditions Affect Attack Resolution
# ---------------------------------------------------------------------------

class TestConditionCombatIntegration:
    """Conditions from Phase 2 interact with Phase 4 attack resolution."""

    def test_blinded_attacker_gets_disadvantage_in_combat(self):
        """Blinded condition → attack resolver uses disadvantage."""
        fighter = make_fighter()
        goblin = make_goblin()

        # Blind the fighter
        fighter.conditions.append(ConditionInstance(condition=ConditionType.BLINDED))

        # Verify condition engine detects it
        atk_ctx = compute_attack_context(fighter)
        assert atk_ctx.has_disadvantage is True

        # Attack with disadvantage — resolver should pick lower roll
        action = make_melee_attack(attack_bonus=7)
        result = resolve_attack(
            fighter, goblin, action,
            roll_overrides=[18, 5],  # disadvantage takes 5
        )
        assert result.roll_used == 5
        # 5 + 7 = 12 vs AC 15 → miss
        assert result.hit is False

    def test_invisible_attacker_gets_advantage(self):
        """Invisible condition → advantage on attacks."""
        fighter = make_fighter()
        fighter.conditions.append(ConditionInstance(condition=ConditionType.INVISIBLE))
        goblin = make_goblin()

        atk_ctx = compute_attack_context(fighter)
        assert atk_ctx.has_advantage is True

        action = make_melee_attack(attack_bonus=7)
        result = resolve_attack(
            fighter, goblin, action,
            advantage=True, roll_overrides=[5, 18],
        )
        assert result.roll_used == 18  # advantage takes higher
        # 18 + 7 = 25 vs AC 15 → hit
        assert result.hit is True

    def test_paralyzed_target_auto_crits_with_melee(self):
        """Paralyzed + melee hit = automatic critical hit."""
        fighter = make_fighter()
        goblin = make_goblin(current_hp=50, max_hp=50)
        goblin.conditions.append(ConditionInstance(condition=ConditionType.PARALYZED))

        action = make_melee_attack(attack_bonus=7, damage_dice="1d8", damage_bonus=4)
        result = resolve_attack(fighter, goblin, action, roll_override=10)
        # Any hit against paralyzed in melee is auto-crit
        assert result.hit is True
        assert result.is_critical is True

    def test_exhaustion_3_gives_disadvantage_on_attacks_and_saves(self):
        """Exhaustion level 3+ → disadvantage on attacks AND saves."""
        fighter = make_fighter(exhaustion_level=3)

        atk_ctx = compute_attack_context(fighter)
        assert atk_ctx.has_disadvantage is True

        save_ctx = compute_save_context(fighter, Ability.DEX)
        assert save_ctx.has_disadvantage is True


# ---------------------------------------------------------------------------
# Test: Effect Duration Ticking Across Turns
# ---------------------------------------------------------------------------

class TestEffectDurationIntegration:
    """Effects tick down during turn cycling and auto-expire."""

    def test_effect_expires_after_duration(self):
        """A 2-round effect ticks down and is removed after 2 turns by source."""
        fighter = make_fighter()
        goblin = make_goblin()
        enc = make_encounter(fighter, goblin)
        start_combat_encounter(enc, [
            ("fighter_1", 18, 14),
            ("goblin_1", 10, 14),
        ])

        # Fighter casts a 2-round effect on goblin
        slow_effect = EffectInstance(
            id="slow_1", name="Slow", source_id="fighter_1",
            target_id="goblin_1", type=EffectType.BONUS,
            target_stat="speed_walk", value=-15,
            duration_type=DurationType.ROUNDS, remaining_rounds=2,
        )
        add_effect(enc, slow_effect)
        assert has_effect(goblin, "slow_1")

        # Tick at end of fighter's turn (source_id = fighter_1)
        tick_effects(enc, source_id="fighter_1")
        assert goblin.effects[0].remaining_rounds == 1

        # Next round: tick again
        next_turn(enc)  # goblin's turn
        next_turn(enc)  # fighter's turn (round 2)
        tick_effects(enc, source_id="fighter_1")

        # Effect should be expired and removed
        assert not has_effect(goblin, "slow_1")

    def test_effect_removal_cleans_linked_conditions(self):
        """When an effect expires, its linked conditions are also removed."""
        fighter = make_fighter()
        goblin = make_goblin()
        enc = make_encounter(fighter, goblin)

        # Effect that grants a condition
        stun_effect = EffectInstance(
            id="stun_spell_1", name="Stunning Strike",
            source_id="fighter_1", target_id="goblin_1",
            type=EffectType.GRANT_CONDITION,
            duration_type=DurationType.ROUNDS, remaining_rounds=1,
        )
        add_effect(enc, stun_effect)
        # Add the linked condition
        goblin.conditions.append(ConditionInstance(
            condition=ConditionType.STUNNED,
            source_effect_id="stun_spell_1",
        ))

        assert any(c.condition == ConditionType.STUNNED for c in goblin.conditions)

        # Tick → expires → condition should also be removed
        tick_effects(enc, source_id="fighter_1")

        assert not has_effect(goblin, "stun_spell_1")
        assert not any(c.condition == ConditionType.STUNNED for c in goblin.conditions)


# ---------------------------------------------------------------------------
# Test: Multi-Target Save Action with Damage Pipeline
# ---------------------------------------------------------------------------

class TestSaveActionDamagePipeline:
    """Save-based actions compose with the damage pipeline."""

    def test_save_with_immunity_and_resistance(self):
        """Fire Breath on targets with different defenses."""
        dragon = make_dragon()
        # Target A: normal (fails save → full damage)
        target_a = make_fighter(id="target_a", current_hp=100, max_hp=100)
        # Target B: normal (passes save → half damage)
        target_b = make_goblin(id="target_b", current_hp=100, max_hp=100)

        fire_breath = make_fire_breath(
            save=SaveRequirement(ability=Ability.DEX, dc=17,
                                 on_fail="full_damage", on_success="half_damage"),
        )

        result = resolve_save_action(
            dragon, [target_a, target_b], fire_breath,
            damage_roll_override=56,
            save_overrides=[8, 22],  # A fails (8 < 17), B passes (22 >= 17)
        )

        assert result.results[0].passed is False
        assert result.results[0].damage == 56  # full damage

        assert result.results[1].passed is True
        assert result.results[1].damage == 28  # floor(56/2) = 28

    def test_fire_damage_with_resistance_through_full_pipeline(self):
        """Apply fire damage to a fire-resistant actor through the damage pipeline."""
        target = make_fighter(current_hp=100, max_hp=100)

        dmg_result = apply_damage(
            target, amount=40, damage_type=DamageType.FIRE,
            damage_resistances=[DamageType.FIRE],
        )
        assert dmg_result.damage_dealt == 20  # halved
        target.current_hp = dmg_result.remaining_hp
        assert target.current_hp == 80

    def test_fire_damage_with_immunity(self):
        """Fire immune target takes zero damage."""
        target = make_dragon(current_hp=178, max_hp=178)

        dmg_result = apply_damage(
            target, amount=63, damage_type=DamageType.FIRE,
            damage_immunities=[DamageType.FIRE],
        )
        assert dmg_result.damage_dealt == 0
        assert target.current_hp == 178


# ---------------------------------------------------------------------------
# Test: Lethal Damage — Monster vs PC
# ---------------------------------------------------------------------------

class TestLethalDamage:
    """Same damage produces different outcomes for monsters vs PCs."""

    def test_monster_dies_at_zero_hp(self):
        """Monster drops to 0 HP → is_dead = True."""
        goblin = make_goblin(current_hp=5)
        result = apply_damage(
            goblin, amount=20, damage_type=DamageType.SLASHING,
        )
        assert result.is_dead is True
        assert result.remaining_hp == 0
        goblin.current_hp = result.remaining_hp
        assert goblin.current_hp == 0

    def test_pc_goes_unconscious_at_zero_hp(self):
        """PC drops to 0 HP → is_unconscious = True, NOT dead."""
        fighter = make_fighter(current_hp=5)
        result = apply_damage(
            fighter, amount=20, damage_type=DamageType.SLASHING,
        )
        assert result.is_dead is False
        assert result.is_unconscious is True
        assert result.remaining_hp == 0

    def test_temp_hp_absorbs_before_real_hp(self):
        """Temp HP absorbs first; remaining goes to real HP."""
        fighter = make_fighter(current_hp=30, max_hp=30, temp_hp=10)
        result = apply_damage(
            fighter, amount=15, damage_type=DamageType.SLASHING,
        )
        # 10 temp absorbs → 5 to real HP
        assert result.damage_absorbed_by_temp == 10
        assert result.remaining_temp_hp == 0
        assert result.remaining_hp == 25
        fighter.temp_hp = result.remaining_temp_hp
        fighter.current_hp = result.remaining_hp
        assert fighter.current_hp == 25


# ---------------------------------------------------------------------------
# Test: Healing After Damage in Same Round
# ---------------------------------------------------------------------------

class TestHealingIntegration:
    """Damage then heal in the same context — verify HP consistency."""

    def test_damage_then_heal(self):
        """Damage a PC, then heal in the same round."""
        fighter = make_fighter(current_hp=45, max_hp=45)
        enc = make_encounter(fighter, make_goblin())
        start_combat_encounter(enc)

        # Take damage
        dmg_result = apply_damage(fighter, amount=20, damage_type=DamageType.SLASHING)
        fighter.current_hp = dmg_result.remaining_hp
        assert fighter.current_hp == 25

        # Heal
        heal_action = make_healing_action(damage_dice="1d8", damage_bonus=3)
        heal_result = resolve_healing(fighter, heal_action, dice_override=5)
        # 5 + 3 = 8 healed → 25 + 8 = 33
        assert fighter.current_hp == 33
        assert heal_result.hp_restored == 8

    def test_healing_capped_at_max_hp(self):
        """Healing cannot exceed max HP."""
        fighter = make_fighter(current_hp=43, max_hp=45)
        heal_action = make_healing_action(damage_dice="1d8", damage_bonus=3)
        result = resolve_healing(fighter, heal_action, dice_override=8)
        # Would heal 11, but capped at 45
        assert fighter.current_hp == 45
        assert result.hp_restored == 2  # only 2 needed

    def test_stat_effects_computed_correctly_with_effects(self):
        """Verify stat calculator processes effects on actors correctly."""
        fighter = make_fighter(armor_class=15)
        # Shield of Faith: +2 AC bonus
        fighter.effects.append(EffectInstance(
            id="shield_faith_1", name="Shield of Faith",
            source_id="cleric_1", target_id="fighter_1",
            type=EffectType.BONUS, target_stat="armor_class", value=2,
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
        ))

        computed = compute_stats(fighter)
        assert computed.armor_class == 17  # 15 + 2
