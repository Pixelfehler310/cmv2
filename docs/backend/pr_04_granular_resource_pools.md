# PR Concept: Granular Resource Pools

## Overview
The current engine excels at tracking the strict phase action economy defined by the `TurnBudget` (Action, Bonus Action, Reaction, Movement), as well as foundational `SpellSlots` and standard Hit Points. 

However, D&D 5e relies heavily on granular class-specific sub-resources (e.g., Sorcery Points, Ki Points, Battlemaster Superiority Dice, Lay on Hands pools, Bardic Inspiration). The backend currently lacks a dynamic generic system to track the consumption limitation of these resources when a specific action is performed.

## 1-PR Scoped Fix Concept

### Objective
Introduce a flexible, schema-driven `ResourceTracker` mechanism that allows `ActionDefinition` objects to require and seamlessly deduct custom localized resources during the Action Resolver pipeline alongside standard turn budgets.

### Acceptance Criteria
1. **Schema Update**: Implement the already partially-stubbed `ResourceCounter` inside `ActorInstance.resources` allowing an actor to hold an arbitrary dictionary of pools (e.g., `{"ki": {"current": 4, "max": 4}}`).
2. **Action Cost Upgrade**: Expand `ActionDefinition` so that the `cost` field can define required resources (e.g., `requires_resource: {"name": "ki", "amount": 1}`).
3. **Execution Verification**: The `CombatService.check_can_act()` function must fail validation if the actor does not possess the required minimum resource amount.
4. **Deduction via Resolver**: The `action_resolver.py` or budget delegator must cleanly subtract exactly the `amount` required from the actor's specific pool once the action resolves successfully.

### Execution Steps
1. Enhance the `ActionDefinition` schema in `systems/dnd5e/schemas/definitions.py` to include a generic `resource_cost: Optional[Dict[str, int]]` field.
2. In `systems/dnd5e/services/combat_service.py`, append a logic block mapped alongside `action_available` checks ensuring the requested action's `resource_cost` is validated against `actor.resources.counters`. 
3. Modify `resolve_and_apply()` inside the `action_resolver.py` to dynamically decrement those dictionary integers synchronously alongside the `.use_action()` budget call.
4. Add robust Pytest tests for checking a Monk using "Flurry of Blows" fails if "ki" is at 0.
