# ISSUE [VERT][V01-01]: Baseline and Drift Audit

Status: Planned
Owner: Systems DnD5e
Parent: ISSUE [VERT][V01]
Depends on: ISSUE [VERT][V00]

## Why This Exists

V01 requires a stable baseline before contract and ownership lock.
This issue captures the current implementation, observed behavior, and contract drift risk so downstream V01 work starts from verified facts.

## Scope

In scope:

- Identify all current scene selection and scene combat start/end paths.
- Capture current WS and REST command and event payload shapes.
- Record reason code behavior for denied and error outcomes.
- Record baseline verification commands and expected outputs.

Out of scope:

- Changing behavior or refactoring logic.
- Introducing new contracts.

## Deliverables

1. Current-state path map for command flow:
   - transport handler
   - application service
   - policy checks
   - repository writes
2. Baseline event and response matrix for:
   - select_scene
   - start_combat
   - end_combat
3. Drift report listing contract mismatches and ownership ambiguities.
4. Updated baseline notes in V01 planning docs.

## Acceptance Criteria

1. Every lifecycle command path has a single documented start and end point.
2. Drift findings are explicit and categorized:
   - contract shape drift
   - reason code drift
   - ownership ambiguity
3. Baseline commands run successfully in containerized test workflow.
4. Findings are sufficient to support V01-02 and V01-03 without re-discovery.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- Hidden fallback paths can produce false confidence in baseline behavior.
- If drift is material, V01-02 contract freeze must include explicit break decisions.
