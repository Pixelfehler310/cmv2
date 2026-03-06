# D&D 5e Data Models Architecture

This document defines every data type needed for the D&D 5e system module. It distinguishes between **Definitions** (compendium templates, read-only) and **Instances** (live game state, mutable). All schemas live inside `src/systems/dnd5e/`.

---

## 1. Design Principles

| Principle                        | Rule                                                                                                                |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Definition ≠ Instance**        | A spell in the SRD compendium is a `SpellDefinition`. A wizard's prepared Fireball in-session is a `SpellInstance`. |
| **Strict typing**                | No `Dict[str, Any]` for core data. Every action, sense, and speed component gets its own typed model.               |
| **Data-driven**                  | The engine reads `ActionDefinition` records. No `def cast_fireball()` anywhere.                                     |
| **Composition over inheritance** | An `ActorInstance` _has_ a list of `EffectInstance` — it does not inherit from an `Effectable` base.                |

---

## 2. Compendium Definitions (Read-Only Templates)

These are loaded from SRD JSON files at boot. They are never mutated during play.

### Class Diagram

```mermaid
classDiagram
    direction LR

    class MonsterDefinition {
        +str slug
        +str name
        +Size size
        +str type
        +str subtype
        +str alignment
        +int armor_class
        +str armor_desc
        +int hit_points
        +str hit_dice
        +SpeedBlock speed
        +AbilityScores abilities
        +SavingThrows saves
        +dict~str,int~ skills
        +str damage_vulnerabilities
        +str damage_resistances
        +str damage_immunities
        +str condition_immunities
        +str senses
        +str languages
        +float challenge_rating
        +int xp
        +list~ActionDefinition~ actions
        +list~ActionDefinition~ bonus_actions
        +list~ActionDefinition~ reactions
        +list~ActionDefinition~ legendary_actions
        +list~TraitDefinition~ special_abilities
        +str legendary_desc
        +int legendary_action_count
        +list~str~ spell_list
    }

    class SpellDefinition {
        +str slug
        +str name
        +int level
        +MagicSchool school
        +str casting_time
        +str range
        +int target_range_sort
        +Components components
        +str material
        +str duration
        +bool requires_concentration
        +bool can_be_cast_as_ritual
        +str desc
        +str higher_level
        +list~str~ spell_lists
        +AreaOfEffect aoe
    }

    class ItemDefinition {
        +str slug
        +str name
        +ItemCategory category
        +str cost
        +str damage_dice
        +DamageType damage_type
        +str weight
        +list~str~ properties
        +Rarity rarity
        +bool requires_attunement
        +list~EffectDefinition~ effects
    }

    class ActionDefinition {
        +str name
        +str desc
        +ActionType action_type
        +int attack_bonus
        +str damage_dice
        +int damage_bonus
        +DamageType damage_type
        +int reach
        +SaveRequirement save
        +AreaOfEffect aoe
        +RechargeRule recharge
    }

    class TraitDefinition {
        +str name
        +str desc
        +UsageLimit usage
    }

    class EffectDefinition {
        +str name
        +EffectType type
        +str target_stat
        +int | str value
        +str source
    }

    MonsterDefinition *-- ActionDefinition : actions
    MonsterDefinition *-- TraitDefinition : special_abilities
    ItemDefinition *-- EffectDefinition : effects
```

### Supporting Value Types

```mermaid
classDiagram
    direction TB

    class AbilityScores {
        +int strength
        +int dexterity
        +int constitution
        +int intelligence
        +int wisdom
        +int charisma
    }

    class SavingThrows {
        +int | None strength
        +int | None dexterity
        +int | None constitution
        +int | None intelligence
        +int | None wisdom
        +int | None charisma
    }

    class SpeedBlock {
        +int walk
        +int | None fly
        +int | None swim
        +int | None climb
        +int | None burrow
        +bool hover
    }

    class Components {
        +bool verbal
        +bool somatic
        +bool material
        +str material_desc
    }

    class AreaOfEffect {
        +AoeShape shape
        +int size
    }

    class SaveRequirement {
        +Ability ability
        +int dc
        +str on_fail
        +str on_success
    }

    class RechargeRule {
        +int min_roll
        +int max_roll
    }

    class UsageLimit {
        +int uses
        +ResetOn reset_on
    }
```

