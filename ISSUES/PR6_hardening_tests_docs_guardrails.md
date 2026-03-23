# PR6: Hardening Tests, Docs, and Guardrails

Status: Planned
Owner: Engineering
Depends on: PR5

## Goal

Lock in the refactor with robust tests, architecture docs, and contribution guardrails to prevent regression into mixed-layer design.

## Scope

In scope:

- Add missing end-to-end coverage for context and action paths.
- Document final layer boundaries and where logic belongs.
- Add PR checklist and drift checks for this slice.

Out of scope:

- Generic action-id migration implementation.
- Frontend context push feature.

## Proposed Files

Update likely:

- docs/development/known_issues.md
- docs/architecture/backend/23_combat_slice_layer_refactor_adr.md
- backend/tests/systems/dnd5e/test_ws_integration.py
- backend/tests/campaigns/test_campaigns_router.py
- backend/tests/systems/dnd5e/test_combat_service.py

Potential new docs:

- docs/development/backend_layer_boundaries.md
- docs/development/pr_checklist_layer_contract.md

## Tasks

1. Add end-to-end tests for context load + action resolve persistence assertions.
2. Add contract-focused tests for denied/error reason codes.
3. Update architecture docs with final ownership table per layer.
4. Add PR checklist requiring layer, contract, and artifact disclosure.
5. Ensure schema/type drift gate instructions are part of contributor workflow.

## Definition of Done

1. Critical context/action flows have deterministic automated coverage.
2. Architecture docs reflect actual implementation boundaries.
3. Guardrails are visible and enforced through PR process.
4. Team has clear path for follow-up epic (generic action naming).

## Verification

1. docker compose --profile test run --rm backend-test pytest tests/campaigns/test_campaigns_router.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
3. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
4. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_action_resolver.py -q
5. docker compose --profile test run --rm backend-test python scripts/generate_types.py --check

## Risks

- Test brittleness if fixtures are overly coupled to implementation details.
- Documentation lag if final changes are not mirrored before merge.

## Rollback

- Keep guardrail docs additive and non-breaking; adjust test assertions to contract level if implementation details change.
