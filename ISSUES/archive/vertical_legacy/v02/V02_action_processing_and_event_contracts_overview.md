# V02 Action Processing and Event Contracts Overview

Status: Draft for Planning
Related module issue: ISSUE [VERT][V02]
Related architecture docs:

- V02_combat_actions_detailed_plan.mmd
- V02_combat_actions_planning_overview.md
- V02_action_processing_and_event_contracts_detailed_plan.mmd
- test/README.md
- test/V02_test_seq_01_deterministic_single_attack_baseline.mmd
- test/V02_test_seq_02_reaction_interrupt_window_on_hit.mmd
- test/V02_test_seq_03_pending_choice_pause_resume_smite.mmd
- test/V02_test_seq_04_unlock_mutation_and_followup_action.mmd
- test/V02_test_seq_05_deferred_zone_tick_and_cleanup_lifecycle.mmd

## Why This Document Exists

V02 now treats actions as generic operation graphs instead of single-target command shapes.

This document is the canonical contract for:

1. Multi-operation action processing semantics.
2. Per-operation targeting and effect execution.
3. Event taxonomy and ordering.
4. Concentration, zone, and tick lifecycle representation.
5. Drift recovery and projection resync policy.

## Core Architecture Shift (Mandatory)

Previous assumption:

1. One action had one dominant targeting mode.
2. Effects were secondary by-products.

New mandatory assumption:

1. One action is a container for one or more operations.
2. Each operation has its own targeting mode and payload.
3. Any operation can produce one or more effect outcomes.
4. Operation execution order is explicit and deterministic.

## Generic Action Graph Model

### Action Command Envelope

A command must carry:

1. request_id, campaign_id, scene_id, actor_id, action_id, action_type_cost.
2. operation_specs as a non-empty list.
3. command_context for optional global action metadata.

### Operation Envelope

Each operation must carry:

1. operation_id.
2. operation_kind.
3. effect_ref optional.
4. targeting_mode.
5. target_payload.
6. operation_payload.
7. execution_phase (immediate, deferred, tick).
8. depends_on_operation_ids.

### Design Consequence

Targeting is no longer an action-level singleton.
Targeting is operation-local and can vary inside a single action execution.

## Action Processing Lifecycle (Canonical)

### Stage A: Intake and Validation

1. Validate command envelope.
2. Validate operation list shape.
3. Validate request_id and contract requirements.
4. Deny malformed command before any mutation.

### Stage B: Authorization and Budget

1. Validate actor authority and active turn.
2. Validate action economy window.
3. Reserve budget once for the command.
4. Emit denial terminal event when blocked.

### Stage C: Operation Graph Build

1. Build dependency graph from operation_specs.
2. Validate dependency references and cycles.
3. Produce deterministic linearized execution order.

### Stage D: Per-Operation Target Resolution

1. Resolve targets independently for each operation.
2. Snapshot targets per operation and request_id.
3. Emit operation_targets_resolved or operation_targets_denied.

### Stage E: Per-Operation Execution

1. Execute immediate operations in graph order.
2. Emit operation_resolved or operation_denied.
3. Emit actor-impact and combat outcome events.

### Stage F: Deferred and Tick Scheduling

1. Materialize deferred effects and zones.
2. Register tick operations and removal triggers.
3. Emit effect and zone lifecycle events.

### Stage G: Concentration Lifecycle

1. Start, replace, break, and clear concentration through operation semantics.
2. Emit concentration events as first-class lifecycle events.

### Stage H: Finalization and Projection

1. Emit turn_budget_updated with post-command budget snapshot.
2. Emit terminal result envelope with revision and operation coverage.
3. Persist authoritative state and audit log.

## Canonical Event Taxonomy

### Group 1: Command Events

1. action_authorized
2. action_denied
3. command_denied

### Group 2: Operation Graph Events

1. operation_graph_built
2. operation_planned
3. operation_resolved
4. operation_denied

### Group 3: Targeting Events

1. operation_targets_resolved
2. operation_targets_denied

### Group 4: Combat Outcome Events

1. attack_result
2. save_result
3. actor_damaged
4. actor_healed
5. actor_died
6. actor_moved

### Group 5: Effect Lifecycle Events

