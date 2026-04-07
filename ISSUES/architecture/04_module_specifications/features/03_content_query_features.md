# Feature Description: content_query

## Goal

Deliver deterministic, revision-aware read models for compendium and sheet consumers.

## Core Features

1. Stable ordering and pagination behavior.
2. Detail hydration with link expansion safeguards.
3. Revision gap detection with explicit invalidation semantics.
4. Read-model cache invalidation aligned to mutation events.

## User Outcomes

1. Queries are predictable for UI and tests.
2. Stale data states are detectable and recoverable.
3. Hydrated references remain consistent across views.
