# ISSUE [ARCH][D00]: DnD Domain Stream Map (Derived from D2.9)

Status: Planned
Owner: Architecture
Depends on: ISSUE [ARCH][M00]

## Why This Exists

The Mxx modules are cross-cutting and useful for boundaries, but they are too generic for day-to-day DnD feature work.
This issue introduces domain streams based on the target diagram so implementation can proceed by business capability with fewer cross-module edits.

## Source of Truth

- docs/diagrams/mmd/D2.9_target_corrected_architecture.mmd

## Domain Streams

1. D01 Runtime Hierarchy and Encounter Lifecycle.
2. D02 Combat Actions, Turn Economy, and Effects.
3. D03 World Context Runtime (regions, places, factions, npcs).
4. D04 Content Schema and Content Pack Lifecycle.
5. D05 Compendium CRUD and Definition Catalog.
6. D06 Event Contracts and Frontend Projection Feed.

## How Streams and Modules Work Together

1. Dxx stream = what business capability is being changed.
2. Mxx module = which technical boundary is being hardened.
3. Every architecture change should reference one primary Dxx and one primary Mxx.

## Acceptance Criteria

1. All Dxx stream issues exist and are linked from this issue.
2. New architecture tasks use Dxx plus Mxx tagging.
3. Cross-module churn is reduced by stream-local implementation planning.
