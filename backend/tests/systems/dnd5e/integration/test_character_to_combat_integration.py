"""
Integration Test Suite 2: Character Builder → Combat Pipeline.

Tests the end-to-end flow from character creation via CharacterBuilder
to participation in an active combat encounter. Verifies that built PCs
have correct stats that interact properly with combat engines.
"""

import pytest

from src.systems.dnd5e.schemas.enums import (
    Ability,
    ActorType,
    DamageType,
    EffectType,
)
from src.systems.dnd5e.schemas.common import AbilityScores, SpeedBlock
from src.systems.dnd5e.schemas.creation import CharacterCreationBlueprint
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.schemas.definitions import ActionDefinition
from src.systems.dnd5e.data.registry import CompendiumRegistry
from src.systems.dnd5e.engine.character_builder import CharacterBuilder
from src.systems.dnd5e.engine.initiative import InitiativeEntry
from src.systems.dnd5e.engine.combat_state import (
    start_combat,
    get_active_combatant,
    get_turn_budget,
    next_turn,
)
from src.systems.dnd5e.engine.action_resolver import resolve_attack, resolve_and_apply
from src.systems.dnd5e.engine.stat_calculator import (
    compute_stats,
    compute_spell_save_dc,
    calculate_modifier,
    calculate_proficiency_bonus,
)

from .conftest import make_goblin, make_melee_attack, make_encounter, start_combat_encounter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_pc(builder: CharacterBuilder, **kwargs) -> "ActorInstance":
    """Build a PC with sensible defaults, overridable by kwargs."""
    defaults = dict(
        name="Test Hero",
        race_slug="human",
        class_slug="fighter",
        background_slug="soldier",
        level=1,
        base_abilities=AbilityScores(
            strength=16, dexterity=14, constitution=14,
            intelligence=10, wisdom=12, charisma=8,
        ),
        chosen_skills=["athletics", "intimidation"],
    )
    defaults.update(kwargs)
    bp = CharacterCreationBlueprint(**defaults)
    return builder.build(bp)


# ---------------------------------------------------------------------------
# Test: Built PC Enters Combat
# ---------------------------------------------------------------------------

class TestBuiltPCInCombat:
    """Verify a CharacterBuilder-built PC works in combat encounters."""

    def test_built_fighter_can_attack_in_combat(self, builder):
        """Build a Fighter → place in encounter → start combat → attack a goblin."""
        fighter = _build_pc(builder, name="Theron", level=1)
        goblin = make_goblin(id="goblin_1", current_hp=15, max_hp=15)

        assert fighter.actor_type == ActorType.PLAYER_CHARACTER
        assert fighter.max_hp == 12  # Human: CON 14+1=15 mod=+2, d10: 10+2=12
        assert fighter.proficiency_bonus == 2

        enc = make_encounter(fighter, goblin)
        start_combat_encounter(enc, [
            (fighter.id, 18, fighter.abilities.dexterity),
            ("goblin_1", 10, 14),
        ])

        assert get_active_combatant(enc).id == fighter.id

        longsword = make_melee_attack(attack_bonus=7, damage_dice="1d8", damage_bonus=4)
        result = resolve_and_apply(enc, fighter, goblin, longsword, roll_override=15)
        assert result.hit is True

        budget = get_turn_budget(enc, fighter.id)
        assert budget.action_available is False

    def test_built_fighter_has_correct_saving_throws(self, builder):
        """Fighter gets STR + CON saving throw proficiencies."""
        fighter = _build_pc(builder, class_slug="fighter")
        assert Ability.STR in fighter.saving_throw_proficiencies
        assert Ability.CON in fighter.saving_throw_proficiencies

    def test_built_fighter_has_correct_skills(self, builder):
        """Fighter with soldier background has expected skills."""
        fighter = _build_pc(
            builder,
            background_slug="soldier",
            chosen_skills=["athletics", "perception"],
        )
        assert "athletics" in fighter.skill_proficiencies
        assert "intimidation" in fighter.skill_proficiencies  # from soldier bg
        assert "perception" in fighter.skill_proficiencies


# ---------------------------------------------------------------------------
# Test: Wizard Spell Save DC Integration
# ---------------------------------------------------------------------------

