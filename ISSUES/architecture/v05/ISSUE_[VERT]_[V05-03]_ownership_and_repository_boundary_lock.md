# ISSUE [VERT][V05-03]: Ownership and Repository Boundary Lock

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:
- ISSUE [VERT][V05-02]

## Why This Exists

Content correctness depends on deterministic write ownership.
This issue enforces one write authority for definitions, lifecycle transitions, and linked-entry graph updates using the canonical DB layer.

## Implementation Steps (Actionable)

1.  **Create ORM Models (`backend/src/modules/compendium/infrastructure/orm.py`):**
    *   Schreibe SQLAlchemy `Base` Klassen für `ContentPackModel`, `CompendiumDefinitionModel` und `LinkedEntryModel`.
    *   **Tipp:** Nutze für das individuelle Payload eines Speichers (z.B. den spezifischen Body von `MonsterDefinition` oder `SpellDefinition`) ein **`JSONB` Feld** (`payload = Column(JSONB)`). Das erlaubt schnelle Suchen über Postgres Indexe, ohne für jede Definition Family 20 neue Tabellenspalten anzulegen.
2.  **Alembic Migration:**
    *   Führe `alembic revision --autogenerate -m "v05 compendium foundation"` aus.
    *   Prüfe das generierte File, pass es an und committe es (`alembic upgrade head`).
3.  **Implement Repositories (`infrastructure/repositories.py`):**
    *   Erstelle `ContentPackRepository` mit `create()`, `get_by_id()`, `list()`.
    *   Erstelle `DefinitionRepository` mit `upsert()`, `get_by_pack_id()`, `get_versions()`. 
    *   **Wichtig:** Das Repository MUSS das SQLAlchemy Model (ORM) in das Pydantic Modell (aus V05-02) umwandeln, bevor es zurückgegeben wird! Der Application Layer darf NIE SQL-Artefakte sehen.
4.  **Transaction Boundary (Unit of Work):**
    *   Stelle sicher, dass Multi-Writes (z.B. ein neues Monster einfügen + gleichzeitig die `LinkedEntryReference` für seine Fähigkeiten updaten) in einer strikten `.commit() / .rollback()` SQL-Transaktion gekapselt sind.

## Scope
In scope:
- Assign single-writer ownership per mutable content aggregate.
- Lock repository boundaries for definition records, packs, and relations.
- Define transaction boundary for multi-record operations.

Out of scope:
- Frontend projection implementation.
- API Routers.

## Deliverables
1. SQLAlchemy Models für alles Content/Entity mäßige.
2. Alembic Migrations-Skripts ready to execute.
3. Sauber getrennte Repositories, die DTOs/Pydantic-Models zurückgeben.

## Acceptance Criteria
1. JSONB-Index-Struktur für das Polymorphe Payload ist implementiert.
2. Jedes Repository gibt saubere Domain Models aus PR 1 zurück statt SQLAlchemy Objects.
3. Die Transaction Boundary greift (ein Crash beim Schreiben der Links rollt den Definition-Insert mit zurück).

## Verification Commands
1. `docker compose --profile test run --rm backend-test pytest tests/data -k repository -q`
2. Check migrations: `alembic upgrade head` in a clean DB.
