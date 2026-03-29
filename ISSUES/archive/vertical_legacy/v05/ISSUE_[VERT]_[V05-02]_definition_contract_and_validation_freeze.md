# ISSUE [VERT][V05-02]: Definition Contract and Validation Freeze

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:
- ISSUE [VERT][V05-01]

## Why This Exists

CRUD consistency is impossible without a frozen contract layer.
This issue locks canonical definition payloads, lifecycle fields, linked-entry rules, and validation semantics bevor orchestration changes.

## Implementation Steps (Actionable)

1.  **Create Domain Models (`backend/src/systems/dnd5e/content/domain/definition_models.py`):**
    *   **Basis-Klasse `DefinitionRecord`** anlegen. Muss von Pydantic `BaseModel` erben. Felder: `id` (UUID), `family` (Enum), `pack_id` (UUID), `lifecycle_state` (Enum: draft/published/archived), `content_version` (int).
    *   **Sub-Klassen erstellen**: `ClassDefinition`, `SpeciesDefinition`, `BackgroundDefinition`, `AbilityDefinition` (vereinigt Feat & Feature!), `SpellDefinition`, `ItemDefinition`, `MonsterDefinition`. Alle erben von `DefinitionRecord`.
    *   Erstelle das Modell **`ContentPackRecord`** (Pack-Metadaten, `is_homebrew` flag).
    *   Erstelle das Modell **`LinkedEntryReference`** zum Mappen von Relationen (z.B. Class grants Ability).
2.  **Define Validation Logic (`domain/validators.py`):**
    *   Pydantic `@model_validator` schreiben, der sicherstellt, dass `content_version` immer >= 1 ist.
    *   Prüfen, dass ein Draft niemals als `superseded` markiert werden kann (nur `published` kann supersede werden).
3.  **Generate Frontend Types:**
    *   Passe das Type-Generation Script (`scripts/generate_types.py`) an, damit diese neuen Pydantic-Modelle sauber in das `packages/types/src/compendium.ts` Interface kompiliert werden.
4.  **Error Code Taxonomy:**
    *   Lege ein dediziertes Enum `CompendiumErrorCode` an (z.B. `VALIDATION_FAILED`, `LINKED_TARGET_NOT_FOUND`, `INVALID_LIFECYCLE_TRANSITION`).

## Scope
In scope:
- Define canonical contract fields per definition family.
- Freeze shared lifecycle metadata fields.
- Freeze linked-entry reference semantics (target-family, cycle-denial, missing-reference).
- Freeze machine-readable denied/error reason taxonomy.

Out of scope:
- Repository ownership restructuring (passiert in V05-03).
- UI rendering implementation details.

## Deliverables
1. Contract delta specification for all scoped definition families (Domain Models in Python).
2. Validation rule matrix by operation type (`models.py` validators).
3. Reason-code taxonomy document (`exceptions.py` or Enums).

## Acceptance Criteria
1. All scoped definition families have canonical Pydantic field contracts.
2. Linked-entry constraints are explicit and testable via Pydantic/Domain Logic.
3. Validation denials map to stable, machine-readable reason codes (FastAPI Error Formats).
4. `npm run generate-types` (oder das Äquivalent) spuckt saubere TypeScript-Interfaces für das Frontend aus.

## Verification Commands
1. `docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check`
2. `docker compose --profile test run --rm backend-test pytest tests/data -k validation -q`
