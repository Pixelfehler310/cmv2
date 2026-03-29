# ISSUE [VERT][V05-07]: Test Matrix and Completion Gate

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:
- ISSUE [VERT][V05-05]
- ISSUE [VERT][V05-06]

## Why This Exists

This is the final lock for Vertical-05. Es stellt sicher, dass alle Systeme (Contracts, Database, Business Logic, API und Indexing) nahtlos ineinander greifen, bevor wir V05 offiziell beenden und uns der Character-Sheet Integration oder V02 Combat zuwenden.

## Implementation Steps (Actionable)

1.  **Write End-to-End Integration Tests (`backend/tests/systems/dnd5e/content/integration/test_compendium_v05_e2e.py`):**
    *   **Der "Homebrew" Flow:** 
        1. Sende `POST /packs` (Erstelle Draft Pack).
        2. Sende `POST /definitions` (Erstelle Draft Spell).
        3. Teste, ob `PUT /definitions/{id}` bei Status `draft` funktioniert.
        4. Sende `POST /definitions/{id}/publish`.
        5. Teste, ob `PUT /definitions/{id}` nach Publish von einer Exception `409` abgeblockt wird.
        6. Prüfe via `GET /search`, ob der veröffentlichte Spell im SearchIndex für Spieler sichtbar ist.
2.  **Write Error Case Matrix Tests:**
    *   Sende `POST` mit Pydantic Verträgen in denen Pflichtfelder fehlen -> Erwarte `422 Unprocessable Entity` mit klaren Typ-Checks.
    *   Sende Link-Kombinationen, die Zyklen aufbauen und warte auf den korrekten `CycleError` Reason Code im Response.
3.  **Cross-Diagram Sanity Check:**
    *   Verifiziere, dass die Typnamen der API exakt dem `V05_business_and_content_entities_class_diagram` entsprechen (Gibt es `AbilityDefinition` und `LinkedEntryReference`?).

## Scope
In scope:
- E2E Test Suite Development for Content Management.
- Verification of test coverage targets.
- Final approval of all previous V05 subtasks.

Out of scope:
- Changing application implementation rules.

## Deliverables
1. Complete, passing CI Integration Test suite.
2. Sign-off against the V05 Goal post.

## Acceptance Criteria
1. Das End-To-End Testskript läuft ohne Mocking gegen die echte (bzw testcontainer) Docker-Datenbank und Search-Indexer durch.
2. `npm run type-check` im Frontend schlägt nicht Alarm.
3. Der Write-Pfad (SQL) und der Read-Pfad (Indexer) kommunizieren sauber via Events (bzw. Async Tasks).

## Verification Commands
1. `docker compose --profile test run --rm backend-test pytest backend/tests/systems/dnd5e/content/integration/test_compendium_v05_e2e.py -v`
2. `Coverage > 85% on backend/src/systems/dnd5e/content`
