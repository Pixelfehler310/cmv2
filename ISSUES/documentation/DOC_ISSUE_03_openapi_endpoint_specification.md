# DOC ISSUE 03: Full OpenAPI Endpoint Specification

Status: Planned  
Owner: Documentation + Backend

## Goal

Create complete endpoint documentation aligned with FastAPI-generated OpenAPI, including auth requirements, request/response contracts, and route ownership.

Target output document:

- docs/documentation/openapi_endpoint_specification.md

## Scope

In scope:

- REST endpoints exposed by router registration in backend main app.
- Auth and role requirements per endpoint.
- OpenAPI tags/grouping and contract notes.
- Explicit note for websocket endpoint contract alongside OpenAPI-only REST surface.

Out of scope:

- Frontend API usage guides.
- Non-app internal scripts.

## Important Source Files

Application entry and router wiring:

- backend/src/main.py

Data routers:

- backend/src/data/routers/items.py
- backend/src/data/routers/spells.py
- backend/src/data/routers/monsters.py
- backend/src/data/routers/definitions.py

Campaign and character routers:

- backend/src/campaigns/routers/campaigns.py
- backend/src/campaigns/routers/characters.py

Identity/auth endpoints and dependencies:

- backend/src/identity/router.py
- backend/src/identity/dependencies.py
- backend/src/identity/schemas.py

Encounter API (REST) and websocket transport endpoint:

- backend/src/systems/dnd5e/encounter_router.py
- backend/src/core/ws_dispatcher.py

## Deliverables

1. Endpoint inventory table: method, path, auth, role constraints, main response model.
2. Contract drift section comparing generated OpenAPI to hand-written docs.
3. Operational note on docs URL / schema URL and environment caveats.
4. Versioning and backward-compatibility notes for future API changes.

## Verification Commands

1. docker compose up backend -d
2. curl http://localhost:8000/openapi.json
3. curl http://localhost:8000/health
4. docker compose logs backend --tail=200
