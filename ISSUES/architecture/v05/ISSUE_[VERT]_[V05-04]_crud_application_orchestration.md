# ISSUE [VERT][V05-04]: CRUD Application Orchestration

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:
- ISSUE [VERT][V05-03]

## Why This Exists

Repositories (SQL) and Models (Pydantic) exist, but they have no brain. 
This issue creates the authoritative Service Layer (Application Services). Es dirigiert *wie* Business-Regeln angewendet werden, wer was editieren darf, und wie State-Transitions (Bsp: Draft -> Published) orchestriert werden.

## Implementation Steps (Actionable)

1.  **Create Services (`backend/src/systems/dnd5e/content/application/services.py`):**
    *   Erstelle den `CompendiumApplicationService`. Er bekommt das Repository injiziert (Dependency Injection).
2.  **Implement Create & Update Commands:**
    *   Schreibe `create_definition(...)`: Es prüft über das Repo, ob die ID oder der Slug bereits existiert. Wenn nein: `repository.upsert()`.
    *   Schreibe `update_definition(...)`: **Wichtig:** Eine Definition darf nur geupdated werden, wenn ihr `lifecycle_state == 'draft'` ist. Wirf eine Exception, falls versucht wird, eine bereits publizierte Definition via Update zu verändern.
3.  **Implement Lifecycle Commands:**
    *   Schreibe `publish_definition(...)`: Setzt den state auf `published` und sperrt den Datensatz für zukünftige harte Updates.
    *   Schreibe `supersede_definition(old_id, new_id)`: Ein Replacement-Flow für Patches (z.B. wenn eine Ability generfed wird, wird die alte `superseded` und verweist auf die neue).
4.  **Implement Event Emitting (Prep for V05-06):**
    *   Sobald `publish_definition` erfolgreich die Transaktion committet, sollte der Service intern ein (in-memory) Event werfen, z.B. `ContentMutationEvent`. (Dies wird im Search-Indexer gebraucht).

## Scope
In scope:
- Application Service Orchestration of Create, Read, Update, Delete for Definitions and Packs.
- Business Logic enforcement (Draft mutability, Publishing immutability).
- Supersede/Replacement Flow orchestration.

Out of scope:
- API Routes (happens in V05-05).
- Frontend.

## Deliverables
1. Python Application Service(s) for Compendium Operations.
2. Business rule implementation covering mutable vs immutable states.

## Acceptance Criteria
1. Service kapselt die Business Logik komplett (keine Datenbank-Logik in den Controllern später!).
2. Tests covern den Fall: Update auf eine `published` Entität wird mit einem klaren Fehlercode blockiert.
3. Supersedence Chain kann erfolgreich gesetzt werden (Ein Eintrag weiß, wer sein Nachfolger ist).

## Verification Commands
1. `docker compose --profile test run --rm backend-test pytest tests/data/test_compendium_service.py -q`
