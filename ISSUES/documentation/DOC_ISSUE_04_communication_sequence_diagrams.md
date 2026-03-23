# DOC ISSUE 04: Communication Sequence Diagram Specification

Status: Planned  
Owner: Documentation + Backend + Frontend

## Goal

Create a sequence-diagram package that documents critical communication flows between client, transport, backend services, persistence, and state broadcast paths.

Target output document:

- docs/documentation/communication_sequence_diagrams.md

## Scope

In scope:

- WS connect and initial state sync.
- Command flow: request_action to publish result events.
- Turn flow: end_turn with effect ticking and turn_advanced.
- Preview flows (movement preview / attack preview).
- REST + WS interaction points where relevant.

Out of scope:

- UI component animation/state transitions.
- Non-critical exploratory feature flows.

## Important Source Files

Backend transport and handler orchestration:

- backend/src/core/ws_dispatcher.py
- backend/src/core/sessions/manager.py
- backend/src/systems/dnd5e/ws_handler.py
- backend/src/systems/dnd5e/state_filter.py

Backend service and engine execution paths:

- backend/src/systems/dnd5e/services/combat_service.py
- backend/src/systems/dnd5e/application/action_execution_service.py
- backend/src/systems/dnd5e/engine/action_resolver.py
- backend/src/systems/dnd5e/engine/effect_engine.py

Frontend receive/dispatch integration (for end-to-end communication diagrams):

- frontend/packages/shared/src/stores/useCombatStore.ts
- frontend/packages/shared/src/adapters/wsEnvelopeAdapter.ts
- frontend/apps/host/src/routes/SessionRoute.tsx

Reference docs already created:

- docs/documentation/event_specification.md

## Deliverables

1. Mermaid sequence diagrams for each critical path listed in scope.
2. Deterministic event ordering notes per flow.
3. Error/denied branch variants for command flows.
4. Correlation notes for request_id propagation.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose logs backend --tail=200
3. (optional) frontend integration smoke in host session route
