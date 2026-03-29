# ISSUE [VERT][V05]: Compendium CRUD and Definition Catalog

Status: Active Planning
Owner: Data + Content Systems
Depends on: ISSUE [VERT][V00]

## Why This Exists

Compendium breadth creates high accidental complexity.
This module keeps definition CRUD complete and consistent without leaking into unrelated runtime architecture streams.

## Scope

In scope:

- CRUD contracts per definition family.
- Repository and endpoint consistency.
- Validation and lifecycle field alignment.

Out of scope:

- Encounter lifecycle transitions.

## D2.9 Alignment

- ApplicationLayer (CompendiumApplicationService)
- RepositoryLayer (CompendiumRepository)
- PersistenceDnd5e definition records

## High-Level Acceptance Criteria

1. CRUD behavior is contract-consistent across families.
2. Repository boundaries are explicit and test-covered.
3. API surface is complete for scoped entities.

## Decomposition Policy

Create child issues only when V05 becomes active.

## Child Issue Plan (Sequenced)

1. ISSUE [VERT][V05-01]: Baseline and Drift Audit.
2. ISSUE [VERT][V05-02]: Definition Contract and Validation Freeze.
3. ISSUE [VERT][V05-03]: Ownership and Repository Boundary Lock.
4. ISSUE [VERT][V05-04]: CRUD Application Orchestration.
5. ISSUE [VERT][V05-05]: REST/WS Contract Convergence for Content Streams.
6. ISSUE [VERT][V05-06]: Indexing, Search, and Linked-Entry Resolution Policy.
7. ISSUE [VERT][V05-07]: Test Matrix and Completion Gate.

Execution rule:

- Complete each issue in sequence unless a dependency exception is explicitly documented.

Module completion rule:

- V05 can only close when V05-07 gate passes and V00 module DoD is satisfied.
