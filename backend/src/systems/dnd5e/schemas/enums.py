"""
D&D 5e Game System Enums.

All enumeration types used across the D&D 5e system module.
Defined per 07_dnd5e_data_models.md architecture spec.
"""

from enum import Enum


class Size(str, Enum):
    TINY = "Tiny"
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    HUGE = "Huge"
    GARGANTUAN = "Gargantuan"


class DamageType(str, Enum):
    SLASHING = "slashing"
    PIERCING = "piercing"
    BLUDGEONING = "bludgeoning"
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"
    THUNDER = "thunder"
    POISON = "poison"
    ACID = "acid"
    NECROTIC = "necrotic"
    RADIANT = "radiant"
    FORCE = "force"
    PSYCHIC = "psychic"


class Ability(str, Enum):
    STR = "strength"
    DEX = "dexterity"
    CON = "constitution"
    INT = "intelligence"
    WIS = "wisdom"
    CHA = "charisma"


class ConditionType(str, Enum):
    BLINDED = "Blinded"
    CHARMED = "Charmed"
    DEAFENED = "Deafened"
    EXHAUSTION = "Exhaustion"
    FRIGHTENED = "Frightened"
    GRAPPLED = "Grappled"
    INCAPACITATED = "Incapacitated"
    INVISIBLE = "Invisible"
    PARALYZED = "Paralyzed"
    PETRIFIED = "Petrified"
    POISONED = "Poisoned"
    PRONE = "Prone"
    RESTRAINED = "Restrained"
    STUNNED = "Stunned"
    UNCONSCIOUS = "Unconscious"


class AoeShape(str, Enum):
    CONE = "cone"
    SPHERE = "sphere"
    LINE = "line"
    CUBE = "cube"
    CYLINDER = "cylinder"


class MagicSchool(str, Enum):
    ABJURATION = "Abjuration"
    CONJURATION = "Conjuration"
    DIVINATION = "Divination"
    ENCHANTMENT = "Enchantment"
    EVOCATION = "Evocation"
    ILLUSION = "Illusion"
    NECROMANCY = "Necromancy"
    TRANSMUTATION = "Transmutation"


class ActionType(str, Enum):
    MELEE_WEAPON = "melee_weapon"
    RANGED_WEAPON = "ranged_weapon"
    MELEE_SPELL = "melee_spell"
    RANGED_SPELL = "ranged_spell"
    SAVE_EFFECT = "save_effect"
    HEALING = "healing"
    UTILITY = "utility"


class EffectType(str, Enum):
    # Stat Modifiers
    BONUS = "BONUS"
    SET = "SET"
    MULTIPLY = "MULTIPLY"
    # Roll Modifiers
    ADVANTAGE = "ADVANTAGE"
    DISADVANTAGE = "DISADVANTAGE"
    # Damage Interaction
    IMMUNITY = "IMMUNITY"
    RESISTANCE = "RESISTANCE"
    VULNERABILITY = "VULNERABILITY"
    # Per-Turn Effects
    DAMAGE_PER_TURN = "DAMAGE_PER_TURN"
    HEALING_PER_TURN = "HEALING_PER_TURN"
    # Status/Condition Effects
    GRANT_CONDITION = "GRANT_CONDITION"
    REMOVE_CONDITION = "REMOVE_CONDITION"


class ResetOn(str, Enum):
    SHORT_REST = "short_rest"
    LONG_REST = "long_rest"
    DAWN = "dawn"
    ROUND = "round"


class ItemCategory(str, Enum):
    SIMPLE_MELEE = "Simple Melee Weapons"
    SIMPLE_RANGED = "Simple Ranged Weapons"
    MARTIAL_MELEE = "Martial Melee Weapons"
    MARTIAL_RANGED = "Martial Ranged Weapons"
    ARMOR_LIGHT = "Light Armor"
    ARMOR_MEDIUM = "Medium Armor"
    ARMOR_HEAVY = "Heavy Armor"
    SHIELD = "Shield"
    ADVENTURING_GEAR = "Adventuring Gear"
    TOOL = "Tool"
    WONDROUS = "Wondrous Item"
    POTION = "Potion"
    SCROLL = "Scroll"
    RING = "Ring"
    ROD = "Rod"
    STAFF = "Staff"
    WAND = "Wand"


class Rarity(str, Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    VERY_RARE = "Very Rare"
    LEGENDARY = "Legendary"


class ActorType(str, Enum):
    PLAYER_CHARACTER = "pc"
    NPC = "npc"
    MONSTER = "monster"
    SUMMON = "summon"


class DurationType(str, Enum):
    INSTANTANEOUS = "instantaneous"
    ROUNDS = "rounds"
    MINUTES = "minutes"
    HOURS = "hours"
    UNTIL_DISPELLED = "until_dispelled"
    UNTIL_LONG_REST = "until_long_rest"
    PERMANENT = "permanent"
