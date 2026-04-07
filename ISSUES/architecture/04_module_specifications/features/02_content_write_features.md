# Feature Description: content_write

## Goal

Safely mutate compendium content with lifecycle, integrity, and revision guarantees.

## Core Features

1. Draft-first create and update flows with optimistic locking.
2. Publish and supersede paths guarded by dependency validation.
3. Referential integrity protection for required links.
4. Mutation event emission for downstream invalidation and projection updates.

## User Outcomes

1. Content changes are version-safe and traceable.
2. Invalid dependency states are blocked early.
3. Publish pipeline remains deterministic and auditable.
