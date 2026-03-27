# V05 Ticket Fleshing-Out Plan

Du möchtest die 7 strukturellen V05-Tickets (`V05-01` bis `V05-07`) in extrem aufbereitete, handlungsorientierte Entwickler-Checklisten ("Actionable Developer Specifications") umwandeln. 

Ich werde alle 7 `.md` Dateien im `ISSUES/architecture/v05` Ordner komplett überschreiben. Statt theoretischer Architekturziele werden sie konkrete, schrittweise Anleitungen enthalten: **Welche Datei muss erstellt werden? Welche Variablen müssen rein? Wie sieht der Test dafür aus?**

## Proposed Changes

Ich werde in jede der folgenden Dateien eine neue Sektion `## Implementation Steps (Actionable)` einfügen, die genau beschreibt, was zu tun ist:

### [MODIFY] `ISSUE_[VERT]_[V05-01]_baseline_and_drift_audit.md`
**Fokus:** Bestandsaufnahme.
- **Schritte:** Alle aktuellen Daten in der alten Datenbank dumpen (z.B. als JSON), Frontend-Typen analysieren um zu gucken, wo wir von der neuen V05 Struktur noch abweichen.

### [MODIFY] `ISSUE_[VERT]_[V05-02]_definition_contract_and_validation_freeze.md`
**Fokus:** Domain / Pydantic Layer.
- **Schritte:** 
  1. Erstellen von `backend/src/compendium/models/domain.py`.
  2. Pydantic Basis-Klasse `DefinitionRecord` mit `lifecycle_state` Enum implementieren.
  3. Polymorphe Sub-Klassen (`AbilityDefinition`, `SpellDefinition`, `MonsterDefinition`) exakt nach dem `V05_business_and_content_entities` Diagramm definieren.
  4. Generierung der TypeScript-Typen auslösen.

### [MODIFY] `ISSUE_[VERT]_[V05-03]_ownership_and_repository_boundary_lock.md`
**Fokus:** SQLAlchemy / Datenbankschicht.
- **Schritte:**
  1. Erstellen von `backend/src/compendium/models/orm.py`.
  2. Implementierung von `ContentPackRecord` und `DefinitionRecord` als ORM Modelle mit JSONB Spalten (für Flexibilität).
  3. Erstellen der Alembic Migration.
  4. Schreiben des `DefinitionRepository` mit sauberen Schnittstellen (z.B. `get_by_pack()`, `upsert_definition()`).

### [MODIFY] `ISSUE_[VERT]_[V05-04]_crud_application_orchestration.md`
**Fokus:** Services & Business Logic (Application Layer).
- **Schritte:**
  1. Erstellen der Klasse `CompendiumApplicationService`.
  2. Logik implementieren: Verhindern, dass `published` Definitionen modifiziert werden (nur Superseding erlaubt).
  3. Validierung der `ContentPack` Zugehörigkeiten.

### [MODIFY] `ISSUE_[VERT]_[V05-05]_rest_ws_contract_convergence_for_content_streams.md`
**Fokus:** FastAPI Endpoints & Websockets.
- **Schritte:**
  1. Erstellen von `backend/src/compendium/router.py`.
  2. `POST /api/compendium/packs`, `GET /api/compendium/definitions/{family}` aufbauen und an den ApplicationService koppeln.
  3. Websocket Broadcaster einrichten: Wenn Content auf `published` gesetzt wird, sendet der WS ein `ContentLifecycleEvent` an alle offenen Campaigns.

### [MODIFY] `ISSUE_[VERT]_[V05-06]_indexing_search_and_linked_entry_resolution_policy.md`
**Fokus:** Search ReadModel & Graph Resolution.
- **Schritte:**
  1. Den `LinkedEntryResolutionService` bauen (löst Abhängigkeiten wie "Klasse Fighter beinhaltet Ability Action Surge" auf).
  2. Aufbau eines Denormalisierten Search-Indexes (als separate Tabelle oder In-Memory), der blitzschnelles Volltext-Suchen im Frontend erlaubt.

### [MODIFY] `ISSUE_[VERT]_[V05-07]_test_matrix_and_completion_gate.md`
**Fokus:** Integrationstests.
- **Schritte:** Checkliste zum Schreiben von integration Tests (`test_compendium_crud.py`, `test_linked_graph_cycles.py`).

## User Review Required

Bevor ich diese 7 Dateien radikal umschreibe: Erfüllt dieser Ansatz genau das, was du dir unter "extrem aufarbeiten" vorstellst (also sehr technischer, File/Class-zentrierter Leitfaden für den Coder, basierend auf unserer V05 Theorie)?
