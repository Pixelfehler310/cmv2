# Walkthrough: Milestone 2.3 - Effect Engine V1

I have implemented the initial version of the Effect Engine, allowing for static modifiers to be applied to game entities.

## Changes

### 1. Effect Schema (`backend/src/schemas/effect.py`)
- **`Effect`**: Defines a modifier with `type` (BONUS, SET), `target` (attribute path), and `value`.

### 2. Schema Updates
- **`CharacterBase`**, **`MonsterBase`**, **`MonsterInstance`**, **`ItemBase`**: Added `effects: List[Effect]` field.

### 3. Effect Engine (`backend/src/services/effect_engine.py`)
- **`EffectEngine.apply_effects(entity)`**:
    - Creates a deep copy of the entity (View Model).
    - Aggregates effects from the entity itself and equipped items.
    - Applies effects to target attributes (supporting nested paths like `speed.walk`).

## Verification

I created `backend/tests/test_effects.py` covering:
- **Bonus Effects**: Adding to stats (e.g., +1 AC).
- **Set Effects**: Overriding stats (e.g., Strength = 19).
- **Inventory Integration**: Effects from equipped items are automatically applied.
- **Nested Attributes**: Modifying nested fields like `speed.walk`.

### Test Results
```
tests\test_effects.py ....                                         [100%]
4 passed in 0.04s
```
