# ISSUE [ARCH][D03]: World Context Runtime (Regions, Places, Factions, NPCs)

Status: Planned
Owner: Systems + Campaigns
Depends on: ISSUE [ARCH][D00]

## Why This Exists

World context is now first-class runtime state in D2.9.
This stream ensures context entities evolve as a coherent domain, not as incidental JSON payloads.

## Scope

In scope:

- Region/place/faction/npc state contracts.
- CRUD and relationship invariants.
- Scene linkage and campaign ownership constraints.

Out of scope:

- Combat resolution internals.

## Related D2.9 Namespaces

- WorldContextRuntime
- ApplicationLayer (WorldContextApplicationService)
- RepositoryLayer (WorldContextRepository)
- PersistenceDnd5e (RegionRecord, PlaceRecord, NpcRecord, FactionRecord)

## Acceptance Criteria

1. Context entities have explicit ownership and invariants.
2. Relationship constraints are validated and test-covered.
3. Contracts are consumable by frontend without ad-hoc transformations.
