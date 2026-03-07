"""
Phase 5 — Character Builder Tests (TDD).

Tests for assembling PCs from race + class + background definitions.
All tests use in-memory fixtures registered in a CompendiumRegistry.
"""

import pytest

from src.systems.dnd5e.schemas.enums import (
    Ability,
    ActorType,
    EffectType,
)
from src.systems.dnd5e.schemas.common import (
    AbilityScores,
    AbilityScoreBonus,
    LevelFeature,
    EffectDefinition,
    SkillChoice,
    SpeedBlock,
    SpellcastingProgression,
    SpellSlots,
)
from src.systems.dnd5e.schemas.definitions import (
    BackgroundDefinition,
    ClassDefinition,
    RaceDefinition,
)
from src.systems.dnd5e.schemas.creation import CharacterCreationBlueprint
from src.systems.dnd5e.data.registry import CompendiumLookupError, CompendiumRegistry
from src.systems.dnd5e.engine.character_builder import CharacterBuilder


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

def _make_registry() -> CompendiumRegistry:
    """Build a registry with a handful of test definitions."""
    reg = CompendiumRegistry()

    # --- Races ---
    reg.register_race(RaceDefinition(
        slug="human",
        name="Human",
        speed=SpeedBlock(walk=30),
        ability_bonuses=[
            AbilityScoreBonus(ability=Ability.STR, bonus=1),
            AbilityScoreBonus(ability=Ability.DEX, bonus=1),
            AbilityScoreBonus(ability=Ability.CON, bonus=1),
            AbilityScoreBonus(ability=Ability.INT, bonus=1),
            AbilityScoreBonus(ability=Ability.WIS, bonus=1),
            AbilityScoreBonus(ability=Ability.CHA, bonus=1),
        ],
        languages=["Common", "one extra"],
    ))

    reg.register_race(RaceDefinition(
        slug="dwarf",
        name="Dwarf",
        speed=SpeedBlock(walk=25),
        ability_bonuses=[
            AbilityScoreBonus(ability=Ability.CON, bonus=2),
        ],
        languages=["Common", "Dwarvish"],
    ))

    # --- Classes ---
    reg.register_class(ClassDefinition(
        slug="fighter",
        name="Fighter",
        hit_die="d10",
        saving_throw_proficiencies=[Ability.STR, Ability.CON],
        armor_proficiencies=["light", "medium", "heavy", "shield"],
        weapon_proficiencies=["simple", "martial"],
        skill_choices=SkillChoice(
            options=["acrobatics", "animal_handling", "athletics",
                     "history", "insight", "intimidation",
                     "perception", "survival"],
            choose=2,
        ),
        level_features=[
            LevelFeature(
                level=1,
                feature_slug="fighting-style",
                effects=[],
            ),
            LevelFeature(
                level=1,
                feature_slug="second-wind",
                effects=[],
            ),
            LevelFeature(
                level=5,
                feature_slug="extra-attack",
                effects=[
                    EffectDefinition(
                        name="Extra Attack",
                        type=EffectType.BONUS,
                        target_stat="attacks_per_action",
                        value=1,
                    ),
                ],
            ),
        ],
    ))

    reg.register_class(ClassDefinition(
        slug="wizard",
        name="Wizard",
        hit_die="d6",
        saving_throw_proficiencies=[Ability.INT, Ability.WIS],
        weapon_proficiencies=["daggers", "darts", "slings", "quarterstaffs", "light_crossbows"],
        skill_choices=SkillChoice(
            options=["arcana", "history", "insight", "investigation",
                     "medicine", "religion"],
            choose=2,
        ),
        spellcasting=SpellcastingProgression(
            ability=Ability.INT,
            type="full",
            cantrips_known_at_1=3,
        ),
    ))

    # --- Backgrounds ---
    reg.register_background(BackgroundDefinition(
        slug="soldier",
        name="Soldier",
        skill_proficiencies=["athletics", "intimidation"],
    ))

    reg.register_background(BackgroundDefinition(
        slug="acolyte",
        name="Acolyte",
        skill_proficiencies=["insight", "religion"],
    ))

    return reg


def _make_builder(registry: CompendiumRegistry | None = None) -> CharacterBuilder:
    return CharacterBuilder(registry or _make_registry())


