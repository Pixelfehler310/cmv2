# ISSUE [ARCH][D01]: Runtime Hierarchy and Encounter Lifecycle

Status: Planned
Owner: Systems DnD5e
Depends on: ISSUE [ARCH][D00]

## Why This Exists

D2.9 defines Campaign -> Scene -> optional active Encounter as the runtime backbone.
This stream captures all lifecycle and ownership work around that hierarchy.

## Scope

In scope:

- Campaign/scene/encounter state transitions.
- Encounter activation/deactivation and phase progression.
- Runtime ownership and persistence handoff points for hierarchy nodes.

Out of scope:

- Detailed action resolution semantics.

## Related D2.9 Namespaces

- RuntimeHierarchy
- ApplicationLayer (ContextApplicationService)
- RepositoryLayer (SceneRepository, EncounterRepository)

## Acceptance Criteria

1. Lifecycle transitions are explicit and deterministic.
2. One write authority exists per hierarchy aggregate.
3. Tests cover enter/leave encounter and scene selection flows.
