# ISSUE [ARCH][M01]: Backend Truth and Domain Contracts

Status: In Progress
Owner: Backend
Depends on: ISSUE [ARCH][M00]

## Why This Exists

The architecture principle says backend is the source of truth.
This issue secures ownership boundaries and domain contract definitions so frontend and transport remain consumers.

## Scope

In scope:

- Define canonical domain state ownership for encounter/combat/context.
- Align service-layer DTO contracts to backend-owned state transitions.
- Remove hidden fallback behavior that weakens ownership clarity.

Out of scope:

- UI-level state ergonomics.

## Interface Focus

- Service contracts: request DTO, result DTO, denied/error contract.
- Event contracts: deterministic event payloads and reason codes.

## Acceptance Criteria

1. Ownership table exists for each core combat aggregate.
2. Service and event contracts are explicit and test-covered.
3. No frontend-driven state mutation logic remains outside backend authority.

## Recursive Child Issue Plan

1. ISSUE [ARCH][M01-01]: Aggregate State Ownership Matrix.
2. ISSUE [ARCH][M01-02]: Service Contracts for Request, Result, and Denied Codes.
3. ISSUE [ARCH][M01-03]: Event Contract Determinism and Reason Taxonomy.
4. ISSUE [ARCH][M01-04]: Remove Legacy Fallbacks Violating Backend Truth.
5. ISSUE [ARCH][M01-05]: M01 Contract Guardrails and Regression Suite.

Execution order:

1. M01-01
2. M01-02
3. M01-03 and M01-04 in parallel when contracts are stable
4. M01-05 as closure gate
