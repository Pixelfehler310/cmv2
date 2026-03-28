# ISSUE [VERT][V05-06]: Indexing, Search, and Linked-Entry Resolution Policy

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:
- ISSUE [VERT][V05-04]

## Why This Exists

This is the CQRS Read-Path. Das Fronted will beim Bauen eines Charakters wissen: "Was bekommt mein Level 3 Fighter?" Das Backend muss die Links "Class -> Level 3 -> Ability -> Effect" rasend schnell auflösen. 
Eine relationale Datenbank ist für tiefverschachtelte Listen-Suchen zu langsam. Wir brauchen einen Projection/Index Layer.

## Implementation Steps (Actionable)

1.  **Implement Link Resolution (`backend/src/systems/dnd5e/content/application/resolution.py`):**
    *   Baue einen Recursive-Graph-Resolver. Wenn der Request lautet "Löse Baum für Fighter Class (ID: 123) auf", muss der Service das `LinkedEntryModel` traversieren.
    *   **Deadlock/Cycle Detection:** Baue einen Checker ein, der Infinite-Loops verhindert (`if next_id in visited_set: raise CycleDetected()`).
    *   **Missing Targets:** Falls ein Link ins Leere zeigt (z.B. weil der User Homebrew gelöscht hat), markiere den Link im Resultat als `BROKEN`, anstatt das Schema komplett abstürzen zu lassen.
2.  **Create Search Index Projection (`backend/src/systems/dnd5e/content/infrastructure/search_indexer.py`):**
    *   Entweder als Denormalisierter Postgres View, per Elasticsearch, oder als In-Memory Cache (Redis).
    *   Das Index-Dokument (Das "Read Model") muss flach sein! z.B. `IndexDocument(id="uuid", family="spell", name_normalized="fireball", search_tokens=["fire", "aoe", "damage"])`.
3.  **Build the Async Projection Worker:**
    *   Schreibe einen Listener, der auf die Events aus V05-04 horcht (`ContentMutationEvent`).
    *   Wenn ein Spell via CRUD neu erstellt wurde, fängt dieser Worker das Event auf und pusht das flache `IndexDocument` in den Such-Index.
4.  **Create Search Endpoints (`api/router.py` extension):**
    *   `GET /api/compendium/search?q=fireball&family=spell` (Dieser Endpoint fragt DIREKT den Search-Index ab, NICHT die relationale SQL-Datenbank!).

## Scope
In scope:
- Graph Traversing and LinkedEntry resolution (Forward & Reverse).
- Cyclus Erkennung und Abfangen von inkonsistenten Link-Graphen.
- Aufbau eines flachen ReadModels für Volltextsuche und Filterung.

Out of scope:
- Relationale CRUD Writes (Erledigt in V05-04).

## Deliverables
1. Recursive Graph-Resolver Service.
2. Denormalisiertes ReadModel (Search Index).
3. Search API Endpoint.

## Acceptance Criteria
1. Zirkuläre A -> B -> A Verlinkungen werden sauber als Error geworfen, ohne den Server in Endlosschleifen zu zwingen.
2. Die `GET /search` Route greift nicht auf die Base-Tabellen zu, sondern liefert Suchergebnisse im Millisekundenbereich aus den Indexes.
3. Wenn ein `ItemDefinition` per Update im Write-Pfad seinen Namen ändert, wird der Read-Indexer asynchron darüber informiert und der Index zieht nach.

## Verification Commands
1. `docker compose --profile test run --rm backend-test pytest tests/data/test_link_resolution.py -q`
2. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_search_index.py -q`
