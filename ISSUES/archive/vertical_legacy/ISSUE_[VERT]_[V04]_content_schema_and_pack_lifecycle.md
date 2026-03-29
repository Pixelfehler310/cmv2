# ISSUE [VERT][V04]: Content Schema and Pack Lifecycle

Status: Planned
Owner: Content Systems
Depends on: ISSUE [VERT][V00]

## Why This Exists

This module governs lifecycle-aware content contracts and pack versioning behavior.
It isolates content authoring and publishing semantics from runtime combat concerns.

## Scope

In scope:

- Action, effect, and binding content contracts.
- Content lifecycle transitions and replacement links.
- Pack metadata, compatibility, and provenance policy.

Out of scope:

- Runtime state mutation behavior.

## D2.9 Alignment

- ContentSchema
- ApplicationLayer (ContentPackApplicationService)
- RepositoryLayer (ContentRepository)
- PersistenceDnd5e content definition records

## High-Level Acceptance Criteria

1. Lifecycle transitions are explicit and validated.
2. Version and provenance metadata are consistent.
3. Contract drift checks include content artifacts.

## Decomposition Policy

Create child issues only when V04 becomes active.
