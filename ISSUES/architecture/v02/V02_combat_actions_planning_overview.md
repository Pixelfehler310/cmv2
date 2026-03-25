# V02 Planning Overview: Combat Actions, Turn Economy, and Effects

Status: Draft for Planning
Related module issue: ISSUE [VERT][V02]
Related playbook: docs/architecture/shared/05_vertical_module_execution_plan.md
Related diagram: V02_combat_actions_detailed_plan.mmd

Detailed issue set (proposed for activation window):

- ISSUE [VERT][V02-01] action_contract_and_denied_taxonomy_freeze
- ISSUE [VERT][V02-02] turn_budget_ownership_and_spend_rules
- ISSUE [VERT][V02-03] target_resolution_and_snapshot_contract_lock
- ISSUE [VERT][V02-04] application_orchestration_for_action_execution
- ISSUE [VERT][V02-05] ws_rest_contract_convergence_for_combat_actions
- ISSUE [VERT][V02-06] effect_lifecycle_zone_tick_and_concentration_policy_lock
- ISSUE [VERT][V02-07] action_execution_tests_matrix_and_completion_gate

## What V02 Is Trying to Achieve

V02 stabilizes the combat execution core after V01 lifecycle authority is in place.
It makes action resolution, turn budget spending, and effect lifecycle semantics deterministic and machine-readable.

## Why V02 Follows V01

1. V02 relies on V01 scene and combat lifecycle invariants to define legal action windows.
2. Action and effect correctness cannot be made reliable while scene and combat ownership are ambiguous.
3. A stable deny taxonomy in V02 reduces projection drift in V06 and frontend state handling.

## Boundaries of V02

In scope:

1. Action execution request and outcome contracts.
2. Target resolution contracts for explicit targets, area targets, and derived targets.
3. Turn economy budget ownership and spend semantics.
3. Effect apply, tick, concentration, expire, and removal semantics.
4. Zone effect lifecycle semantics for area-based persistent effects.
5. Stable deny reason-code taxonomy for combat action and effect transitions.
6. WS and REST parity for combat action execution paths.

Out of scope:

1. Compendium CRUD breadth and content authoring workflows.
2. New frontend gameplay features beyond contract consumption.
3. Non-combat world context runtime deepening (covered by V03).

## Core Ownership Decisions to Lock

1. Single-writer ownership for turn budget mutation.
2. Single authoritative path for action execution and outcome creation.
3. Single authoritative path for effect state transitions.
4. Concentration ownership and interruption semantics.
5. Event mapping ownership for combat action/effect events.
6. Deterministic target snapshot ownership for each execute-action request.

## Target Runtime and Service Structure

Domain runtime targets:

1. Combat encounter runtime with active actor and round state.
2. Actor runtime with concentration and reaction state.
3. Turn budget runtime per actor-turn.
4. Effect instance runtime with explicit lifecycle state and reason codes.
5. Target snapshot runtime state per action request.
6. Zone effect runtime state for persistent area effects.

Application targets:

1. ActionExecutionApplicationService orchestrates command handling.
2. Service enforces deterministic read-validate-mutate-map flow.
3. Service returns stable result envelopes for WS and REST mappers.
4. Service handles multi-result actions through a result planning stage (immediate plus deferred outcomes).

Policy targets:

1. Authorization policy for action and turn-level commands.
2. Turn economy policy for budget and reaction gating.
3. Target resolution policy for area and explicit target determination.
4. Effect lifecycle policy for apply/tick/remove/concentration decisions.

## Detailed Execute-Action Pipeline (Target Flow and Multi-Result Outcomes)

The execute-action path should be explicit and deterministic. It is the orchestration entrypoint, but not the place where all rule semantics are hardcoded inline.

### Step A: Request Intake and Authorization

1. Validate transport contract fields and request correlation id.
2. Authorize actor command rights.
3. Validate turn window and spend availability.

Expected denied examples:

- not_active_actor
- insufficient_budget
- reaction_window_closed

### Step B: Target Resolution

1. Resolve target mode: explicit, area, self, or derived.
2. Validate geometry/range/line-of-effect constraints for area requests.
3. Produce a deterministic target snapshot object bound to request_id.

