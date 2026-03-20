# PR Concept: Refactor `ws_handler.py` (SRP Violation)

> [!CAUTION]
> **WARNING - CRITICAL ARCHITECTURAL FLAW**
> The current implementation of `systems/dnd5e/ws_handler.py` represents a massive violation of the Single Responsibility Principle (SRP). It is currently nearly 100KB in size because it does not act as a simple WebSocket router; instead, it fundamentally leaks and executes core business logic. 

## Extensive Explanation of the Structural Flaw
In a clean architecture, the WebSocket layer should only be responsible for:
1. **Deserialization**: Taking raw JSON strings and parsing them into `WsEnvelope`.
2. **Permission Checks**: Role-based access control (DM vs Player).
3. **Delegation**: Passing the structured data to a Domain Service (`CombatService`).
4. **Serialization and Broadcast**: Taking the resulting domain events and pushing them back down the socket securely (Fog of War filtering).

Instead, the current `ws_handler.py` manually calculates target eligibility for previews, performs cross-checks on action budgets manually *before* passing execution down to the Action Resolver, duplicates loop comprehensions to find active tokens, and resolves complex "effect intents" internally. 
**This makes the code uncomposable, highly prone to regression, impossible to unit-test in isolation, and incredibly difficult for multiple developers to safely modify.**

---

## 1-PR Scoped Fix Concept

### Objective
Create a strict boundary between the WebSocket transport layer `ws_handler.py` and the D&D engine `CombatService`, fully encapsulating all combat validation and calculation inside the service layer.

### Acceptance Criteria
1. **Reduce Handler Size**: `ws_handler.py` should be stripped down purely to `fastapi` style route-to-service delegations.
2. **Service Layer API Expansion**: Expand `CombatService` to expose robust validation methods:
   - `CombatService.generate_attack_preview(actor, action)`
   - `CombatService.validate_action_budget(actor, action)`
   - `CombatService.resolve_action_intents(actor, action, targets)`
3. **Remove Engine Imports from Handler**: The `ws_handler.py` should no longer import `DiceService`, `action_resolver`, `TurnBudget`, or `effect_engine`. It should only import `CombatService`.
4. **Testability**: The newly migrated `CombatService` methods must have dedicated Pytest suites that operate entirely without a `WebSocket` object or `SessionContext`.

### Execution Steps
1. Create a `validation.py` sub-module inside the `systems/dnd5e/services/` directory.
2. Cut the massive helper methods (like `_handle_request_attack_preview` validation loops) out of `ws_handler.py` and paste them into the new service layer as stateless domain functions.
3. Update `ws_handler.py` so that `_handle_request_attack_preview` strictly parses the IDs from the socket envelope, calls the service, and constructs the expected outbound `WsOutbound` envelope.
4. Ensure `check_can_act` natively encompasses the resource budget checks that are currently spread throughout the handler's if/else branches.
