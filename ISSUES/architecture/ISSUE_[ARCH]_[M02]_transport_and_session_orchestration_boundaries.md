# ISSUE [ARCH][M02]: Transport and Session Orchestration Boundaries

Status: Planned
Owner: Backend Transport
Depends on: ISSUE [ARCH][M00]

## Why This Exists

WebSocket transport/session handling can accidentally absorb business logic.
This issue constrains transport to routing, validation, and correlation only.

## Scope

In scope:

- Define WS envelope and correlation responsibilities.
- Define session lifecycle boundaries (connect, authorize, subscribe, cleanup).
- Ensure transport never performs persistence or rule evaluation.

Out of scope:

- Combat rule algorithms.

## Interface Focus

- WS command envelope contract.
- WS event envelope contract.
- Error/denied transport mapping contract.

## Acceptance Criteria

1. Transport-layer responsibilities are documented and tested.
2. Business logic lives in service/application/domain layers only.
3. Request correlation and error mapping are deterministic.