Expected denied examples:

- invalid_target_spec
- target_out_of_range
- blocked_line_of_effect
- no_valid_targets

### Step C: Action Result Planning

1. Build an ActionResultPlan that separates immediate outcomes from deferred outcomes.
2. Immediate outcomes can include direct damage/heal and immediate conditions.
3. Deferred outcomes include persistent effects and zone-effect instances.
4. Define deterministic execution ordering in the plan.

### Step D: Immediate Application

1. Spend budget exactly once.
2. Apply immediate outcomes in planned order.
3. Persist actor and encounter deltas.

### Step E: Deferred Materialization

1. Create effect instances and zone instances.
2. Attach concentration ownership if required.
3. Emit lifecycle events for created runtime artifacts.

### Step F: Tick-Time Runtime Processing

1. Before each tick, recompute zone occupancy.
2. Apply per-tick and threshold rules in deterministic actor order.
3. For remain-in-zone policies, track entry turn and full-turn thresholds.
4. Expire/remove instances using canonical reason codes.

### Step G: Result Mapping

1. Return one stable result envelope.
2. Emit stable event sequence with request_id correlation.
3. Keep mapper logic translation-only (no gameplay decisions).

## Multi-Result Action Example (Smoke Zone)

Example behavior to support in V02:

1. Action creates a smoke zone in an area.
2. Action applies immediate damage to occupants in initial target snapshot.
3. Zone persists for N turns as a runtime instance.
4. Each tick recomputes occupants and applies either:
   - delayed sleep after full-turn remain threshold, or
   - periodic tick damage.
5. Zone expires or is removed (expiry, concentration break, dispel, overwrite).

This behavior should be represented as one execute-action command with multiple planned outcomes, not multiple ad-hoc command paths.

## Phase Plan for V02 (Using the Playbook)

### P0 Alignment and Baseline

1. Confirm current action execution paths and where budget/effects mutate today.
2. Confirm existing denied reasons and event payload variants.
3. Capture baseline deterministic and non-deterministic scenarios.

Exit signal:

- Team agrees on exact V02 scope, risk list, and baseline behavior matrix.

### P1 Contract and Denied Taxonomy Freeze

1. Define execute-action contract inputs and outputs.
2. Define target-resolution contract payloads and snapshot shape.
3. Define deny reason-code taxonomy with stable machine-readable values.
4. Freeze event payload requirements for action, targets, zones, budget, and effect lifecycle events.

Exit signal:

- Action contracts and denied taxonomy are stable enough for implementation.

### P2 Ownership and Persistence Boundaries

1. Map all budget fields to one write authority.
2. Map all effect lifecycle transitions to one write authority.
3. Remove or flag ambiguous mutation paths.

Exit signal:

- No unresolved multi-writer state for budget or effects.

### P3 Policy Consolidation

1. Implement turn economy policy with explicit spend and reaction rules.
2. Implement target resolution policy with explicit area/derived semantics.
3. Implement effect lifecycle policy with concentration, stacking, and zone tick behavior.
4. Verify invariant coverage for budget/target/effect transitions.

Exit signal:

- Policy layer is complete for target V02 scenarios with stable reason codes.

### P4 Application Orchestration

1. Route action execution through one application orchestration path.
2. Ensure deterministic sequencing: authorize -> validate -> mutate -> map.
3. Ensure result envelope consistency for both success and denied outcomes.

Exit signal:

- Service behavior matches P1 contracts in core combat scenarios.

### P5 Transport and Interface Convergence

1. Align WS and REST handlers to the same action execution contracts.
2. Ensure request_id correlation and deterministic event emission.
3. Validate mappers emit only stable contract fields.

Exit signal:

- WS and REST flows are behaviorally aligned and deterministic.

### P6 Test Matrix and Determinism Hardening

1. Contract tests for execute-action, targets-resolved, zone lifecycle, and deny taxonomy.
2. ActionExecutionTests suite for multi-result action orchestration behavior.
3. Invariant tests for budget spend, reaction windows, target snapshot stability, concentration, and lifecycle order.
4. Integration tests for action->target->effect->zone flows across rounds and transport paths.
5. Replay tests for deterministic outcomes under identical inputs.

