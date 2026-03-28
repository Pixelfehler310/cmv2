"""
Tests for D&D 5e schemas.

Validates that Pydantic models correctly parse real Open5e SRD JSON
and that instance models can be constructed with all components.
"""

import json
from pathlib import Path

import pytest

from src.systems.dnd5e.schemas.enums import (
    ActorType,
    DamageType,
    MagicSchool,
    Size,
)
from src.systems.dnd5e.schemas.common import (
    AbilityScores,
    SpeedBlock,
)
from src.systems.dnd5e.schemas.definitions import (
    MonsterDefinition,
    SpellDefinition,
    ItemDefinition,
)
from src.systems.dnd5e.schemas.instances import (
    ActorInstance,
    ConcentrationState,
    ConditionInstance,
    EffectInstance,
    ItemInstance,
    ResourcePool,
    SpellcastingState,
)
from src.systems.dnd5e.schemas.encounter import (
    EncounterState,
    MapState,
    MapToken,
)
from src.systems.dnd5e.data.loader import CompendiumLoader

pytestmark = pytest.mark.legacy


FIXTURES = Path(__file__).parent / "fixtures"


def load_json(path: str) -> dict:
    with open(FIXTURES / path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Monster Definition
# ---------------------------------------------------------------------------

class TestMonsterDefinition:

    def test_adult_red_dragon_from_srd_json(self):
        """Adult Red Dragon JSON → MonsterDefinition without validation errors."""
        raw = load_json("monsters/adult-red-dragon.json")
        monster = CompendiumLoader._parse_monster(raw)

        assert monster.name == "Adult Red Dragon"
        assert monster.slug == "adult-red-dragon"
        assert monster.armor_class == 19
        assert monster.hit_points == 256
        assert monster.speed.fly == 80
        assert monster.speed.walk == 40
        assert monster.speed.climb == 40
        assert monster.abilities.strength == 27
        assert monster.abilities.dexterity == 10
        assert monster.challenge_rating == 17.0
        assert monster.damage_immunities == "fire"
        assert monster.size == Size.HUGE
        # 6 actions: Multiattack, Bite, Claw, Tail, Frightful Presence, Fire Breath
        assert len(monster.actions) == 6
        assert monster.actions[1].name == "Bite"
        assert monster.actions[1].attack_bonus == 14
        assert monster.actions[1].damage_dice == "2d10+2d6"
        # Legendary actions
        assert len(monster.legendary_actions) == 3
        # Special abilities
        assert len(monster.special_abilities) == 1
        assert "Legendary Resistance" in monster.special_abilities[0].name

    def test_goblin_from_srd_json(self):
        """Goblin JSON → MonsterDefinition."""
        raw = load_json("monsters/goblin.json")
        monster = CompendiumLoader._parse_monster(raw)

        assert monster.name == "Goblin"
        assert monster.size == Size.SMALL
        assert monster.armor_class == 15
        assert monster.hit_points == 7
        assert monster.challenge_rating == 0.25
        assert len(monster.actions) == 2


# ---------------------------------------------------------------------------
# Spell Definition
# ---------------------------------------------------------------------------

class TestSpellDefinition:

    def test_fireball_from_srd_json(self):
        """Fireball JSON → SpellDefinition."""
        raw = load_json("spells/fireball.json")
        spell = CompendiumLoader._parse_spell(raw)

        assert spell.name == "Fireball"
        assert spell.slug == "fireball"
        assert spell.level == 3
        assert spell.school == MagicSchool.EVOCATION
        assert spell.requires_concentration is False
        assert spell.can_be_cast_as_ritual is False
        assert spell.components.verbal is True
        assert spell.components.somatic is True
        assert spell.components.material is True
        assert spell.target_range_sort == 150
        assert "sorcerer" in spell.spell_lists
        assert "wizard" in spell.spell_lists

    def test_cure_wounds_from_srd_json(self):
        """Cure Wounds JSON → SpellDefinition."""
        raw = load_json("spells/cure-wounds.json")
        spell = CompendiumLoader._parse_spell(raw)

        assert spell.name == "Cure Wounds"
        assert spell.level == 1
        assert spell.components.material is False
        assert "cleric" in spell.spell_lists


# ---------------------------------------------------------------------------
# Item Definition
# ---------------------------------------------------------------------------

class TestItemDefinition:

    def test_longsword_from_srd_json(self):
        """Longsword JSON → ItemDefinition."""
        raw = load_json("weapons/longsword.json")
        item = CompendiumLoader._parse_item(raw)

        assert item.name == "Longsword"
        assert item.slug == "longsword"
        assert item.damage_dice == "1d8"
        assert item.damage_type == "slashing"
        assert "versatile (1d10)" in item.properties


# ---------------------------------------------------------------------------
# Actor Instance
# ---------------------------------------------------------------------------

class TestActorInstance:

    def test_actor_instance_creation(self):
        """Create an ActorInstance with inventory, effects, conditions."""
        actor = ActorInstance(
            id="fighter_1",
            definition_slug="fighter",
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
            proficiency_bonus=2,
        )

        assert actor.id == "fighter_1"
        assert actor.name == "Theron"
        assert actor.current_hp == 45
        assert actor.max_hp == 45
        assert actor.actor_type == ActorType.PLAYER_CHARACTER
        assert actor.abilities.strength == 18

    def test_actor_with_full_state(self):
        """ActorInstance can hold conditions, effects, inventory."""
        actor = ActorInstance(
            id="wizard_1",
            name="Gandalf",
            actor_type=ActorType.PLAYER_CHARACTER,
            current_hp=30,
            max_hp=30,
            armor_class=12,
            conditions=[
                ConditionInstance(condition="Frightened",
                                  source_id="dragon_1"),
            ],
            effects=[
                EffectInstance(
                    id="shield_of_faith_1",
                    name="Shield of Faith",
                    type="BONUS",
                    target_stat="armor_class",
                    value=2,
                ),
            ],
            inventory=[
                ItemInstance(id="staff_1", definition_slug="quarterstaff"),
            ],
            spellcasting=SpellcastingState(
                spell_save_dc=15,
                spell_attack_bonus=7,
            ),
            concentration=ConcentrationState(
                is_concentrating=True,
                effect_id="shield_of_faith_1",
            ),
        )

        assert len(actor.conditions) == 1
        assert len(actor.effects) == 1
        assert len(actor.inventory) == 1
        assert actor.spellcasting.spell_save_dc == 15
        assert actor.concentration.is_concentrating is True


# ---------------------------------------------------------------------------
# Encounter State
# ---------------------------------------------------------------------------

class TestEncounterState:

    def test_encounter_state_creation(self):
        """Construct a full encounter with combatants and map."""
        dragon = ActorInstance(
            id="dragon_1",
            name="Adult Red Dragon",
            actor_type=ActorType.MONSTER,
            current_hp=256,
            max_hp=256,
            armor_class=19,
        )
        fighter = ActorInstance(
            id="fighter_1",
            name="Theron",
            actor_type=ActorType.PLAYER_CHARACTER,
            current_hp=45,
            max_hp=45,
            armor_class=18,
        )

        encounter = EncounterState(
            id="enc_1",
            campaign_id="campaign_1",
            round_number=1,
            turn_phase="active",
            active_index=0,
            combatants=[dragon, fighter],
            map=MapState(
                width=50,
                height=50,
                tokens=[
                    MapToken(actor_id="dragon_1", size=Size.HUGE),
                    MapToken(actor_id="fighter_1", size=Size.MEDIUM),
                ],
            ),
        )

        assert encounter.id == "enc_1"
        assert len(encounter.combatants) == 2
        assert encounter.combatants[0].name == "Adult Red Dragon"
        assert encounter.map.width == 50
        assert len(encounter.map.tokens) == 2
