# ISSUE [ARCH][M05]: Frontend Read Models and Projection Boundaries

Status: Planned
Owner: Frontend + Backend Contracts
Depends on: ISSUE [ARCH][M00]

## Why This Exists

Frontend should display backend truth, not calculate gameplay rules.
This issue defines projection/read-model boundaries so UI remains modular and safe.

## Scope

In scope:

- Define frontend-consumed read models from backend WS/REST contracts.
- Remove or avoid derived rule calculations in frontend.
- Clarify adapter/store responsibilities for projection only.

Out of scope:

- Visual redesign.

## Interface Focus

- Backend event to store projection contract.
- API adapter normalization contract.
- Type synchronization contract between backend models and frontend types.

## Acceptance Criteria

1. Frontend rule computation responsibilities are removed or explicitly banned.
2. Projection interfaces are documented and typed.
3. Backend model changes trigger frontend type sync workflow.
