# Module Annex: recovery

## Scope

Drift detection, projection restoration, checkpoint policy, and replay semantics.

## Primary Classes

1. `DriftDetector` for divergence and staleness analysis.
2. `ProjectionRestorer` for snapshot and replay-based projection rebuild.
3. `CheckpointManager` for checkpoint creation, validation, and retention.
4. `ReplayProcessor` for deterministic event-range replay.
5. `RecoveryOrchestrator` for path selection and recovery workflow coordination.
6. `RecoveryStateStore` for status tracking and audit records.

## Externally Callable Methods (10+)

1. `analyze_state_divergence(projection_id, projection_scope, current_revision, db_session)`
2. `detect_projection_staleness(projection_id, last_sync_timestamp, db_session)`
3. `compute_revision_gap(current_revision, persisted_revision)`
4. `restore_projection_from_snapshot(snapshot_id, db_session, projection_scope)`
5. `restore_projection_via_replay(starting_checkpoint_id, event_filter, db_session)`
6. `verify_restored_state(restored_projection, expected_revision, expected_checksum)`
7. `invalidate_stale_projection(projection_id, reason, db_session)`
8. `create_checkpoint(projection_id, projection_state, checkpoint_metadata, db_session)`
9. `mark_checkpoint_verified(checkpoint_id, verification_checksum, db_session)`
10. `get_latest_verified_checkpoint(projection_id, db_session)`
11. `prune_old_checkpoints(projection_id, retention_count, db_session)`
12. `replay_events_since(starting_checkpoint_id, current_projection_state, db_session)`
13. `batch_replay_events(events, initial_state, operation_context)`
14. `verify_replay_consistency(replay_result, expected_final_revision, expected_checksum)`
15. `execute_recovery(recovery_request, db_session)`
16. `decide_recovery_path(drift_report, staleness_report)`
17. `trigger_recovery_via_checkpoint(checkpoint_id, projection_id, db_session)`
18. `cancel_recovery(recovery_id)`
19. `log_recovery_attempt(recovery_request, status, metadata, db_session)`
20. `get_recovery_status(recovery_id, db_session)`

## Critical Flows

1. Drift detection and recovery-path decision flow.
2. Snapshot-based projection restore flow.
3. Checkpoint plus replay restoration flow.
4. Recovery execution lifecycle with status tracking and cancellation.

## Context Objects

1. `RecoveryRequest` with projection id, scope, trigger reason, revision, correlation id.
2. `DriftReport` with divergence category and suggested action.
3. `CheckpointMetadata` with event counts, revision and checksum.
4. `OperationContext` for replay schema and correlation scope.
5. `RecoveryOutcome` with final state and metrics.

Mutability:

1. Requests and reports are immutable.
2. State store entries mutate status across lifecycle steps.
3. Projection restore outputs are immutable snapshots once verified.

## Constraints and Denial Mapping

Invariants:

1. Verified state required before accepting restored projection.
2. Event replay ordering must be strict and deterministic.
3. Checkpoint retention preserves latest verified checkpoints.
4. Recovery workflows cannot run concurrently for same projection id.

Reason-code families:

1. `projection_not_found`
2. `revision_unknown`
3. `checkpoint_not_found`
4. `replay_determinism_violation`
5. `checksum_mismatch`
6. `unrecoverable_corruption`
7. `recovery_timeout`

## Recovery and Idempotency

1. Recovery requests should be deduplicated by recovery id and projection id.
2. Snapshot restoration is replay-safe for same snapshot id.
3. Replay execution is pure and deterministic for same event range.
4. Completed recoveries must be auditable via correlation ids and final checksums.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-03]_query_projection_consistency.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/SYSTEM_CRITICAL_FLOWS_ACTIVITY.mmd`.
4. System info anchor: `ISSUES/architecture/system_info/architecture/CORE_03_recovery_policy.md`.