1. effect_applied
2. effect_refreshed
3. effect_tick_resolved
4. effect_removed
5. effect_denied

### Group 6: Zone Lifecycle Events

1. zone_created
2. zone_tick_resolved
3. zone_expired
4. zone_removed

### Group 7: Concentration Events

1. concentration_started
2. concentration_replaced
3. concentration_check_required
4. concentration_broken
5. concentration_cleared

### Group 8: Turn and Budget Events

1. turn_advanced
2. turn_budget_updated

### Group 9: Sync and Recovery Events

1. state_sync
2. request_sync
3. projection_resync_required

## Required Event Field Contract

Every command-derived event must include:

1. request_id
2. campaign_id
3. scene_id
4. state_revision
5. event_type

Every operation-derived event must also include:

1. operation_id
2. operation_kind
3. execution_phase

Recommended fields:

1. Actor-impact events include actor_id and source_actor_id where applicable.
2. Effect events include effect_id and effect_instance_id where applicable.
3. Target events include targeting_mode and resolved_target_ids.
4. Denied events include reason_code and denial family.

## Event Ordering Contract

Canonical ordering rules for one command batch:

1. action_authorized before any operation_resolved.
2. operation_graph_built before operation_planned.
3. operation_planned before operation_resolved.
4. operation_targets_resolved before effect_applied for the same operation_id.
5. Operation dependency order must be respected.
6. effect_tick_resolved before effect_removed(expired).
7. concentration_replaced must emit prior removal semantics before new concentration_started.
8. turn_budget_updated must represent post-mutation budget state.
9. Denied commands emit exactly one terminal denial path.

## Visibility and Projection Rules

1. DM receives full payloads.
2. Player receives redacted payloads where required.
3. Spectator follows player-safe subset.
4. Redaction must not change event semantics or ordering.

## Drift Detection and Resync Policy

1. Every command batch increments state_revision.
2. Clients detect revision gaps.
3. Gaps trigger projection_resync_required.
4. Server returns state_sync snapshot.
5. Projection continues from latest revision deterministically.

## Event Coverage Matrix (Planning Checklist)

V02 completeness requires:

1. Every required event is documented, emittable, and tested.
2. Every operation lifecycle event is covered.
3. Concentration chain is fully covered across start, replace, check, break, clear.
4. Zone chain is covered across create, tick, expire, remove.
5. Replay tests prove identical command input gives identical event sequence.

## Test Planning Addendum (Operation-Graph Model)

### Contract Tests

1. test_action_command_requires_operation_specs
2. test_operation_event_requires_operation_id
3. test_event_payload_required_fields
4. test_event_reason_code_machine_readable

### Graph and Ordering Tests

1. test_operation_graph_builds_without_cycles
2. test_operation_dependency_order_respected
3. test_operation_planned_before_execution
4. test_target_resolution_before_effect_application
5. test_tick_before_expiry_removal

### Concentration Tests

1. test_concentration_started_on_operation_apply
2. test_concentration_replaced_emits_remove_then_start
3. test_concentration_check_required_on_damage_trigger
4. test_concentration_broken_emits_effect_removal
5. test_concentration_cleared_on_expiry

### Replay and Resync Tests

1. test_identical_command_replay_identical_event_batch
2. test_revision_gap_triggers_projection_resync_required
3. test_state_sync_restores_projection

### Visibility Tests

1. test_dm_payload_unredacted
2. test_player_payload_redacted_without_semantic_loss
3. test_spectator_payload_policy

## V02 Completion Gate Additions

V02 cannot close until all are true:

1. EventCoverageMatrix: green
2. OperationGraphOrderingTests: green
3. EventParityTests (WS and REST): green
4. ReplayAndResyncTests: green
5. Concentration lifecycle chain: complete and tested
6. Operation-level targeting contract: complete and tested

## Verification Commands (Draft)

1. docker compose --profile test run --rm backend-test pytest tests -k "request_action and operation" -q
2. docker compose --profile test run --rm backend-test pytest tests -k "effect and concentration" -q
3. docker compose --profile test run --rm backend-test pytest tests -k "graph and ordering" -q
4. docker compose --profile test run --rm backend-test pytest tests -k "state_sync and resync" -q
5. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
