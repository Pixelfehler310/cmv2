# WS Event Refactor Acceptance Matrix

This matrix defines acceptance tests for each event family in the backend-first refactor.

Companion plan: [docs/architecture/backend/14_ws_event_refactor_backend_phase_plan.md](docs/architecture/backend/14_ws_event_refactor_backend_phase_plan.md)
Baseline reference: [docs/architecture/backend/13_ws_event_system_baseline_as_built.md](docs/architecture/backend/13_ws_event_system_baseline_as_built.md)

## 1. Test Convention

Each test row follows:

- Preconditions
- Command
- Expected outbound sequence
- Expected state mutation
- Expected denial/error behavior

Use deterministic fixtures and explicit `request_id` in all command tests.

## 2. Core Lifecycle Family

| ID   | Event          | Scenario                            | Expected outbound                    | Expected state                               |
| ---- | -------------- | ----------------------------------- | ------------------------------------ | -------------------------------------------- |
| L-01 | `start_combat` | valid encounter with >=1 combatant  | `combat_started`                     | `turn_phase=active`, round/index initialized |
| L-02 | `start_combat` | no combatants                       | `error` (`invalid_action`)           | no mutation                                  |
| L-03 | `end_turn`     | active phase and valid active actor | `turn_advanced`                      | next active actor, round advanced on wrap    |
| L-04 | `end_turn`     | phase not active                    | explicit denied/error (never silent) | no mutation                                  |
| L-05 | `end_combat`   | active combat                       | `combat_ended`                       | phase post-combat, round/index reset         |

## 3. Movement Family

| ID   | Event        | Scenario                                   | Expected outbound             | Expected state                 |
| ---- | ------------ | ------------------------------------------ | ----------------------------- | ------------------------------ |
| M-01 | `move_token` | active actor moves within remaining budget | `actor_moved`                 | actor + token position updated |
| M-02 | `move_token` | non-active actor attempts move             | denied (`not_your_turn`)      | no position change             |
| M-03 | `move_token` | player moves non-owned actor               | denied (`unauthorized`)       | no position change             |
| M-04 | `move_token` | path exceeds budget                        | denied (`resource_exhausted`) | no position change             |
| M-05 | `move_token` | out-of-bounds path                         | `error` (`invalid_action`)    | no position change             |
| M-06 | `move_token` | empty path                                 | `error` (`invalid_message`)   | no position change             |

Acceptance requirement:

- M-02/M-03/M-04 must pass in every runtime mode (no in-memory bypass).

Stage B lifecycle additions:

| ID   | Event                  | Scenario                                         | Expected outbound                          | Expected state                                            |
| ---- | ---------------------- | ------------------------------------------------ | ------------------------------------------ | --------------------------------------------------------- |
| M-07 | `request_move_preview` | active actor requests movement highlight preview | `movement_preview` with non-empty envelope | no mutation (preview-only); reachable derived server-side |
| M-08 | `request_move_preview` | actor is not active / unauthorized               | `command_denied` deterministic reason code | no mutation                                               |
| M-09 | `request_move_preview` | malformed payload                                | `error` (`invalid_message`)                | no mutation                                               |

## 4. Action Authorization and Economy Family

| ID   | Event            | Scenario                                            | Expected outbound                      | Expected state           |
| ---- | ---------------- | --------------------------------------------------- | -------------------------------------- | ------------------------ |
| A-01 | `action`         | active actor with available action                  | success terminal event                 | action budget consumed   |
| A-02 | `request_action` | active actor with available bonus action            | success terminal event                 | bonus budget consumed    |
| A-03 | `action`         | action already spent                                | `action_denied` (`resource_exhausted`) | no further budget change |
| A-04 | `request_action` | dead actor attempts action                          | `action_denied` (`invalid_action`)     | no mutation              |
| A-05 | `action`         | player on non-owned actor                           | `action_denied` (`unauthorized`)       | no mutation              |
| A-06 | `action`         | non-active actor uses non-reaction action           | `action_denied` (`not_your_turn`)      | no mutation              |
| A-07 | `action`         | reaction while non-active but valid trigger context | success terminal event                 | reaction consumed        |

Stage A lifecycle additions:

| ID   | Event                         | Scenario                                        | Expected outbound                                  | Expected state                    |
| ---- | ----------------------------- | ----------------------------------------------- | -------------------------------------------------- | --------------------------------- |
| A-08 | `request_executable_actions`  | active actor requests action deck snapshot      | `executable_actions_snapshot`                      | no mutation (projection-only)     |
| A-09 | `request_executable_actions`  | non-owner or turn-ineligible actor request      | `command_denied` deterministic reason code         | no mutation                       |
| A-10 | `request_executable_actions`  | malformed payload                               | `error` (`invalid_message`)                        | no mutation                       |
| A-11 | `executable_actions_snapshot` | snapshot includes backend-computed availability | payload has `actions[]` and optional `turn_budget` | frontend can render without rules |

## 5. Action Resolution Family

| ID   | Event                  | Scenario            | Expected outbound                   | Expected state             |
| ---- | ---------------------- | ------------------- | ----------------------------------- | -------------------------- |
| R-01 | `action` (attack-like) | hit resolution      | result event(s) + hp delta event(s) | target hp reduced          |
| R-02 | `action` (attack-like) | miss resolution     | result event(s) without hp delta    | no hp change               |
| R-03 | `action` (damage)      | target reaches 0 hp | result + `actor_died`               | actor dead state set       |
| R-04 | `action` (heal)        | valid heal          | result + `actor_healed`             | hp increased capped at max |
| R-05 | `action` (condition)   | apply condition     | result + `condition_added`          | condition present          |
| R-06 | `action` (condition)   | remove condition    | result + `condition_removed`        | condition absent           |

