# DOC ISSUE 02: Full Backend Class Diagram Specification (with Properties)

Status: Planned  
Owner: Documentation + Backend

## Goal

Produce a complete backend class-diagram specification including properties/fields for all relevant backend type layers (transport, schemas, domain DTOs, ORM models).

Target output document:

- docs/documentation/backend_class_diagram_specification.md

## Scope

In scope:

- Pydantic schema models used by DnD5e runtime.
- WebSocket transport and session context models.
- Key domain/result DTOs in combat service.
- ORM model layer classes needed to understand persistence interaction.

Out of scope:

- React frontend component types.
- Mock-only test data classes.

## Important Source Files

Transport and session models:

- backend/src/core/ws_protocol.py
- backend/src/core/sessions/models.py
- backend/src/systems/dnd5e/event_types.py

DnD5e schema layer:

- backend/src/systems/dnd5e/schemas/common.py
- backend/src/systems/dnd5e/schemas/enums.py
- backend/src/systems/dnd5e/schemas/definitions.py
- backend/src/systems/dnd5e/schemas/instances.py
- backend/src/systems/dnd5e/schemas/encounter.py
- backend/src/systems/dnd5e/schemas/contracts.py

Service/domain DTOs and orchestration:

- backend/src/systems/dnd5e/services/combat_service.py
- backend/src/systems/dnd5e/application/action_execution_service.py
- backend/src/systems/dnd5e/domain/authorization.py
- backend/src/systems/dnd5e/domain/action_economy.py

ORM classes (for model-layer class diagram sections):

- backend/src/campaigns/lib/campaign.py
- backend/src/campaigns/lib/character.py
- backend/src/identity/models.py
- backend/src/systems/dnd5e/lib/combat_models.py
- backend/src/systems/dnd5e/lib/context_models.py
- backend/src/systems/dnd5e/lib/content_models.py

## Deliverables

1. Mermaid classDiagram blocks split by layer (transport, schema, persistence).
2. Property-level fields in each class (not just class names).
3. Relationship arrows with ownership and dependency direction notes.
4. “Backend is truth” section describing which classes are authoritative state.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
3. docker compose logs backend --tail=200
