# Command Deck Enhancement Concept (DM + Player Parity)

## 1. Goal

Enhance the command deck so actions and attack options for the selected token are represented as backend-authoritative action cards with clear availability, targeting guidance, and execution feedback.

This concept keeps architecture invariants intact:

- Backend is source of truth for rules and availability.
- Frontend renders provided state and sends explicit action requests.
- Action definitions remain data-driven and extensible.

## 2. Current Baseline

- DM selection source: `DmWorkspace` owns `selectedCombatantId` and passes it into map, initiative, and command panels.
- DM command surfaces exist in `dm-view` (`CommandDeck`, `ActionDeck`).
- Player command surface exists in `apps/player-view` (`CommandDeck`) but action cards are currently simple and minimally typed.
- Backend fixtures support encounter state and monster action lists, but command deck-specific test data is not yet isolated.

## 3. Desired UX (Shared Across DM and Player)

## 3.1 Deck Modes

1. No token selected
   - Show neutral guidance and existing global utility controls.
2. Token selected
   - Show grouped action cards for the selected actor.
3. Action requires target
   - Enter target-select mode, with pending action shown until target is chosen/cancelled.

## 3.2 Action Card Information Priority

Each card should expose, in this order:

1. Intent: action name + category (attack, bonus, reaction, utility).
2. Cost/Economy: action/bonus/reaction/movement consumption.
3. Availability: enabled/disabled plus reason text.
4. Targeting: range, target mode, and area shape/size if relevant.
5. Resolution preview: to-hit, damage, save DC, effect summary.

## 3.3 Action Card States

- Available
- Pending (command in flight)
- Consumed by economy (e.g., action already used)
- No valid target
- Out of range
- Cooldown/recharge unavailable
- Limited use exhausted
- Blocked by concentration/condition

## 3.4 Interaction Flow

1. Click action card
2. If needed, enter target selection mode
3. If required, confirm (dangerous/expensive action)
4. Dispatch command payload to backend
5. Show pending feedback
6. Render accepted/rejected/resolved outcome from backend response stream

## 4. Backend-Authoritative ViewModel Contract

Introduce a shared frontend type (in `frontend/packages/types`) for action card rendering.

```ts
export interface ActionCardViewModel {
  id: string;
  name: string;
  category: "action" | "bonus_action" | "reaction" | "free" | "utility";
  tags: string[];
  sort_order: number;

  economy: {
    action_cost: number;
    bonus_action_cost: number;
    reaction_cost: number;
    movement_cost_ft: number;
    uses_remaining?: number;
    uses_max?: number;
    recharge_label?: string;
  };

  availability: {
    is_available: boolean;
    reason_code?: string;
    reason_text?: string;
  };

  targeting: {
    target_mode: "self" | "single" | "multi" | "area";
    range_ft?: number;
    aoe_shape?: "cone" | "sphere" | "line" | "cube" | "cylinder";
    aoe_size_ft?: number;
    valid_target_filters?: string[];
  };

  preview: {
    to_hit?: string;
    damage?: string;
    damage_type?: string;
    save_dc?: number;
    save_ability?: string;
    effects?: string[];
  };

  request_template: {
    action_type: string;
    action_name: string;
    payload: Record<string, unknown>;
  };

  confirm_required?: boolean;
}
```

Notes:

- If this model is missing, frontend falls back to existing simple button rendering.
- Frontend does not calculate hit chance, damage totals, or turn budget deltas.

## 5. Rendering and Composition Rules

- Group order: Action -> Bonus Action -> Reaction -> Free -> Utility.
- Within group: sort by `sort_order`, then name.
- Disabled cards remain visible with explicit reason (no hidden action surprises).
- Compact mode: intent + cost + key availability hint.
- Expanded mode: includes full targeting and preview blocks.

## 6. Backend Test Data Strategy (Implemented in Fixtures)

Add dedicated fixture pair for command deck exercise coverage:

1. Monster fixture with comprehensive action metadata
   - File: `backend/data/fixtures/monsters/027_command_deck_test_warlord.json`
   - Includes 15+ actions spanning:
     - melee/ranged attacks
     - bonus and reaction actions
     - save-based area action
     - recharge-labeled action
     - movement-cost utility actions
     - concentration/effect-style action metadata
     - limited-use and legendary-style actions

2. Encounter fixture for selected-token command deck testing
   - File: `backend/data/fixtures/encounters/11_command_deck_actions.json`
   - Uses `seed-campaign-001`
   - Contains PCs + the test warlord + supporting targets
   - Token map aligns exactly with combatant ids

## 7. Validation Requirements

- `backend/tests/test_fixtures.py` must pass for:
  - valid monster fixture schema
  - valid encounter fixture schema
  - encounter token/combatant reference integrity
  - fixture volume thresholds (new fixtures increase totals)

## 8. Rollout Plan

1. Ship fixture data and concept (this phase).
2. Add typed action-card view model to shared frontend types.
3. Update DM command deck to render grouped cards from backend model.
4. Update player command deck to render the same card model for parity.
5. Wire target-select and command outcome feedback loop.
6. Add frontend tests for card state matrix and fallback mode.

## 9. Architecture Guardrails

- No frontend-only game rule calculations.
- No duplicated decision logic between DM and Player decks.
- All availability and restrictions are backend-provided and displayed verbatim.
- Keep model fields optional where backend migration is incremental.
