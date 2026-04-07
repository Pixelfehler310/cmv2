# Feature Description: sheets

## Goal

Generate deterministic character-sheet projections with strict reference resolution and recovery behavior.

## Core Features

1. Projection pipeline with revision and status metadata.
2. Reference resolver with explicit unresolved denial states.
3. Mutation-driven invalidation and re-projection scheduling.
4. Visibility-aware sheet output filtering.

## User Outcomes

1. Sheet state is reliable and explainable.
2. Broken references are explicit, not silent.
3. Recovery from invalidation is controlled and auditable.
