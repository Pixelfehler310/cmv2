# ISSUE [VERT][V05-11]: Inventory & Prepared Spells V05 Pivot

Status: Planned
Owner: Character Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V05-08]

## Why This Exists

Character inventory and spellbooks are currently "Static Snapshots" stored as raw JSON or linked to legacy tables. This means that if a spell's wording is corrected or an item's weight is balanced in the compendium, the players' character sheets remain out of sync.

V05 introduces the concept of "Linked Instances." We need to refactor the character's active state to "Delegate" its mechanics back to the Compendium definitions while storing only the "Instance Delta" (e.g., `is_equipped`, `current_charges`, `custom_nickname`).

## Implementation Steps (Actionable)

1. **Refactor ItemInstance:**
   * Create a proper `ItemInstance` model that points to an `item_def_id`.
   * Separate "Intrinsic Stats" (from the definition) from "Extrinsic State" (from the character inventory).
2. **Implement Spell Resolution:**
   * Replace raw spell lists with `PreparedSpell` objects referencing `spell_def_id`.
3. **Hydration Service:**
   * Implement a "Sheet Hydrator" that takes a character's list of IDs and merges them with the latest (or pinned) definitions from the Compendium service.
4. **Version Pinning (Optional but Recommended):**
   * Allow players to "Pin" an item/spell to a specific `content_version` to prevent balance changes from disrupting their current game.

## Scope

In Scope:
- `backend/src/campaigns/lib/inventory.py` and `backend/src/campaigns/lib/character.py`.
- Migration of existing items/spells to the V05 link-based model.

Out of Scope:
- Combat math or damage calculation (V02).

## Acceptance Criteria

1. Character character inventory contains references to V05 standard Items.
2. The UI/API can successfully "Hydrate" a character sheet by resolving all item/spell definitions.
3. Changing a definition's `cost` or `weight` in the Compendium is immediately reflected in the character sheet's read-model (if not version-pinned).

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/campaigns -k inventory_hydration`