### Key Enums

```python
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
    SAVE_EFFECT = "save_effect"    # No attack roll, forces a save (e.g., breath weapons)
    UTILITY = "utility"            # Non-damaging (e.g., Frightful Presence)
    # What about Healing actions? are those just spells?

class EffectType(str, Enum):
    BONUS = "BONUS"       # +2 AC
    SET = "SET"           # Set STR to 19
    MULTIPLY = "MULTIPLY" # Speed × 2
    ADVANTAGE = "ADVANTAGE"
    DISADVANTAGE = "DISADVANTAGE"
    IMMUNITY = "IMMUNITY"
    RESISTANCE = "RESISTANCE"
    VULNERABILITY = "VULNERABILITY"
    # what about a damage effect? or status effects? where do those go?

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
```

---

## 3. Live Instances (Mutable Game State)

These are created when the DM places a monster on the map, a player equips an item, or a spell is cast. They hold **session-specific mutable state**.

### Class Diagram

```mermaid
classDiagram
    direction TB

    class ActorInstance {
        +str id
        +str definition_slug
        +str name
        +ActorType actor_type
        +AbilityScores abilities
        +int current_hp
        +int max_hp
        +int temp_hp
        +int armor_class
        +SpeedBlock speed
        +int proficiency_bonus
        +Position position
        +list~ConditionInstance~ conditions
        +list~EffectInstance~ effects
        +list~ItemInstance~ inventory
        +SpellcastingState spellcasting
        +ResourcePool resources
        +ConcentrationState concentration
        +int exhaustion_level
    }

    class EffectInstance {
        +str id
        +str name
        +str source_id
        +str target_id
        +EffectType type
        +str target_stat
        +int | str value
        +DurationType duration_type
        +int | None remaining_rounds
        +bool requires_concentration
    }

    class ConditionInstance {
        +ConditionType condition
        +str source_id
        +str source_effect_id
        +int | None remaining_rounds
    }

    class ItemInstance {
        +str id
        +str definition_slug
        +str custom_name
        +int quantity
        +bool equipped
        +bool attuned
        +int | None current_charges
        +int | None max_charges
    }

    class SpellcastingState {
        +dict~int,SpellSlots~ slots
        +list~PreparedSpell~ prepared_spells
        +Ability spellcasting_ability
        +int spell_save_dc
        +int spell_attack_bonus
    }

    class SpellSlots {
        +int max
        +int current
    }

    class PreparedSpell {
        +str spell_slug
        +bool always_prepared
    }

    class ResourcePool {
        +dict~str,ResourceCounter~ counters
    }

    class ResourceCounter {
        +str name
        +int max
        +int current
        +ResetOn resets_on
    }

    class ConcentrationState {
        +bool is_concentrating
        +str | None effect_id
    }

    class Position {
        +int x
        +int y
        +int elevation
    }

    ActorInstance *-- EffectInstance : effects
    ActorInstance *-- ConditionInstance : conditions
    ActorInstance *-- ItemInstance : inventory
    ActorInstance *-- SpellcastingState : spellcasting
    ActorInstance *-- ResourcePool : resources
    ActorInstance *-- ConcentrationState : concentration
    ActorInstance *-- Position : position
    SpellcastingState *-- SpellSlots : slots
    SpellcastingState *-- PreparedSpell : prepared_spells
    ResourcePool *-- ResourceCounter : counters
```

### Supporting Types

```python
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
```

---

## 4. SRD Compendium Ingest Pipeline

The compendium loader reads Open5e-format JSON and hydrates it into `*Definition` models.

