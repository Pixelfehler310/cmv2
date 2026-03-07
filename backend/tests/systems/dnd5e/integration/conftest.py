"""
Shared fixtures for D&D 5e integration tests.

Provides reusable actor factories, encounter builders, and a pre-populated
CompendiumRegistry for CharacterBuilder integration.
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
from src.systems.dnd5e.schemas.common import (
    AbilityScoreBonus,
    AbilityScores,
    EffectDefinition,
    SaveRequirement,
    SkillChoice,
    SpeedBlock,
    SpellcastingProgression,
)
from src.systems.dnd5e.schemas.instances import (
    ActorInstance,
    ConditionInstance,
    ConcentrationState,
    EffectInstance,
)
from src.systems.dnd5e.schemas.definitions import (
    ActionDefinition,
    BackgroundDefinition,
    ClassDefinition,
    RaceDefinition,
)
from src.systems.dnd5e.schemas.creation import CharacterCreationBlueprint
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.data.registry import CompendiumRegistry
from src.systems.dnd5e.engine.character_builder import CharacterBuilder
from src.systems.dnd5e.engine.initiative import InitiativeEntry
from src.systems.dnd5e.engine.combat_state import (
    start_combat,
    get_active_combatant,
    get_turn_budget,
    next_turn,
)


# ---------------------------------------------------------------------------
# Actor Factories
# ---------------------------------------------------------------------------

def make_fighter(**kwargs) -> ActorInstance:
    """Create a level-appropriate Fighter PC with realistic stats."""
    defaults = dict(
        id="fighter_1",
        name="Theron",
        actor_type=ActorType.PLAYER_CHARACTER,
        abilities=AbilityScores(
            strength=18, dexterity=14, constitution=14,
            intelligence=10, wisdom=12, charisma=8,
        ),
        current_hp=45,
        max_hp=45,
        temp_hp=0,
        armor_class=18,
        speed=SpeedBlock(walk=30),
        proficiency_bonus=3,
        saving_throw_proficiencies=[Ability.STR, Ability.CON],
        skill_proficiencies=["athletics", "intimidation"],
    )
    defaults.update(kwargs)
    return ActorInstance(**defaults)


def make_wizard(**kwargs) -> ActorInstance:
    """Create a level-appropriate Wizard PC with realistic stats."""
    defaults = dict(
        id="wizard_1",
        name="Elara",
        actor_type=ActorType.PLAYER_CHARACTER,
        abilities=AbilityScores(
            strength=8, dexterity=14, constitution=12,
            intelligence=18, wisdom=12, charisma=10,
        ),
        current_hp=17,
        max_hp=17,
        temp_hp=0,
        armor_class=12,
        speed=SpeedBlock(walk=30),
        proficiency_bonus=2,
        saving_throw_proficiencies=[Ability.INT, Ability.WIS],
        skill_proficiencies=["arcana", "history"],
    )
    defaults.update(kwargs)
    return ActorInstance(**defaults)


def make_goblin(**kwargs) -> ActorInstance:
    """Create a standard Goblin monster."""
    defaults = dict(
        id="goblin_1",
        name="Goblin",
        actor_type=ActorType.MONSTER,
        abilities=AbilityScores(
            strength=8, dexterity=14, constitution=10,
            intelligence=10, wisdom=8, charisma=8,
        ),
        current_hp=7,
        max_hp=7,
        temp_hp=0,
        armor_class=15,
        speed=SpeedBlock(walk=30),
        proficiency_bonus=2,
    )
    defaults.update(kwargs)
    return ActorInstance(**defaults)


def make_dragon(**kwargs) -> ActorInstance:
    """Create a Young Red Dragon monster."""
    defaults = dict(
        id="dragon_1",
        name="Young Red Dragon",
        actor_type=ActorType.MONSTER,
        abilities=AbilityScores(
            strength=23, dexterity=10, constitution=21,
            intelligence=14, wisdom=11, charisma=19,
        ),
        current_hp=178,
        max_hp=178,
        temp_hp=0,
        armor_class=18,
        speed=SpeedBlock(walk=40, fly=80),
        proficiency_bonus=4,
    )
    defaults.update(kwargs)
    return ActorInstance(**defaults)


# ---------------------------------------------------------------------------
# Action Factories
# ---------------------------------------------------------------------------

def make_melee_attack(**kwargs) -> ActionDefinition:
    """Standard melee weapon attack."""
    defaults = dict(
        name="Longsword",
        action_type=ActionType.MELEE_WEAPON,
        attack_bonus=7,
        damage_dice="1d8",
        damage_bonus=4,
        damage_type=DamageType.SLASHING,
        reach=5,
    )
    defaults.update(kwargs)
    return ActionDefinition(**defaults)


def make_fire_breath(**kwargs) -> ActionDefinition:
    """Dragon's fire breath weapon — save-based action."""
    defaults = dict(
        name="Fire Breath",
        action_type=ActionType.SAVE_EFFECT,
        damage_dice="16d6",
        damage_type=DamageType.FIRE,
        save=SaveRequirement(
            ability=Ability.DEX,
            dc=17,
            on_fail="full_damage",
            on_success="half_damage",
        ),
    )
    defaults.update(kwargs)
    return ActionDefinition(**defaults)


def make_healing_action(**kwargs) -> ActionDefinition:
    """Cure Wounds healing spell."""
    defaults = dict(
        name="Cure Wounds",
        action_type=ActionType.HEALING,
        damage_dice="1d8",
        damage_bonus=3,
    )
    defaults.update(kwargs)
    return ActionDefinition(**defaults)


# ---------------------------------------------------------------------------
# Encounter Builders
# ---------------------------------------------------------------------------

def make_encounter(*actors: ActorInstance, encounter_id: str = "enc_integ") -> EncounterState:
    """Create an EncounterState with the given combatants."""
    return EncounterState(
        id=encounter_id,
        campaign_id="campaign_test",
        combatants=list(actors),
    )


def start_combat_encounter(
    encounter: EncounterState,
    initiative_rolls: list[tuple[str, int, int]] | None = None,
) -> EncounterState:
    """Start combat with explicit initiative entries.

    Args:
        encounter: The encounter to start.
        initiative_rolls: List of (actor_id, roll, dex_score). If None,
            uses descending order based on combatant position.
    """
    if initiative_rolls is None:
        initiative_rolls = [
            (actor.id, 20 - i, actor.abilities.dexterity)
            for i, actor in enumerate(encounter.combatants)
        ]

    initiatives = [
        InitiativeEntry(actor_id=aid, roll=roll, dex_score=dex)
        for aid, roll, dex in initiative_rolls
    ]
    start_combat(encounter, initiatives)
    return encounter


# ---------------------------------------------------------------------------
# CompendiumRegistry (for CharacterBuilder integration)
# ---------------------------------------------------------------------------

@pytest.fixture
def registry() -> CompendiumRegistry:
    """Build a CompendiumRegistry with test definitions."""
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
        languages=["Common"],
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
            options=["acrobatics", "athletics", "intimidation",
                     "perception", "survival"],
            choose=2,
        ),
        level_features=[
            EffectDefinition(
                name="Extra Attack",
                type=EffectType.BONUS,
                target_stat="attacks_per_action",
                value=1,
            ),
        ] and [],  # features defined below via LevelFeature
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


@pytest.fixture
def builder(registry: CompendiumRegistry) -> CharacterBuilder:
    return CharacterBuilder(registry)
