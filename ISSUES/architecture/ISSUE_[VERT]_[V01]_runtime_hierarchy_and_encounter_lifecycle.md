# ISSUE [VERT][V01]: Runtime Hierarchy and Scene Combat Lifecycle

Status: Planned
Owner: Systems DnD5e
Depends on: ISSUE [VERT][V00]

## Why This Exists

This module establishes the scene-first runtime backbone from the target architecture:
Campaign -> Scene with optional combat state.
It must be completed first because later modules depend on stable lifecycle and ownership semantics.

## Scope

In scope:

- Campaign and scene lifecycle transitions.
- Combat start and combat end as scene state transitions (no encounter entity/type).
- Ownership and persistence handoff boundaries for hierarchy state.

Out of scope:

- Detailed action resolution algorithms.

## D2.9 Alignment

- RuntimeHierarchy
- ApplicationLayer (ContextApplicationService)
- RepositoryLayer (SceneRepository)

## High-Level Acceptance Criteria

1. Lifecycle transitions are deterministic and documented.
2. One write authority exists per hierarchy aggregate.
3. Tests cover scene selection and scene combat start/end flows.

## Decomposition Policy

Create child issues only when V01 becomes active.
