# CORE-03 Recovery Policy: Query and Projection Consistency

## Purpose

Define the deterministic recovery behavior when clients detect revision gaps or stale projections for DND5E content queries.

## Inputs

1. `current_revision`: revision currently applied by the consumer.
2. `incoming_revision`: revision announced by event/result envelope.
3. `scope_id`: projection scope key (for example family filter, pack filter, or character-sheet context).
4. `last_successful_sync_at`: timestamp of last confirmed synchronized projection.

## Recovery Decision Rules

1. If `incoming_revision == current_revision`, no recovery action is required.
2. If `incoming_revision == current_revision + 1`, apply targeted update for the affected scope.
3. If `incoming_revision > current_revision + 1`, invalidate projection scope and start full resync.
4. If `incoming_revision < current_revision`, ignore event and log stale event detection.
5. If `incoming_revision` cannot be parsed, deny update and emit `command_denied` with a recovery reason code.

## Recovery Paths

### Path A: Targeted Refetch

Use when a single revision step is available and `affected_definition_ids` are present.

1. Fetch definitions by `affected_definition_ids` at `incoming_revision`.
2. Rebuild only impacted projection rows.
3. Confirm local projection revision equals `incoming_revision`.

### Path B: Full Resync

Use when revision gaps exceed one step or affected scope is ambiguous.

1. Mark projection scope as invalidated.
2. Request full snapshot for scope at latest catalog revision.
3. Replace local scope projection atomically.
4. Publish `content_projection_updated` with synchronized revision.

## Convergence Expectations

1. Targeted refetch should converge within one processing cycle after fetch success.
2. Full resync should converge within bounded retries with deterministic backoff.
3. Any failure beyond retry budget must surface an explicit denial/error envelope.

## Required Envelope Fields

1. `request_id`
2. `catalog_revision`
3. `status`
4. `reason_code` for denied/error
5. `affected_definition_ids` for targeted updates

## Cross-Contract Links

1. CORE-03 (`query_projection_consistency`) owns snapshot and revision semantics.
2. CORE-04 (`session_event_envelopes`) owns transport-visible event envelope shape.
3. DND5E-04 (`content_query_projection`) owns DND5E-specific projection consumer behavior.