Exit signal:

- Required V02 suites are deterministic and green.

### P7 Closure and Handoff

1. Summarize completed V02 scope and residual risks.
2. Create focused follow-up issues for deferred combat work only.
3. Hand off resulting constraints to V03 and V06 planning streams.

Exit signal:

- V02 closure criteria are met and handoff constraints are explicit.

## Recommended Initial Child-Issue Cut (When V02 Is Activated)

1. V02-01 Action Contract and Denied Taxonomy Freeze.
2. V02-02 Turn Budget Ownership and Spend Rules.
3. V02-03 Target Resolution and Snapshot Contract Lock.
4. V02-04 Application Orchestration for Action Execution.
5. V02-05 WS and REST Contract Convergence for Combat Actions.
6. V02-06 Effect Lifecycle, Zone Tick Semantics, and Concentration Policy Lock.
7. V02-07 ActionExecutionTests Matrix and Completion Gate.

## Detailed Test Planning: ActionExecutionTests

The ActionExecutionTests suite should be planned as a first-class module gate, not a small add-on. Its purpose is to validate end-to-end orchestration semantics at service level with deterministic replay.

### A. Execute-Action Contract and Shape Tests

1. accepted_minimal_action_returns_stable_shape
2. denied_action_returns_machine_readable_reason
3. execute_action_response_contains_spent_budget_and_effect_refs
4. execute_action_response_preserves_request_id_correlation

### B. Target Flow Tests

1. explicit_targets_resolve_in_stable_actor_order
2. area_targets_resolve_with_expected_geometry_rules
3. derived_targets_resolve_from_context_without_transport_side_logic
4. target_snapshot_is_stable_for_same_request_replay
5. invalid_target_spec_denies_before_mutation

### C. Multi-Result Planning Tests

1. action_with_immediate_damage_and_zone_creation_generates_two_result_phases
2. result_plan_order_is_deterministic_for_same_input
3. budget_is_spent_once_even_with_multiple_results
4. partial_result_application_is_not_allowed_on_denied_paths

### D. Zone Lifecycle and Tick Tests

1. zone_created_event_emitted_on_materialization
2. zone_occupancy_recomputed_before_tick_effects
3. remain_in_zone_for_full_turn_triggers_delayed_sleep
4. tick_damage_applies_only_to_current_occupants
5. zone_expires_with_canonical_reason_code

### E. Concentration Interaction Tests

1. concentration_break_removes_linked_zone_effects
2. concentration_switch_replaces_prior_concentration_effect
3. concentration_drop_reason_propagates_to_lifecycle_event

### F. Determinism and Replay Tests

1. identical_inputs_identical_outputs_and_event_order
2. actor_iteration_order_stable_during_area_tick
3. denied_reason_stable_for_same_invalid_input
4. cross-transport parity_ws_vs_rest_same_semantics

### G. Negative and Edge-Case Tests

1. no_valid_targets_denies_without_budget_spend
2. target_out_of_range_denies_without_side_effects
3. blocked_line_of_effect_denies_without_zone_creation
4. overlapping_zones_apply_policy_defined_resolution_order
5. zone_and_effect_expire_in_same_tick_follow_defined_order

### H. Completion Criteria for ActionExecutionTests

1. All critical behavior families above have passing deterministic tests.
2. At least one canonical smoke-style scenario is covered in ws and rest integrations.
3. Flakiness rate remains zero across repeated seeded runs.
4. All denied paths prove no unauthorized mutation side effects.

Planning status:

- Target architecture now includes explicit target flow and zone lifecycle planning.
- Test strategy now includes dedicated ActionExecutionTests planning as a primary completion gate.
- Next step is activation of V02 in the V00 board, then decomposition into child issues.

## Verification Commands (Draft)

1. docker compose --profile test run --rm backend-test pytest tests -k "combat and action" -q
2. docker compose --profile test run --rm backend-test pytest tests -k "action and target" -q
3. docker compose --profile test run --rm backend-test pytest tests -k "effect and zone" -q
4. docker compose --profile test run --rm backend-test pytest tests -k "deterministic and replay" -q
5. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
6. docker compose logs backend --tail=200
