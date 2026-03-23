# PR4: Domain Extraction and Service Cleanup

Status: Planned
Owner: Engineering
Depends on: PR3

## Goal

Isolate domain rules from orchestration and persistence, reducing CombatService to a compatibility shell or thin integration point.

## Scope

In scope:

- Extract pure or near-pure domain modules for authorization, action economy, and resolution coordination inputs/outputs.
- Remove mixed-layer logic from monolithic service methods.
- Keep behavior parity with existing contracts.

Out of scope:

- New gameplay mechanics.
- Payload redesign.

## Proposed Files

Create:

- backend/src/systems/dnd5e/domain/authorization.py
- backend/src/systems/dnd5e/domain/action_economy.py
- backend/src/systems/dnd5e/domain/action_resolution_pipeline.py

Update:

- backend/src/systems/dnd5e/services/combat_service.py
- backend/src/systems/dnd5e/application/action_execution_service.py
- backend/src/systems/dnd5e/engine/action_resolver.py (only where integration points are needed)

## Tasks

1. Define domain-level request/response types free of transport and DB concerns.
2. Move rule evaluation and decision logic into domain modules.
3. Keep domain deterministic and testable without FastAPI and DB session wiring.
4. Keep application service responsible for transactions and repository calls only.
5. Add unit tests for domain modules with explicit invariant cases.

## Definition of Done

1. Domain modules can be tested without DB.
2. Application service coordinates but does not implement core combat rules.
3. Behavior parity is preserved for key WS command flows.
4. Compatibility wrappers are minimized and clearly marked for removal.

## Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_action_resolver.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
3. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
4. docker compose logs backend --tail=200

## Risks

- Accidental behavior changes while extracting mixed methods.
- Hidden coupling with persistence record shapes.

## Rollback

- Revert only extracted module wiring while keeping tests and docs.
