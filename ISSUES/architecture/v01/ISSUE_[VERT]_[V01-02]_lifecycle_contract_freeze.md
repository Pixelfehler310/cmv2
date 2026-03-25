# ISSUE [VERT][V01-02]: Lifecycle Contract Freeze

Status: Planned
Owner: Systems DnD5e
Parent: ISSUE [VERT][V01]
Depends on:

- ISSUE [VERT][V01-01]

## Why This Exists

V01 must provide deterministic lifecycle contracts across interfaces.
This issue freezes command inputs, success outputs, denied/error reason codes, and event payloads for scene and scene-combat lifecycle transitions.

## Scope

In scope:

- Freeze command contracts for select_scene, start_combat, end_combat.
- Freeze denied and error reason code set for these commands.
- Freeze WS and REST externally visible payload shape.
- Freeze lifecycle event contract payloads and required fields.

Out of scope:

- Transport-specific implementation refactors.
- New lifecycle commands outside V01 boundary.

## Deliverables

1. Command contract specification with required and optional fields.
2. Reason code registry for denied and error outcomes.
3. Event contract table with deterministic payload definitions.
4. Contract test checklist mapped to each command and event.

## Acceptance Criteria

1. Contract docs define one canonical payload shape per command and event.
2. Denied and error outcomes are represented by stable reason codes.
3. WS and REST contracts align to the same application semantics.
4. Contract definitions are consumable by frontend projection without inference.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check

## Risks and Notes

- Contract freeze should avoid preserving accidental legacy fields from MVP behavior.
- If a contract cannot be stabilized, defer with explicit follow-up issue and risk statement.