def _make_blueprint(**kwargs) -> CharacterCreationBlueprint:
    defaults = dict(
        name="Test Character",
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
    return CharacterCreationBlueprint(**defaults)


def _build(blueprint: CharacterCreationBlueprint | None = None, **kwargs) -> "ActorInstance":
    """Convenience: build with defaults, override with kwargs."""
    bp = blueprint or _make_blueprint(**kwargs)
    return _make_builder().build(bp)


# ---------------------------------------------------------------------------
# Test: Full Build Pipeline
# ---------------------------------------------------------------------------

class TestBuildPipeline:

    def test_build_level_1_fighter(self):
        """Full pipeline: human fighter, level 1 → valid ActorInstance."""
        blueprint = CharacterCreationBlueprint(
            name="Theron",
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
        actor = _make_builder().build(blueprint)

        assert actor.name == "Theron"
        assert actor.actor_type == ActorType.PLAYER_CHARACTER
        # Human: +1 to all → CON becomes 15, mod = +2
        # Fighter d10: max 10 + CON mod 2 = 12
        assert actor.max_hp == 12
        assert actor.current_hp == 12
        assert actor.proficiency_bonus == 2

    def test_build_level_1_fighter_hp_with_racial_con_bonus(self):
        """Dwarf fighter: +2 CON affects HP calculation."""
        blueprint = _make_blueprint(
            name="Bruenor",
            race_slug="dwarf",
            class_slug="fighter",
            base_abilities=AbilityScores(
                strength=16, dexterity=12, constitution=14,
                intelligence=10, wisdom=13, charisma=8,
            ),
        )
        actor = _make_builder().build(blueprint)
        # Dwarf: CON 14 + 2 = 16, mod = +3
        # Fighter d10: 10 + 3 = 13
        assert actor.max_hp == 13


# ---------------------------------------------------------------------------
# Test: Racial Bonuses
# ---------------------------------------------------------------------------

class TestRacialBonuses:

    def test_race_applies_ability_bonuses(self):
        """Dwarf: +2 CON applied on top of base abilities."""
        blueprint = _make_blueprint(
            race_slug="dwarf",
            base_abilities=AbilityScores(
                strength=14, dexterity=10, constitution=14,
                intelligence=10, wisdom=12, charisma=8,
            ),
        )
        actor = _make_builder().build(blueprint)
        # Base CON 14 + Dwarf bonus 2 = 16
        assert actor.abilities.constitution == 16
        # STR should stay the same (no dwarf STR bonus)
        assert actor.abilities.strength == 14

    def test_human_gets_plus_one_to_all(self):
        """Human: +1 to every ability score."""
        blueprint = _make_blueprint(
            race_slug="human",
            base_abilities=AbilityScores(
                strength=15, dexterity=13, constitution=13,
                intelligence=9, wisdom=11, charisma=7,
            ),
        )
        actor = _make_builder().build(blueprint)
        assert actor.abilities.strength == 16
        assert actor.abilities.dexterity == 14
        assert actor.abilities.constitution == 14
        assert actor.abilities.intelligence == 10
        assert actor.abilities.wisdom == 12
        assert actor.abilities.charisma == 8


# ---------------------------------------------------------------------------
# Test: Class Proficiencies
# ---------------------------------------------------------------------------

class TestClassProficiencies:

    def test_class_grants_saving_throw_proficiencies(self):
        """Wizard class → INT + WIS saving throw proficiencies."""
        actor = _build(class_slug="wizard")
        assert Ability.INT in actor.saving_throw_proficiencies
        assert Ability.WIS in actor.saving_throw_proficiencies
        assert len(actor.saving_throw_proficiencies) == 2

    def test_fighter_saving_throw_proficiencies(self):
        """Fighter class → STR + CON saving throw proficiencies."""
        actor = _build(class_slug="fighter")
        assert Ability.STR in actor.saving_throw_proficiencies
        assert Ability.CON in actor.saving_throw_proficiencies


# ---------------------------------------------------------------------------
# Test: Spellcasting
# ---------------------------------------------------------------------------

class TestSpellcasting:

    def test_spellcaster_gets_spell_slots(self):
        """Wizard at level 3: 4 × 1st-level, 2 × 2nd-level slots."""
        actor = _build(class_slug="wizard", level=3)
        assert actor.spellcasting is not None
        assert actor.spellcasting.slots[1].max == 4
        assert actor.spellcasting.slots[2].max == 2

    def test_non_caster_has_no_spellcasting(self):
        """Fighter has no spellcasting state."""
        actor = _build(class_slug="fighter", level=1)
        assert actor.spellcasting is None

    def test_wizard_spell_save_dc(self):
        """Wizard level 1: DC = 8 + prof(2) + INT mod."""
        actor = _build(
            class_slug="wizard",
            level=1,
            base_abilities=AbilityScores(
                strength=8, dexterity=14, constitution=12,
                intelligence=16, wisdom=10, charisma=10,
            ),
        )
        # Human: INT 16 + 1 = 17, mod = +3
        # DC = 8 + 2 + 3 = 13
        assert actor.spellcasting is not None
        assert actor.spellcasting.spell_save_dc == 13
        assert actor.spellcasting.spell_attack_bonus == 5


# ---------------------------------------------------------------------------
# Test: Level Features
# ---------------------------------------------------------------------------

class TestLevelFeatures:

    def test_level_5_fighter_gets_extra_attack(self):
        """At level 5, Fighter gets the 'Extra Attack' effect."""
        actor = _build(class_slug="fighter", level=5)
        extra_attack = [e for e in actor.effects if e.name == "Extra Attack"]
        assert len(extra_attack) == 1
        assert extra_attack[0].type == EffectType.BONUS
        assert extra_attack[0].target_stat == "attacks_per_action"

    def test_level_1_fighter_does_not_get_extra_attack(self):
        """Level 1 fighter should NOT have Extra Attack yet."""
        actor = _build(class_slug="fighter", level=1)
        extra_attack = [e for e in actor.effects if e.name == "Extra Attack"]
        assert len(extra_attack) == 0

    def test_level_3_fighter_does_not_get_extra_attack(self):
        """Level 3 fighter should NOT have Extra Attack yet."""
        actor = _build(class_slug="fighter", level=3)
        extra_attack = [e for e in actor.effects if e.name == "Extra Attack"]
        assert len(extra_attack) == 0


# ---------------------------------------------------------------------------
# Test: Background Skills
# ---------------------------------------------------------------------------

class TestBackgroundSkills:

    def test_background_grants_skills(self):
        """Acolyte background → insight + religion skill proficiencies."""
        actor = _build(background_slug="acolyte", chosen_skills=[])
        assert "insight" in actor.skill_proficiencies
        assert "religion" in actor.skill_proficiencies

    def test_skills_deduplication(self):
        """If background and player choices overlap, no duplicates."""
        actor = _build(
            background_slug="soldier",
            chosen_skills=["athletics", "perception"],
        )
        # Soldier gives athletics + intimidation; player also chose athletics
        assert actor.skill_proficiencies.count("athletics") == 1
        assert "intimidation" in actor.skill_proficiencies
        assert "perception" in actor.skill_proficiencies


# ---------------------------------------------------------------------------
# Test: Error Handling
# ---------------------------------------------------------------------------

class TestErrorHandling:

    def test_invalid_race_slug_raises_error(self):
        """Non-existent race slug → CompendiumLookupError."""
        blueprint = _make_blueprint(race_slug="nonexistent")
        with pytest.raises(CompendiumLookupError, match="Race not found"):
            _make_builder().build(blueprint)

    def test_invalid_class_slug_raises_error(self):
        """Non-existent class slug → CompendiumLookupError."""
        blueprint = _make_blueprint(class_slug="nonexistent")
        with pytest.raises(CompendiumLookupError, match="Class not found"):
            _make_builder().build(blueprint)

    def test_invalid_background_slug_raises_error(self):
        """Non-existent background slug → CompendiumLookupError."""
        blueprint = _make_blueprint(background_slug="nonexistent")
        with pytest.raises(CompendiumLookupError, match="Background not found"):
            _make_builder().build(blueprint)


# ---------------------------------------------------------------------------
# Test: Multi-Level HP Progression
# ---------------------------------------------------------------------------

class TestHPProgression:

    def test_level_5_fighter_hp(self):
        """Level 5 human fighter: d10, CON 14 (+1 racial = 15, mod = +2).
        Level 1: 10 + 2 = 12
        Levels 2-5: (6 + 2) × 4 = 32
        Total: 44
        """
        actor = _build(
            race_slug="human",
            class_slug="fighter",
            level=5,
            base_abilities=AbilityScores(
                strength=16, dexterity=14, constitution=14,
                intelligence=10, wisdom=12, charisma=8,
            ),
        )
        assert actor.max_hp == 44
        assert actor.proficiency_bonus == 3  # levels 5-8

    def test_level_3_wizard_hp(self):
        """Level 3 wizard: d6, INT-focused.
        Human: CON 12 + 1 = 13, mod = +1
        Level 1: 6 + 1 = 7
        Levels 2-3: (4 + 1) × 2 = 10
        Total: 17
        """
        actor = _build(
            class_slug="wizard",
            level=3,
            base_abilities=AbilityScores(
                strength=8, dexterity=14, constitution=12,
                intelligence=16, wisdom=10, charisma=10,
            ),
        )
        assert actor.max_hp == 17
