# Feature Description: campaigns

## Goal

Define campaign identity, membership, and context selection as explicit policy-driven operations.

## Core Features

1. Campaign membership and role gates for all scoped operations.
2. DM-only context switching for scene and combat-state selection.
3. Cross-campaign mutation denial semantics.
4. Deterministic context-version updates for synchronization.

## User Outcomes

1. Access control is explicit and predictable.
2. Campaign orchestration stays bounded and safe.
3. Context changes propagate consistently across modules.
