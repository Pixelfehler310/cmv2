# V05 Migration Notes: Schema Drift & Link-Graph Audit

This document serves as the primary artifact for understanding how the currently implemented system (baseline) must change to align with V05 architectures. 

## 1. Schema Drift Analysis (Baseline vs. V05)
The findings here were gathered by analyzing `backend/src/data/lib/` and `frontend/packages/types/src/generated.ts` against `V05_business_and_content_entities_class_diagram.mmd`.

### 1.1 Universal Definition Drift (All Content Types)
Currently, `Spells`, `Items`, and `Monsters` lack the core metadata required to belong to the Content Catalog Domain.
- **[MISSING] `family`**: Needs to be added to all entities to specify their definition type dynamically.
- **[MISSING] `pack_id`**: Needs to be added to support content entitlement and ownership.
- **[MISSING] `content_version`**: Needs to be added to allow for immutable revisions.
- **[MISSING] `lifecycle_state`**: Currently missing; V05 requires `draft | published | archived`.

### 1.2 Monster Definition Drift
| Current Model (Baseline) | Target V05 Model | Migration Note |
|---|---|---|
| `hit_points` (int) | `hit_points_formula` (str) | We must transition from an absolute integer to a generic formula (e.g. "1d8+2"). |
| `effects[]`, `actions[]`, `special_abilities[]`, `legendary_actions[]` | `action_operation_specs[]` (list[dict]) | V05 unifies all interactive mechanical behaviors into a single list of standardized operation dictionaries. We must consolidate these disparate arrays. |

### 1.3 Item Definition Drift
| Current Model (Baseline) | Target V05 Model | Migration Note |
|---|---|---|
| `type` | `item_type` | Needs to be renamed to avoid conflict with `family` or Python reserved words. |
| `price` | `cost` | Needs renaming. |
| `effects[]` | `action_operation_specs[]` | As with monsters, static and active effects must merge into unified ops. |

### 1.4 Spell Definition Drift
| Current Model (Baseline) | Target V05 Model | Migration Note |
|---|---|---|
| `effects[]` | `action_operation_specs[]` | Again, disparate effects logic must pivot to standard operation specs. |

---

## 2. Link-Graph Dependency Audit
The following analyzes severe structural coupling (hard-coded references) that will break under the new "Content Catalog Domain" separation and must be updated to V05 standard linkages.

### 2.1 Character Identity Couplings (High Severity)
Currently, the `Character` table (`backend/src/campaigns/lib/character.py`) utilizes explicit relational `ForeignKey` constraints directly to individual definition tables:
- `species_id = ForeignKey("species.id")`
- `class_id = ForeignKey("classes.id")`
- `background_id = ForeignKey("backgrounds.id")`

**V05 Resolution:** 
These strict DB-level foreign keys must be dismantled. Content Definitions might live as versioned documents or within Content Packs that CharacterProgression only weakly references. 
Characters should utilize `species_def_id`, `background_def_id`, and `class_levels` stored contextually, pointing to immutable references without strict Relational ForeignKey constraints to definition families.

### 2.2 Inventory Instances
Currently, `ItemInstance` references `item_id` string values from the `Item` model.
**V05 Resolution:** 
Rename `item_id` to `item_def_id` to conform with V05 terminology and point to a DefinitionRecord ID rather than a hard DB primary key.

### 2.3 Spell Books (Prepared Spells)
Currently, `Character` models store `spells` natively as a raw JSON list.
**V05 Resolution:** 
V05 designates a specific `PreparedSpells` structure containing `spell_def_ids`. We need to pull the spell logic out of raw character JSON and into this dedicated object.

### 2.4 Internal Catalog Linkages (LinkedEntryReference)
Currently, certain effects or abilities embed references to other definitions implicitly (e.g. an ability granting a spell via raw JSON properties).
**V05 Resolution:** 
These native connections must be extracted into explicit `LinkedEntryReference` records (e.g., `source_definition_id="race123"`, `target_definition_id="spell456"`, `relation_kind="grants"`). This prevents endless loops and supports clean projection.
