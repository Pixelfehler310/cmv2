# Test Plan: D&D 5e Base Rule Schema (D1) Validation

## Goal
Verify that all game entities (Monsters, Spells, Items) strictly adhere to the **Horizontal Layer 1 Contract** defined in `ISSUE_[CONTRACT]_[DND5E-01]`.

## 1. Unit Invariants (Monsters)
- **Attribute Range**: Str, Dex, Con, Int, Wis, Cha must be between 1 and 30.
- **HP Validity**: `hit_points` must be integer > 0.
- **Speed Units**: Speed values (Walk, Fly, etc.) must be non-negative.
- **Action Count**: A Monster must have at least 1 Action or Trait unless it's a non-combatant.

## 2. Unit Invariants (Spells)
- **Level Integrity**: Spell level must be an integer between 0 and 9.
- **Casting Time**: Must match a standard time taxonomy (e.g. "1 Action", "1 Bonus Action", "1 Reaction").
- **Components**: At least one component (V, S, or M) should be defined if it's a player-castable spell.

## 3. Unit Invariants (Items)
- **Weight**: Must be >= 0.
- **Cost**: Must be >= 0 (CP).
- **Rarity**: Must match a standard rarity category.

## 4. Edge Cases
- **Recursive Linking**: Ensure a Monster's action doesn't create an infinite resolving loop in the Action Mechanics (D2) layer.
- **Invalid Formulas**: HP formulas that are unparseable (e.g. "5xx + 10").
- **Missing Action Specs**: Monsters with actions that have no `ActionOperationSpec`.

## 5. Expected Results
- Validation should fail with a `CompendiumErrorCode.VALIDATION_FAILED` (422) if any of the above are violated.
- Successfully harvested legacy data should be transformed into the new Pydantic shapes with 100% field coverage.
