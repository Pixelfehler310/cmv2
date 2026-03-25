# ISSUE [VERT][V05]: Compendium CRUD and Definition Catalog

Status: Planned
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
