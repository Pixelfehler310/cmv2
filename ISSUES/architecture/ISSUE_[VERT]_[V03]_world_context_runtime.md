# ISSUE [VERT][V03]: World Context Runtime

Status: Planned
Owner: Systems + Campaigns
Depends on: ISSUE [VERT][V01]

## Why This Exists

World context is first-class runtime state in the target architecture.
This module keeps regions, places, factions, and NPCs as a coherent domain with explicit invariants.

## Scope

In scope:

- Region, place, faction, and NPC state contracts.
- Relationship invariants and campaign ownership rules.
- Repository and service flow for world context runtime data.

Out of scope:

- Combat action resolution internals.

## D2.9 Alignment

- WorldContextRuntime
- ApplicationLayer (WorldContextApplicationService)
- RepositoryLayer (WorldContextRepository)
- PersistenceDnd5e (RegionRecord, PlaceRecord, NpcRecord, FactionRecord)

## High-Level Acceptance Criteria

1. Context entities have explicit ownership and invariants.
2. Relationship constraints are validated and test-covered.
3. Contracts are consumable by frontend without ad-hoc transforms.

## Decomposition Policy

Create child issues only when V03 becomes active.
