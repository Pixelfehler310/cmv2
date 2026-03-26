# V02 Action Processing and Event Contracts Overview

Status: Draft for Planning
Related module issue: ISSUE [VERT][V02]
Related architecture docs:

- V02_combat_actions_detailed_plan.mmd
- V02_combat_actions_planning_overview.md
- V02_action_processing_and_event_contracts_detailed_plan.mmd

## Why This Document Exists

V02 already defines combat action architecture, but event completeness needs a dedicated contract artifact.

This document is the canonical checklist for:

1. Which events must exist for action processing.
2. What each event must contain.
3. How events must be ordered.
4. How concentration and effect lifecycle transitions must be represented.
5. How to detect and recover projection drift.

## Design Decision

Primary transport model for V02:

1. Event-first command output (granular domain events).
2. Authoritative backend encounter state persisted each command.
3. Snapshot sync for connect/resync/recovery, not per-action full-state push.

Rationale:

1. Event streams are human-readable for logs and debugging.
2. Event streams support deterministic replay and contract testing.
3. Full-state-only per action is noisy and hides intent semantics.

## Action Processing Lifecycle (Canonical)

### Stage A: Command Intake

1. Validate command envelope shape.
2. Require request_id for command-class events.
3. Reject malformed payloads before any state mutation.

### Stage B: Authorization and Budget Gate

1. Validate actor existence and ownership.
2. Validate active-turn authority and alive-state.
3. Validate action economy spend availability.
4. Emit denial terminal event on failure.

### Stage C: Target Resolution

1. Resolve explicit, area, self, or derived targets.
2. Validate range/line-of-effect/template constraints.
3. Build deterministic target snapshot bound to request_id.
4. Emit targets_resolved or targets_denied.

### Stage D: Outcome Planning

1. Split immediate outcomes from deferred outcomes.
2. Define deterministic execution ordering.
3. Reserve budget spend exactly once.

### Stage E: Immediate Outcome Execution

1. Emit attack_result or save_result when applicable.
2. Emit actor_damaged and actor_healed as needed.
3. Emit actor_died where state transition crosses death threshold.
4. Emit actor_moved where movement side effects occur.

### Stage F: Deferred Effect and Zone Execution

1. Apply or refresh effect instances.
2. Create zone instances for area persistence.
3. Emit effect and zone lifecycle events.

### Stage G: Concentration Lifecycle

1. Emit concentration_started when concentration begins.
2. Emit concentration_replaced when previous concentration is superseded.
3. Emit concentration_check_required on damage-triggered checks.
4. Emit concentration_broken when concentration fails.
5. Emit concentration_cleared when effect expires or is removed.

### Stage H: Finalization and Projection

1. Emit turn_budget_updated when budget-affecting action completes.
2. Emit terminal action result envelope semantics (resolved or denied).
3. Persist state checkpoint and audit log.
4. Attach state_revision and request correlation metadata.

## Canonical Event Taxonomy

The following groups are mandatory for V02 event completeness.

### Group 1: Command Events

1. action_authorized
2. action_denied
3. command_denied

### Group 2: Targeting Events

1. targets_resolved
2. targets_denied

### Group 3: Combat Outcome Events

1. attack_result
2. save_result
3. actor_damaged
4. actor_healed
5. actor_died
6. actor_moved

### Group 4: Effect Lifecycle Events

1. effect_applied
2. effect_refreshed
3. effect_tick_resolved
4. effect_removed
5. effect_denied

### Group 5: Zone Lifecycle Events

1. zone_created
2. zone_tick_resolved
3. zone_expired
4. zone_removed

### Group 6: Concentration Events

1. concentration_started
2. concentration_replaced
3. concentration_check_required
4. concentration_broken
5. concentration_cleared

### Group 7: Turn and Budget Events

1. turn_advanced
2. turn_budget_updated

### Group 8: Sync and Recovery Events

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

Recommended required fields by event family:

1. Actor-impact events include actor_id and source_actor_id where applicable.
2. Effect events include effect_id and effect_instance_id where applicable.
3. Target events include target_mode and resolved_target_ids.
4. Denied events include reason_code and machine-readable denial family.

## Event Ordering Contract

Canonical ordering rules for a single command batch:

1. action_authorized must appear before any success outcome events.
2. targets_resolved must appear before effect_applied or zone_created.
3. effect_tick_resolved must appear before effect_removed(expired).
4. concentration_replaced must include removal semantics before new concentration_started.
5. turn_budget_updated must represent post-mutation budget snapshot.
6. Terminal denied events must be the only terminal outcome for denied commands.

## Visibility and Projection Rules

1. DM projection receives full event payloads.
2. Player projection applies redaction policy where needed.
3. Spectator projection follows player-safe subset.
4. Visibility filtering must not alter event semantic meaning.

## Drift Detection and Resync Policy

1. Every command batch increments state_revision.
2. Clients detect revision gaps.
3. Gaps trigger projection_resync_required.
4. Server responds with state_sync snapshot.
5. Resync must preserve deterministic continuation from latest revision.

## Event Coverage Matrix (Planning Checklist)

Use this as the V02 completeness audit matrix.

1. Each canonical event has: producer stage, payload contract, ordering assertions, visibility policy, and test coverage.
2. Each denial reason is mapped to at least one deterministic test.
3. Concentration event chain is fully covered across start, replace, check, break, and clear.
4. Zone event chain is covered across create, tick, expire, and remove.
5. Replay tests confirm identical inputs produce identical event sequence and reason codes.

## Test Planning Addendum (Event Contracts and Action Processing)

### Contract Tests

1. test_event_payload_required_fields
2. test_event_reason_code_machine_readable
3. test_event_family_contract_stability

### Ordering Tests

1. test_action_authorized_precedes_outcome_events
2. test_target_resolution_precedes_effect_events
3. test_tick_precedes_expiry_removal

### Concentration Tests

1. test_concentration_started_on_concentration_effect_apply
2. test_concentration_replaced_emits_remove_then_start
3. test_concentration_check_required_emitted_on_damage_trigger
4. test_concentration_broken_emits_effect_removal
5. test_concentration_cleared_on_expiry

### Resync and Replay Tests

1. test_revision_gap_triggers_projection_resync_required
2. test_state_sync_restores_projection
3. test_identical_command_replay_identical_event_batch

### Visibility Tests

1. test_dm_payload_unredacted
2. test_player_payload_redacted_without_semantic_loss
3. test_spectator_payload_policy

## V02 Completion Gate Additions

V02 cannot close until all are true:

1. EventCoverageMatrix: green
2. EventOrderingTests: green
3. EventParityTests (WS and REST): green
4. ReplayAndResyncTests: green
5. Concentration lifecycle event chain: complete and tested

## Verification Commands (Draft)

1. docker compose --profile test run --rm backend-test pytest tests -k "request_action and event" -q
2. docker compose --profile test run --rm backend-test pytest tests -k "effect and concentration" -q
3. docker compose --profile test run --rm backend-test pytest tests -k "ordering and replay" -q
4. docker compose --profile test run --rm backend-test pytest tests -k "state_sync and resync" -q
5. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
