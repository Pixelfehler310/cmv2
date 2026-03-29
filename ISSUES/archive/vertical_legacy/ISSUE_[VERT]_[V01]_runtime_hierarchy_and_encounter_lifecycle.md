# ISSUE [VERT][V01]: Runtime Hierarchy and Scene Combat Lifecycle

Status: Active Planning
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

V01 is the current active module and deep child issues are enabled.

## Child Issue Plan (Sequenced)

1. ISSUE [VERT][V01-01]: Baseline and Drift Audit.
2. ISSUE [VERT][V01-02]: Lifecycle Contract Freeze.
3. ISSUE [VERT][V01-03]: Ownership and Repository Boundary Lock.
4. ISSUE [VERT][V01-04]: Application Transition Orchestration.
5. ISSUE [VERT][V01-05]: WS and REST Interface Convergence.
6. ISSUE [VERT][V01-06]: Test Matrix and Completion Gate.

Execution rule:

- Complete each issue in sequence unless a dependency exception is explicitly documented.

Module completion rule:

- V01 can only close when V01-06 gate passes and V00 module DoD is satisfied.
