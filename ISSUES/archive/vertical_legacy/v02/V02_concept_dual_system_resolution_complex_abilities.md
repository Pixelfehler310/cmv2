# V02 Concept: Dual-System Resolution for Complex Abilities (Unlocks vs. Choices)

Status: Draft for Integration
Related module issue: ISSUE [VERT][V02]
Related documents:

- V02_combat_actions_planning_overview.md
- V02_action_processing_and_event_contracts_overview.md
- test/README.md
- test/V02_test_seq_03_pending_choice_pause_resume_smite.mmd
- test/V02_test_seq_04_unlock_mutation_and_followup_action.mmd

## 1. The Design Problem

D&D 5e features an action economy that is highly contextual and heavily driven by "reactive" decisions. When a player takes an action, the game state does not simply leap to a finalized outcome. Instead, feats, class features, and spells constantly interrupt, expand, or unlock new options based on specific triggers (e.g., scoring a critical hit or entering a specific phase of a weapon attack).

To maintain the deterministic, API-driven operation-graph architecture established in V02, we cannot rely on monolithic, hardcoded execution paths. We must formalize how the engine handles:

1.  **Macro-level rule expansions:** (e.g., Polearm Master granting a new Bonus Action attack type, or Great Weapon Master granting a temporary Bonus Action on a kill).
2.  **Micro-level execution interruptions:** (e.g., A Paladin deciding to inject Divine Smite damage _after_ confirming a hit but _before_ rolling damage).

## 2. The Dual-System Solution

This concept resolves the complexity by explicitly separating Macro-level turn permissions from Micro-level execution flow. We divide combat reactivity into two distinct patterns: **The "Unlock" Pattern** and **The "Pending Choice" Pattern**.

---

### System 1: The "Unlock" Pattern (Turn Budget Extension)

**Purpose:** Handle abilities that temporarily grant new, independent actions to the player's available turn options (e.g., PAM, GWM, Crossbow Expert).

**Mechanism:** This is an event-driven state mutation on the `TurnBudgetRuntime`.

1.  **Triggering Event:** An action executes and resolves (e.g., `Attack Action Resolved` or `Actor Died`). The system emits a standard `CombatOutcomeEvent`.
2.  **Listener Policy:** A passive feat/feature listener observes the event. If the conditions are met (e.g., the player has the GWM feat and the event was a critical hit), the listener sends a targeted mutation command to the `TurnBudget`.
3.  **State Update:** The `TurnBudgetRuntime` updates to include a new, specific action reference.
    - _Old Model:_ `bonus_action_available: true`
    - _New Model:_ `available_on_turn_action_refs: ["action.standard_bonus", "feat.gwm.cleave_attack"]`
4.  **Client Resolution:** The frontend receives the `turn_budget_updated` event and lights up the previously hidden "Cleave Attack" button. The player makes a totally separate, new execute-action request.

**Why this fits V02:** It keeps individual `ActionExecutionRequests` strictly atomic. The backend doesn't have to guess if the player _wants_ to use their GWM bonus action right now; it just makes it legal to execute later in the turn.

---

### System 2: The "Pending Choice" Pattern (Graph Interruption)

**Purpose:** Handle abilities that require mid-resolution player input to modify an _currently executing_ operation (e.g., Divine Smite, Sneak Attack, Shield spell reaction).

**Mechanism:** This is a pause-and-resume capability built directly into the `ActionProcessingPipeline`.

1.  **Operation Node Definition:** An `ActionOperationSpec` can include a `choice_ref` (indicating that reaching this node requires a decision) and a `predicate` (indicating the condition under which the node is even evaluated, such as `on_hit`).
2.  **Execution Pause:** When the `ActionExecutionApplicationService` reaches a choice node whose predicate evaluates to true, it **halts** execution of the graph.
3.  **State Output:** The engine returns an `ActionExecutionOutcome` with a new status: `pending_choice`. The payload includes a `choice_context` object describing what decision is needed (e.g., `{"type": "smite", "valid_slots": [1, 2, 3]}`).
4.  **Client Resolution:** The frontend displays the prompt overlay to the player. The player selects an option (e.g., "Use Level 2 Slot").
5.  **Graph Resumption:** The client sends a continuation request containing the `choice_result`. The engine consumes the resource, injects the resulting damage/effect operation into the remaining graph, and resumes execution to finality.

**Why this fits V02:** It ensures that damage and effect resolution remains strictly deterministic while preserving the exact "prompt-before-damage" timing required by 5e rules.

---

## 3. Required Architectural Changes

To implement this dual-system concept, the following specific modifications must be made to the V02 canonical models:

### A. Turn Budget Runtime Updates

The turn budget must track specific contextual action keys, not just boolean availability.

```python
class TurnBudgetRuntime:
    actor_id: str
    turn_id: str
    action_available: bool
    bonus_action_available: bool
    reaction_available: bool
    movement_remaining: int

    # NEW: Tracks specific contextual actions currently legal to execute
    # e.g., ["feat.pam.bonus_attack", "action.cunning_action.hide"]
    unlocked_action_refs: list[str]
```

### B. Execution Outcome Updates

The execution return payload must support the pause-and-prompt state.

```python
class ActionExecutionOutcome:
    # NEW: Added 'pending_choice' to status enum
    status: resolved | denied | error | pending_choice
    reason_code: str | None

    # NEW: Payload for the UI to construct the prompt
    choice_context: dict | None
    target_operation_id: str | None
```

### C. Operation Spec Updates

The base operation definition must support conditional evaluation and choice hooks.

```python
class ActionOperationSpec:
    operation_id: str
    operation_kind: str
    # ... existing fields ...

    # NEW: Condition required to evaluate this node (e.g. 'on_crit', 'on_hit')
    predicate: str | None

    # NEW: Identifier for the type of prompt required if the predicate passes
    choice_ref: str | None
```

## 4. Policy Bypass and Automation

A major benefit of this dual system is that **System 1 (Unlocks/Policies) can automate System 2 (Choices).**

If a player configures a "Smite Policy" in their settings (e.g., "Always use highest available slot on critical hits"), the engine handles it seamlessly:

1. The Operations Graph reaches the Divine Smite `choice_ref` node under an `on_crit` predicate.
2. Before returning `pending_choice`, the engine queries the player's active policies.
3. Finding a matching automation policy, the engine automatically supplies the `choice_result`.
4. The graph execution injects the damage immediately and resolves to finality in a single round trip, skipping the UI prompt entirely while maintaining strict architectural determinism.