```mermaid
flowchart LR
    A["SRD JSON Files\n(Open5e format)"] --> B["CompendiumLoader\nparse + validate"]
    B --> C["CompendiumRegistry\nin-memory dict store"]
    C --> D["Engine\nreads definitions\nat action resolution"]
    C --> E["REST API\nGET /dnd5e/monsters\nGET /dnd5e/spells"]
```

### Data Source Example: Adult Red Dragon

Key takeaways from the real Open5e data that shaped the schemas:

| SRD Field                               | Model Mapping                   | Notes                                                                     |
| --------------------------------------- | ------------------------------- | ------------------------------------------------------------------------- |
| `actions[].attack_bonus`                | `ActionDefinition.attack_bonus` | Nullable — save-based actions don't have this                             |
| `actions[].damage_dice`                 | `ActionDefinition.damage_dice`  | String expression like `"2d10+2d6"`                                       |
| `speed: {walk: 40, fly: 80, climb: 40}` | `SpeedBlock`                    | Variable keys, must be a structured model                                 |
| `legendary_actions`                     | Same `ActionDefinition` list    | But with `cost` field (Wing Attack costs 2)                               |
| `special_abilities[].desc`              | `TraitDefinition.desc`          | Often contains mechanical rules in prose — parsed later                   |
| `damage_immunities: "fire"`             | `str` field                     | Comma-separated string in SRD, normalized to `list[DamageType]` on ingest |

### Data Source Example: Fireball

| SRD Field                | Model Mapping                           | Notes                                            |
| ------------------------ | --------------------------------------- | ------------------------------------------------ |
| `range: "150 feet"`      | Parsed to `int target_range_sort = 150` | String kept for display, int for engine          |
| `higher_level`           | `SpellDefinition.higher_level`          | Prose description — engine uses a formula parser |
| `requires_concentration` | `bool` — drives `ConcentrationState`    | Links to `EffectInstance.requires_concentration` |
| `components: V, S, M`    | `Components` model                      | Split into three booleans + material description |

---

## 5. Encounter State Container

The encounter is the top-level state object that holds all actors, effects, and map state during combat.

```mermaid
classDiagram
    class EncounterState {
        +str id
        +str campaign_id
        +int round_number
        +str turn_phase
        +int active_index
        +list~ActorInstance~ combatants
        +list~EffectInstance~ global_effects
        +MapState map
    }

    class MapState {
        +int width
        +int height
        +str grid_type
        +set~Position~ difficult_terrain
        +list~MapToken~ tokens
    }

    class MapToken {
        +str actor_id
        +Position position
        +Size size
    }

    EncounterState *-- ActorInstance : combatants
    EncounterState *-- EffectInstance : global_effects
    EncounterState *-- MapState : map
    MapState *-- MapToken : tokens
```

---

## 6. Summary: File Map

All data model files inside `src/systems/dnd5e/`:

| File                     | Contains                                                                                        |
| ------------------------ | ----------------------------------------------------------------------------------------------- |
| `schemas/enums.py`       | All enums: `Size`, `DamageType`, `Ability`, `ConditionType`, etc.                               |
| `schemas/common.py`      | Value types: `AbilityScores`, `SpeedBlock`, `Components`, `Position`, `AreaOfEffect`            |
| `schemas/definitions.py` | `MonsterDefinition`, `SpellDefinition`, `ItemDefinition`, `ActionDefinition`, `TraitDefinition` |
| `schemas/instances.py`   | `ActorInstance`, `EffectInstance`, `ConditionInstance`, `ItemInstance`, `SpellcastingState`     |
| `schemas/encounter.py`   | `EncounterState`, `MapState`, `MapToken`                                                        |
| `data/loader.py`         | `CompendiumLoader` — parses SRD JSON into Definition models                                     |
| `data/registry.py`       | `CompendiumRegistry` — in-memory lookup by slug                                                 |
