"""
D&D 5e Character Builder.

Assembles a fully-initialized ActorInstance from a CharacterCreationBlueprint
by resolving race, class, and background definitions from the compendium
registry and applying their bonuses, proficiencies, and features.
"""

from __future__ import annotations

import math
import uuid
from typing import Optional

from ..schemas.enums import Ability, ActorType, EffectType, DurationType
from ..schemas.common import (
    AbilityScores,
    LevelFeature,
    SpeedBlock,
    SpellSlots,
    SpellcastingProgression,
)
from ..schemas.definitions import (
    BackgroundDefinition,
    ClassDefinition,
    RaceDefinition,
)
from ..schemas.instances import (
    ActorInstance,
    EffectInstance,
    SpellcastingState,
)
from ..schemas.creation import CharacterCreationBlueprint
from ..data.registry import CompendiumLookupError, CompendiumRegistry
from .stat_calculator import calculate_modifier, calculate_proficiency_bonus


# ---------------------------------------------------------------------------
# PHB Spell Slot Tables
# ---------------------------------------------------------------------------

# Full caster slot progression (Wizard, Cleric, Druid, Bard, Sorcerer)
_FULL_CASTER_SLOTS: dict[int, dict[int, int]] = {
    1:  {1: 2},
    2:  {1: 3},
    3:  {1: 4, 2: 2},
    4:  {1: 4, 2: 3},
    5:  {1: 4, 2: 3, 3: 2},
    6:  {1: 4, 2: 3, 3: 3},
    7:  {1: 4, 2: 3, 3: 3, 4: 1},
    8:  {1: 4, 2: 3, 3: 3, 4: 2},
    9:  {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
    10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
    11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
    18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
    19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
    20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
}

# Half caster slot progression (Paladin, Ranger)
_HALF_CASTER_SLOTS: dict[int, dict[int, int]] = {
    1:  {},
    2:  {1: 2},
    3:  {1: 3},
    4:  {1: 3},
    5:  {1: 4, 2: 2},
    6:  {1: 4, 2: 2},
    7:  {1: 4, 2: 3},
    8:  {1: 4, 2: 3},
    9:  {1: 4, 2: 3, 3: 2},
    10: {1: 4, 2: 3, 3: 2},
    11: {1: 4, 2: 3, 3: 3},
    12: {1: 4, 2: 3, 3: 3},
    13: {1: 4, 2: 3, 3: 3, 4: 1},
    14: {1: 4, 2: 3, 3: 3, 4: 1},
    15: {1: 4, 2: 3, 3: 3, 4: 2},
    16: {1: 4, 2: 3, 3: 3, 4: 2},
    17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
    18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
    19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
    20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
}

# Third caster slot progression (Eldritch Knight, Arcane Trickster)
_THIRD_CASTER_SLOTS: dict[int, dict[int, int]] = {
    1:  {},
    2:  {},
    3:  {1: 2},
    4:  {1: 3},
    5:  {1: 3},
    6:  {1: 3},
    7:  {1: 4, 2: 2},
    8:  {1: 4, 2: 2},
    9:  {1: 4, 2: 2},
    10: {1: 4, 2: 3},
    11: {1: 4, 2: 3},
    12: {1: 4, 2: 3},
    13: {1: 4, 2: 3, 3: 2},
    14: {1: 4, 2: 3, 3: 2},
    15: {1: 4, 2: 3, 3: 2},
    16: {1: 4, 2: 3, 3: 3},
    17: {1: 4, 2: 3, 3: 3},
    18: {1: 4, 2: 3, 3: 3},
    19: {1: 4, 2: 3, 3: 3, 4: 1},
    20: {1: 4, 2: 3, 3: 3, 4: 1},
}


def _get_slot_table(casting_type: str) -> dict[int, dict[int, int]]:
    """Return the appropriate slot table for a caster type."""
    tables = {
        "full": _FULL_CASTER_SLOTS,
        "half": _HALF_CASTER_SLOTS,
        "third": _THIRD_CASTER_SLOTS,
    }
    return tables.get(casting_type, _FULL_CASTER_SLOTS)


# ---------------------------------------------------------------------------
# Hit Die Parsing
# ---------------------------------------------------------------------------

def _parse_hit_die_max(hit_die: str) -> int:
    """Parse a hit die string like 'd10' and return its maximum value."""
    return int(hit_die.strip().lower().lstrip("d"))


def _hit_die_average(hit_die: str) -> int:
    """Return the average roll for a hit die (rounded up, PHB convention).

    d6 → 4, d8 → 5, d10 → 6, d12 → 7
    """
    max_val = _parse_hit_die_max(hit_die)
    return (max_val // 2) + 1


# ---------------------------------------------------------------------------
# Character Builder
# ---------------------------------------------------------------------------

class CharacterBuilder:
    """Builds an ActorInstance from a CharacterCreationBlueprint."""

    def __init__(self, registry: CompendiumRegistry) -> None:
        self._registry = registry

    def build(self, blueprint: CharacterCreationBlueprint) -> ActorInstance:
        """Assemble a complete ActorInstance from a creation blueprint.

        Steps:
        1. Resolve definitions from registry
        2. Apply racial ability bonuses
        3. Calculate HP
        4. Set proficiency bonus, saving throws, skills
        5. Set speed / size from race
        6. Build spellcasting state (if applicable)
        7. Apply level features as effects
        """
        # 1. Resolve definitions
        race = self._registry.get_race(blueprint.race_slug)
        if race is None:
            raise CompendiumLookupError(
                f"Race not found: '{blueprint.race_slug}'"
            )

        cls = self._registry.get_class(blueprint.class_slug)
        if cls is None:
            raise CompendiumLookupError(
                f"Class not found: '{blueprint.class_slug}'"
            )

        bg = self._registry.get_background(blueprint.background_slug)
        if bg is None:
            raise CompendiumLookupError(
                f"Background not found: '{blueprint.background_slug}'"
            )

        # 2. Apply racial ability bonuses
        abilities = self._apply_racial_bonuses(blueprint.base_abilities, race)

        # 3. HP calculation
        con_mod = calculate_modifier(abilities.constitution)
        max_hp = self._calculate_hp(cls.hit_die, blueprint.level, con_mod)

        # 4. Proficiency bonus
        prof_bonus = calculate_proficiency_bonus(blueprint.level)

        # 5. Saving throw proficiencies (from class)
        save_profs = list(cls.saving_throw_proficiencies)

        # 6. Skill proficiencies (background + player choices)
        skill_profs = list(bg.skill_proficiencies) + list(blueprint.chosen_skills)
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_skills: list[str] = []
        for s in skill_profs:
            if s not in seen:
                seen.add(s)
                unique_skills.append(s)
        skill_profs = unique_skills

        # 7. Speed from race
        speed = SpeedBlock(
            walk=race.speed.walk,
            fly=race.speed.fly,
            swim=race.speed.swim,
            climb=race.speed.climb,
            burrow=race.speed.burrow,
            hover=race.speed.hover,
        )

        # 8. Spellcasting (if class has it)
        spellcasting = self._build_spellcasting(cls, blueprint.level, abilities, prof_bonus)

        # 9. Level features → effects
        effects = self._collect_level_features(cls, blueprint.level)

        actor_id = str(uuid.uuid4())

        return ActorInstance(
            id=actor_id,
            definition_slug=blueprint.class_slug,
            name=blueprint.name,
            actor_type=ActorType.PLAYER_CHARACTER,
            abilities=abilities,
            current_hp=max_hp,
            max_hp=max_hp,
            temp_hp=0,
            armor_class=10,
            speed=speed,
            proficiency_bonus=prof_bonus,
            saving_throw_proficiencies=save_profs,
            skill_proficiencies=skill_profs,
            effects=effects,
            spellcasting=spellcasting,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_racial_bonuses(
        base: AbilityScores,
        race: RaceDefinition,
    ) -> AbilityScores:
        """Return a new AbilityScores with racial bonuses applied."""
        scores = {
            Ability.STR: base.strength,
            Ability.DEX: base.dexterity,
            Ability.CON: base.constitution,
            Ability.INT: base.intelligence,
            Ability.WIS: base.wisdom,
            Ability.CHA: base.charisma,
        }
        for bonus in race.ability_bonuses:
            scores[bonus.ability] = scores.get(bonus.ability, 10) + bonus.bonus

        return AbilityScores(
            strength=scores[Ability.STR],
            dexterity=scores[Ability.DEX],
            constitution=scores[Ability.CON],
            intelligence=scores[Ability.INT],
            wisdom=scores[Ability.WIS],
            charisma=scores[Ability.CHA],
        )

    @staticmethod
    def _calculate_hp(hit_die: str, level: int, con_mod: int) -> int:
        """Calculate max HP using PHB rules.

        Level 1: hit die max + CON mod
        Levels 2+: use average roll (rounded up) + CON mod per level
        """
        if level < 1:
            level = 1
        die_max = _parse_hit_die_max(hit_die)
        avg = _hit_die_average(hit_die)

        hp = die_max + con_mod  # level 1
        if level > 1:
            hp += (avg + con_mod) * (level - 1)
        return max(hp, 1)  # minimum 1 HP

    @staticmethod
    def _build_spellcasting(
        cls: ClassDefinition,
        level: int,
        abilities: AbilityScores,
        prof_bonus: int,
    ) -> Optional[SpellcastingState]:
        """Build SpellcastingState if the class has spellcasting."""
        if cls.spellcasting is None:
            return None

        prog = cls.spellcasting
        slot_table = _get_slot_table(prog.type)
        level_slots = slot_table.get(level, {})

        slots: dict[int, SpellSlots] = {}
        for spell_level, count in level_slots.items():
            slots[spell_level] = SpellSlots(max=count, current=count)

        # Compute spell save DC and attack bonus
        ability_score_map = {
            Ability.STR: abilities.strength,
            Ability.DEX: abilities.dexterity,
            Ability.CON: abilities.constitution,
            Ability.INT: abilities.intelligence,
            Ability.WIS: abilities.wisdom,
            Ability.CHA: abilities.charisma,
        }
        ability_mod = calculate_modifier(
            ability_score_map.get(prog.ability, 10)
        )
        spell_dc = 8 + prof_bonus + ability_mod
        spell_attack = prof_bonus + ability_mod

        return SpellcastingState(
            slots=slots,
            spellcasting_ability=prog.ability,
            spell_save_dc=spell_dc,
            spell_attack_bonus=spell_attack,
        )

    @staticmethod
    def _collect_level_features(
        cls: ClassDefinition,
        level: int,
    ) -> list[EffectInstance]:
        """Convert class LevelFeatures up to the given level into EffectInstances."""
        effects: list[EffectInstance] = []
        for feature in cls.level_features:
            if feature.level > level:
                continue
            for effect_def in feature.effects:
                effects.append(
                    EffectInstance(
                        id=str(uuid.uuid4()),
                        name=effect_def.name,
                        type=effect_def.type,
                        target_stat=effect_def.target_stat,
                        value=effect_def.value,
                        source_id="class_feature",
                        duration_type=DurationType.PERMANENT,
                    )
                )
        return effects
