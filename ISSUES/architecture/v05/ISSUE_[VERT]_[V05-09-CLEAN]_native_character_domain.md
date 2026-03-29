# ISSUE [VERT][V05-09-CLEAN]: Native D&D Character Domain & Sheets Hive

Status: Planned
Owner: Character Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V05-08-CLEAN]

## Why This Exists

The prototype character model in `legacy/campaigns` used hard SQL `ForeignKey` links to specific data tables. This is incompatible with the V05 Goal of a dynamic, versioned compendium.

To finish V05, we must implement a **High-Integrity Character Domain** natively in the `dnd5e` system. This sheet must be "Content-Aware," meaning it doesn't store static data but instead **delegates** its mechanics (stats, features, spells) back to the V05 definitions via weak string references (`def_id`).

## Implementation Steps (Actionable)

1. **Domain Models (`src/systems/dnd5e/sheets/domain/models.py`):**
   * **`PlayerCharacterSheet`**: The persistent out-of-combat anchor.
   * **`CharacterProgression`**: Tracks levels and references `species_def_id`, `class_def_ids`, and `ability_def_ids` (Feats/Features).
   * **`ItemInstance`**: Implements the delegation pattern for inventory tracking.
2. **Hydration Service (`src/systems/dnd5e/sheets/application/hydration_service.py`):**
   * Implement a service that takes a `CharacterID` and merges its local stats (base scores, XP) with its linked definitions from the Compendium to create a **Fully Hydrated ReadModel**.
3. **Infrastructure:**
   * Implement modern SQLAlchemy mappings and a `CharacterRepository`.
4. **API Layer:**
   * Create endpoints for creating characters, updating base scores, and "Leveling Up" (adding new definition links).

## Scope

In Scope:
- Native character sheet persistence in the `dnd5e` namespace.
- Dynamic property resolution via the Compendium Read Path.

Out of Scope:
- Real-time combat state (V02).
- Automatic character generator wizard.

## Acceptance Criteria

1. A character can be created with a `class_def_id` and `species_def_id`.
2. The `HydrationService` successfully resolves the character's base hit dice and speed from the V05 Compendium.
3. Unit tests confirm that changing a `SpeciesDefinition` in the compendium correctly updates the speed on all hydrated character sheets that reference it.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/sheets`
