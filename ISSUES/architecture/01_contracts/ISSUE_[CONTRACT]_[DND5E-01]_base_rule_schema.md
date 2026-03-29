# ISSUE [CONTRACT] [DND5E-01]: Base Rule Schema

## Why This Exists
To ensure a single, authoritative definition of "D&D 5e Rules" that is shared between the Compendium (Storage) and the Combat Engine (Execution). This contract eliminates the "Drift" where a Monster's action in the database doesn't match the Engine's execution capabilities.

## Layer 1: The Definition Envelopes


Every rule entity MUST inherit from the `DefinitionRecord`.

### 1. Monster Definition Schema
Extracted and formalized from legacy `monster.py`.

| Field | Type | Constraint |
| :--- | :--- | :--- |
| `name` | `str` | Indexed, Non-empty |
| `size` | `enum` | Tiny, Small, Medium, Large, Huge, Gargantuan |
| `type` | `str` | e.g. "undead", "humanoid" |
| `stats` | `AbilityScoreSet` | Str, Dex, Con, Int, Wis, Cha (1-30) |
| `hit_points` | `HPScale` | Formula (e.g. 5d10 + 20) + Static Value |
| `armor_class` | `int` | >= 0 |
| `speed` | `dict` | Walk, Fly, Swim, Climb (units in feet) |
| `actions` | `list[ActionOperationSpec]` | Canonical V02 Operation Specs |

### 2. Spell Definition Schema
Extracted and formalized from legacy `spell.py`.

| Field | Type | Constraint |
| :--- | :--- | :--- |
| `level` | `int` | 0 (Cantrip) to 9 |
| `school` | `enum` | Abjuration, Evocation, etc. |
| `components` | `dict` | Verbal (bool), Somatic (bool), Material (text) |
| `casting_time` | `str` | e.g. "1 Action", "1 Bonus Action" |
| `duration` | `str` | e.g. "Instantaneous", "1 Minute (Concentration)" |
| `operation_specs` | `list[ActionOperationSpec]` | The mechanical effect of the spell |

### 3. Item Definition Schema
Extracted and formalized from legacy `item.py`.

| Field | Type | Constraint |
| :--- | :--- | :--- |
| `rarity` | `enum` | Common, Uncommon, Rare, Very Rare, Legendary |
| `item_type` | `enum` | Weapon, Armor, Gear, Consumable |
| `weight` | `float` | In lbs |
| `cost` | `int` | In Copper Pieces (CP) |
| `properties` | `list[str]` | e.g. "Finesse", "Magic" |
| `action_specs` | `list[ActionOperationSpec]` | Attacks or activated abilities |

---

## The Action-Ref Alignment (D1 -> D2)
All entities that "Act" MUST define their mechanical effects using the `ActionOperationSpec` defined in `V02_combat_actions_detailed_plan.mmd`.

## Acceptance Criteria
- [ ] Pydantic models in `src/systems/dnd5e/` strictly implement these fields.
- [ ] All mandatory fields are non-null and validated.
- [ ] Monster XP is automatically derived from CR per DMG rules.
- [ ] All legacy `bronze` data can be successfully mapped to this schema.