class TestWizardSpellcasting:
    """Built wizard has correct spell slots and save DC."""

    def test_wizard_level_3_spell_slots(self, builder):
        """Level 3 Wizard: 4 × 1st, 2 × 2nd slots per PHB."""
        wizard = _build_pc(
            builder,
            name="Elara",
            class_slug="wizard",
            level=3,
            base_abilities=AbilityScores(
                strength=8, dexterity=14, constitution=12,
                intelligence=16, wisdom=10, charisma=10,
            ),
        )

        assert wizard.spellcasting is not None
        assert wizard.spellcasting.slots[1].max == 4
        assert wizard.spellcasting.slots[2].max == 2

    def test_wizard_spell_save_dc_matches_stat_calculator(self, builder):
        """Built wizard's save DC matches compute_spell_save_dc()."""
        wizard = _build_pc(
            builder,
            class_slug="wizard",
            level=1,
            base_abilities=AbilityScores(
                strength=8, dexterity=14, constitution=12,
                intelligence=16, wisdom=10, charisma=10,
            ),
        )

        # Human: INT 16 + 1 = 17, mod = +3
        # DC = 8 + prof(2) + mod(3) = 13
        assert wizard.spellcasting.spell_save_dc == 13
        assert wizard.spellcasting.spell_attack_bonus == 5

        # Verify this matches the stat calculator function directly
        dc_from_calc = compute_spell_save_dc(wizard, Ability.INT)
        assert dc_from_calc == wizard.spellcasting.spell_save_dc

    def test_non_caster_has_no_spellcasting(self, builder):
        """Fighter has no spellcasting state."""
        fighter = _build_pc(builder, class_slug="fighter")
        assert fighter.spellcasting is None


# ---------------------------------------------------------------------------
# Test: Level Features Affect Combat Stats
# ---------------------------------------------------------------------------

class TestLevelFeaturesInCombat:
    """Level features from the builder interact with stat computation."""

    def test_stat_calculator_processes_built_effects(self, builder):
        """Effects attached by the builder are processed by compute_stats()."""
        fighter = _build_pc(builder, level=1, base_abilities=AbilityScores(
            strength=16, dexterity=14, constitution=14,
            intelligence=10, wisdom=12, charisma=8,
        ))

        # At level 1 there shouldn't be many effects
        computed = compute_stats(fighter)
        # Human + fighter → AC should be base (10) without armor equipped
        assert computed.armor_class == fighter.armor_class

    def test_proficiency_bonus_scales_with_level(self, builder):
        """Prof bonus from builder matches stat_calculator table."""
        for level, expected_prof in [(1, 2), (5, 3), (9, 4), (17, 6)]:
            pc = _build_pc(builder, level=level)
            assert pc.proficiency_bonus == expected_prof
            assert pc.proficiency_bonus == calculate_proficiency_bonus(level)


# ---------------------------------------------------------------------------
# Test: Racial Bonuses Affect Combat Calculations
# ---------------------------------------------------------------------------

class TestRacialBonusCombatEffect:
    """Race selection affects derived combat stats via ability scores."""

    def test_dwarf_has_higher_hp_than_human(self, builder):
        """Dwarf +2 CON → higher HP than Human with same base stats."""
        base_abilities = AbilityScores(
            strength=16, dexterity=14, constitution=14,
            intelligence=10, wisdom=12, charisma=8,
        )

        human_fighter = _build_pc(
            builder, race_slug="human",
            base_abilities=base_abilities,
        )
        dwarf_fighter = _build_pc(
            builder, race_slug="dwarf",
            base_abilities=base_abilities,
        )

        # Human: CON 14+1=15 mod=+2 → 10+2 = 12 HP
        # Dwarf: CON 14+2=16 mod=+3 → 10+3 = 13 HP
        assert dwarf_fighter.max_hp > human_fighter.max_hp
        assert human_fighter.max_hp == 12
        assert dwarf_fighter.max_hp == 13

    def test_ability_modifiers_from_built_actor(self, builder):
        """calculate_modifier uses the correct final ability scores."""
        wizard = _build_pc(
            builder, class_slug="wizard",
            race_slug="human",
            base_abilities=AbilityScores(
                strength=8, dexterity=14, constitution=12,
                intelligence=16, wisdom=10, charisma=10,
            ),
        )
        # Human: INT 16 + 1 = 17
        assert wizard.abilities.intelligence == 17
        assert calculate_modifier(wizard.abilities.intelligence) == 3
