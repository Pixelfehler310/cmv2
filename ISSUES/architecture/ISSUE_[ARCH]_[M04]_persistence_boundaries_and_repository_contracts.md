# ISSUE [ARCH][M04]: Persistence Boundaries and Repository Contracts

Status: Planned
Owner: Backend Persistence
Depends on: ISSUE [ARCH][M00]

## Why This Exists

Target architecture needs microservice-ready separation between business logic and data persistence.
This issue protects repository boundaries and prevents persistence leakage into transport or domain orchestration.

## Scope

In scope:

- Define repository interfaces per aggregate.
- Enforce unit-of-work and transaction boundaries.
- Document persistence ownership and allowed write paths.

Out of scope:

- Physical service split/microservice extraction.

## Interface Focus

- Repository read/write contracts.
- Persistence DTO mapping contract.
- Transaction boundary contract.

## Acceptance Criteria

1. Repositories are the only persistence access path for target aggregates.
2. Service layer depends on interfaces, not storage details.
3. Persistence boundary violations are test-detectable.
