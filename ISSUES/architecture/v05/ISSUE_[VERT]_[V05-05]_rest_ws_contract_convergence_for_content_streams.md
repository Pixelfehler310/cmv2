# ISSUE [VERT][V05-05]: REST/WS Contract Convergence for Content Streams

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:
- ISSUE [VERT][V05-04]

## Why This Exists

The API Gateway for the Compendium. REST is needed for CRUD Operations und WS (WebSockets) wird gebraucht, um das VTT in Echtzeit zu benachrichtigen, wenn sich Content Limits oder Regeln live während einer Kampagne ändern.

## Implementation Steps (Actionable)

1.  **Create API Router (`backend/src/modules/compendium/api/router.py`):**
    *   Erstelle einen FastAPI Router: `router = APIRouter(prefix="/api/compendium", tags=["Compendium"])`
    *   **Endpoints für Content Packs:** `POST /packs`, `GET /packs`, `GET /packs/{pack_id}`.
    *   **Endpoints für Definitionen:** 
        - `POST /definitions` (Nimmt das abstrakte `DefinitionRecord` Pydantic Modell entgegen und validiert basierend auf dem `family` Enum-Feld die korrekte Sub-Klasse).
        - `PUT /definitions/{id}`
        - `DELETE /definitions/{id}`
        - `POST /definitions/{id}/publish` (Lifecycle Actions)
    *   Achte darauf, dass die Router-Funktionen intern nur Methoden des `CompendiumApplicationService` aus V05-04 aufrufen, anstatt direkten DB-Zugriff zu nutzen.
2.  **Define HTTP Error Contracts:**
    *   Schreibe Exception Handler, die die Custom Exceptions aus V05-04 (`InvalidLifecycleTransition`) in saubere HTTP `400 Bad Request` oder `409 Conflict` umwandeln.
    *   Nutze das etablierte Error Response Schema (z.B. `{ "error": "VALIDATION_FAILED", "message": "Cannot update published spell." }`).
3.  **WebSocket Integration (`api/ws_events.py`):**
    *   Baue den `ContentStreamWsHandler`, falls die Kampagne live läuft und z.B. der DM on-the-fly einen Homebrew Spell auf "Published" setzt.
    *   Das WebSocket muss ein `ContentLifecycleEvent` (z.B. "DefinitionPublished") an den Raum schicken.

## Scope
In scope:
- FastAPI Routes für komplette V05 CRUD Coverage.
- WebSocket Events für Lifecycle Status Änderungen (Draft -> Published).
- Auth-Dependency: (Optional) Sicherstellen, dass nur eingeloggte Accounts Packs erstellen können.

Out of scope:
- Frontend Client Integration.

## Deliverables
1. FastAPI Router mit OpenAPI/Swagger Dokumentation (Pydantic Models aus V05-02).
2. Exception Mapping Middleware für saubere REST Fehler.
3. WebSocket Broadcast für Lifecycle Events.

## Acceptance Criteria
1. `GET /docs` (Swagger UI) zeigt alle CRUD Routen mit korrekten Payload-Schemas für Spells, Items, Monsters.
2. Validation Errors werfen saubere REST JSON-Antworten und fangen Pydantic-Crashes ab.
3. Live-Event via Websocket wird geschickt, wenn ein Endpoint `supersede_definition` triggert.

## Verification Commands
1. `docker compose up backend` + Öffnen von `http://localhost:8000/docs` zur Schema Prüfung.
2. `docker compose --profile test run --rm backend-test pytest tests/api/compendium -q`
