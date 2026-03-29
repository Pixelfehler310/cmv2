# ISSUE [VERT][V05-01]: Baseline and Drift Audit

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V00]

## Why This Exists

V05 requires a verified baseline before contract freeze and ownership lock.
This issue captures current compendium behavior, linked-entry behavior, and contract drift risk so downstream V05 work starts from measured facts.

## Implementation Steps (Actionable)

1.  **Dump Current Database State:**
    *   Führe ein SQL/JSON-Terminal-Kommando aus, das alle derzeitigen Monster, Spells und Items exportiert: `SELECT * FROM compendium_entries LIMIT 100;`
    *   Speichere das Resultat lokal (z.B. in `tmp/baseline_data.json`).
2.  **Audit the Typescript Types:**
    *   Untersuche `packages/types/src/...` im Frontend nach aktuellen Interfaces für Spells, Items, Monster.
    *   Vergleiche die dortigen Felder mit den Entwürfen aus dem `V05_business_and_content_entities_class_diagram.mmd`.
3.  **Document Breaking Changes:**
    *   Erstelle ein kurzes Dokument `v05_migration_notes.md`, das alle Felder auflistet, die umbenannt werden müssen (z.B. wenn `status` künftig `lifecycle_state` heißen muss).
4.  **Audit the Link-Graph:**
    *   Prüfe, ob bereits hardcodierte Abhängigkeiten existieren (z.B. ob eine Klasse hart auf eine Ability-ID referenziert). Falls ja, notiere diese IDs für die spätere Migration auf das saubere `LinkedEntryReference` Modell.

## Scope

In scope:
- Identify all definition-family CRUD paths currently reachable through REST and application services.
- Capture current payload shapes for list, detail, create, update, delete, and optional lifecycle transitions.
- Capture current linked-entry behavior (forward links, reverse references, missing references, cycle handling).

Out of scope:
- Changing behavior or schema.
- Introducing new APIs.

## Deliverables

1. Current-state path map for definition family flows.
2. Baseline endpoint and contract matrix for scoped families.
3. Linked-entry drift report covering unresolved references and missing links.
4. Baseline notes integrated into V05 planning docs (z.B. `v05_migration_notes.md`).

## Acceptance Criteria

1. Every scoped CRUD path has one documented start and end point.
2. Baseline matrix includes request payload, response payload, reason-code behavior, and lifecycle-field behavior.
3. Linked-entry drift findings are explicit and severity-tagged.
4. Baseline commands run successfully in containerized workflow.
5. Findings are sufficient to support V05-02 and V05-03 without re-discovery.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/data -q`
2. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -k compendium -q`
