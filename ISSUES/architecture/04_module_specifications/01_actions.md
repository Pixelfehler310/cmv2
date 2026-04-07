# Module Annex: actions

## Scope

Action validation, target resolution, budget enforcement, and execution outcome orchestration.

## Primary Classes

1. `ActionDefinition` for immutable action templates.
2. `ActionResolutionRequest` for normalized inbound command payloads.
3. `ActionResolutionContext` for request and turn correlation state.
4. `ActorInstance` for mutable combatant runtime state.
5. `SceneCombatState` for scene combat-state aggregate, phase, and active turn state.
6. `AuthorizationResult` for allow or deny decision payload.
7. `ActionBudgetCheckResult` for action-economy gate outcomes.
8. `AttackResult`, `SaveActionResult`, `HealingResult` for typed outcomes.
9. `CombatService` as orchestration entrypoint for execute and preview.

## Externally Callable Methods (20+)

1. `CombatService.execute_action(...)`
2. `CombatService.get_turn_budget(scene, actor_id)`
3. `CombatService.request_action_preview(...)`
4. `resolve_attack(attacker, target, action_def, ...)`
5. `resolve_save_action(caster, targets, action_def, ...)`
6. `resolve_healing(actor, action_def, ...)`
7. `check_actor_exists(actor_id, actor)`
8. `check_actor_alive(actor)`
9. `check_user_role_allowed(user_role)`
10. `check_actor_ownership(user_role, user_id, actor_owner_user_id)`
11. `check_turn_ownership(action_type, turn_phase, active_actor_id, requesting_actor_id)`
12. `combine_authorization_checks(*results)`
13. `can_spend_action_budget(action_type, action_available, bonus_action_available, reaction_available)`
14. `apply_action_budget_consumption(action_type, budget_state)`
15. `get_or_create_in_memory_budget(turn_budgets, actor_id, max_movement, round_number)`
16. `compute_attack_context(actor)`
17. `compute_save_context(actor, ability)`
18. `apply_damage(target, amount, damage_type)`
19. `add_effect(actor, effect)`
20. `remove_effect(actor, effect_id)`
21. `tick_effects(actor, phase)`

## Method Contract Minimums

1. Every method declares input context object and required fields.
2. Every method declares output envelope or result type.
3. Every denial path maps to stable reason codes.
4. Every state mutation path identifies affected scene combat-state fields.

## Critical Flows

1. Attack action resolution with authorization, budget check, damage apply, and terminal event.
2. Save action resolution for multi-target and AoE templates.
3. Healing action resolution with max-HP cap behavior.
4. Multi-check authorization gate and explicit denied outcomes.
5. Turn budget consume and round reset behavior.
6. Condition and effect influence on advantage, save, and damage outcomes.

Each flow requires resolved, denied, and retry or idempotency notes.

## Context Objects

1. `ActionResolutionContext` with `campaign_id`, `request_id`, `round_number`, `active_actor_id`.
2. `ActionResolutionRequest` with `actor_id`, `action_id`, `action_type_cost`, `target_ids`, `payload`.
3. `AttackContext` or `SaveContext` with advantage-disadvantage and auto-fail attributes.
4. `AreaOfEffect` with shape, radius, origin, affected positions, and resolved actor ids.
5. `SaveRequirement` with ability, DC, on-success, on-fail behavior.

Mutability rules:

1. Resolution request and context are immutable.
2. Combatant and scene combat-state objects are mutable only in service-resolver path.
3. Derived contexts are immutable and recomputed per request.

## Constraints and Denial Mapping

Invariants:

1. Dead actors cannot execute actions.
2. Non-reaction actions must honor active-turn ownership.
3. Action budgets cannot be consumed below availability.
4. Request correlation must survive every emitted event.

Reason-code families:

1. `unauthorized`
2. `not_your_turn`
3. `invalid_action`
4. `invalid_target`
5. `action_exhausted`, `bonus_action_exhausted`, `reaction_exhausted`, `movement_exhausted`
6. `template_out_of_range`, `no_resolved_targets`, `unsupported_action`

## Recovery and Idempotency

1. Same `request_id` replay must not double-consume budget.
2. Preview calls are read-only and replay-safe.
3. Budget reset deterministically follows round boundary.
4. Effect ticks and damage application must be auditable through action logs.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-03]_action_mechanics.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/MASTER_SYSTEM_CLASS_SPEC.mmd` and `ISSUES/architecture/01_contracts/overview/SYSTEM_CRITICAL_FLOWS_SEQUENCE.mmd`.
4. Code anchors: `backend/src/systems/dnd5e/services/combat_service.py`, `backend/src/systems/dnd5e/domain/authorization.py`, `backend/src/systems/dnd5e/domain/action_economy.py`, `backend/src/systems/dnd5e/engine/action_resolver.py`.