Stage C and D preview/validation additions:

| ID   | Event                    | Scenario                                           | Expected outbound                           | Expected state             |
| ---- | ------------------------ | -------------------------------------------------- | ------------------------------------------- | -------------------------- |
| R-07 | `request_attack_preview` | single-target attack preview request               | `attack_preview` with `eligible_target_ids` | no mutation (preview-only) |
| R-08 | `request_attack_preview` | non-owner / invalid actor request                  | `command_denied` deterministic reason code  | no mutation                |
| R-09 | `request_attack_preview` | AoE preview request                                | `attack_preview` with `template_projection` | no mutation (preview-only) |
| R-10 | `request_action`         | execute against target outside preview eligibility | `action_denied` (`invalid_target`)          | no mutation                |
| R-11 | `request_action`         | execute AoE with invalid template origin/intersect | `action_denied` (`invalid_target`)          | no mutation                |

Acceptance requirement:

- A command with successful authorization must not terminate at authorize-only for implemented action families.

## 6. Direct State Manipulation Family (DM Tools)

| ID   | Event              | Scenario                  | Expected outbound                         | Expected state      |
| ---- | ------------------ | ------------------------- | ----------------------------------------- | ------------------- |
| D-01 | `apply_damage`     | valid actor               | `actor_damaged` (+ optional `actor_died`) | hp/temp hp mutated  |
| D-02 | `apply_healing`    | valid actor               | `actor_healed`                            | hp mutated          |
| D-03 | `apply_condition`  | valid condition           | `condition_added`                         | condition added     |
| D-04 | `remove_condition` | valid condition           | `condition_removed`                       | condition removed   |
| D-05 | `remove_actor`     | existing actor            | `actor_removed`                           | actor+token removed |
| D-06 | `add_actor`        | valid definition+position | `actor_added`                             | actor+token created |

## 7. Utility and Sync Family

| ID   | Event          | Scenario           | Expected outbound             | Expected state |
| ---- | -------------- | ------------------ | ----------------------------- | -------------- |
| U-01 | `ping`         | any connected role | `pong`                        | none           |
| U-02 | `request_sync` | any connected role | `state_sync` filtered by role | none           |
| U-03 | `roll_dice`    | valid expression   | `dice_rolled`                 | none           |
| U-04 | `chat_message` | non-empty message  | `chat_message`                | none           |
| U-05 | `chat_message` | blank message      | `error` (`invalid_message`)   | none           |

## 8. Declared-but-Unrouted Alignment Family

| ID   | Event             | Decision branch  | Acceptance                          |
| ---- | ----------------- | ---------------- | ----------------------------------- |
| X-01 | `update_hp`       | implemented      | routed + tested end-to-end          |
| X-02 | `update_hp`       | deferred/removed | removed from permissions/types/docs |
| X-03 | `roll_initiative` | implemented      | routed + tested end-to-end          |
| X-04 | `roll_initiative` | deferred/removed | removed from permissions/types/docs |
| X-05 | `cast_spell`      | implemented      | routed + tested end-to-end          |
| X-06 | `cast_spell`      | deferred/removed | removed from permissions/types/docs |
| X-07 | `toggle_equip`    | implemented      | routed + tested end-to-end          |
| X-08 | `toggle_equip`    | deferred/removed | removed from permissions/types/docs |

Rule:

- Each declared key must end in exactly one branch: implemented or removed/deferred with explicit contract status.

Phase 4 status (current):

- Selected deferred/removed branch: X-02, X-04, X-06, X-08.
- `update_hp`, `roll_initiative`, `cast_spell`, and `toggle_equip` are removed from
  active permission/type declarations and active inbound contract docs.

## 9. Non-Functional Acceptance

| ID   | Area          | Requirement                                                |
| ---- | ------------- | ---------------------------------------------------------- |
| N-01 | Determinism   | No command path returns silent `[]` to caller intent flows |
| N-02 | Correlation   | All command responses include or correlate to `request_id` |
| N-03 | Observability | Logs show inbound type, actor, decision, terminal outcome  |
| N-04 | Consistency   | Auth/budget results identical between persistence modes    |
| N-05 | Compatibility | Contract change log produced for frontend handover         |

Phase 0 contract clarifications:

- Command events MUST include `request_id`; missing ids are rejected with `error` (`invalid_message`).
- Denied outcomes are explicit terminal denied events (`action_denied` for action-family, `command_denied` for other command families).

Phase 5 handover status:

- N-05 artifact published:
  - [docs/architecture/backend/16_ws_event_frontend_contract_handover.md](docs/architecture/backend/16_ws_event_frontend_contract_handover.md)
- Handover defines versioned contract target (`ws-combat-v2`) and frontend migration checklist.
- Compatibility policy is explicit: no backend wire aliases; transitional compatibility is frontend adapter-only.

## 10. Exit Gate

Refactor is backend-ready for frontend integration only when:

- All critical rows pass: L-03, L-04, M-02, M-03, M-04, A-03, A-06, R-01.
- Stage A-D rows are green for implemented scope: A-08, A-09, A-10, A-11, M-07, M-08, M-09, R-07, R-08, R-09, R-10, R-11.
- No silent command paths remain.
- Event catalog is synchronized with implemented routing.
