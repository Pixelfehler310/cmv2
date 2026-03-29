# ISSUE [CONTRACT] [DND5E-03]: Action Mechanics Contract

## Why This Exists
Action execution must be contract-driven and deterministic so combat runtime and content authoring stay aligned across clients and backend.

## Action Operation Contract
`ActionOperationSpec` requires:
1. `operation_id`
2. `activation_cost`
3. `activation_trigger`
4. `resource_consumption`
5. `targeting_spec`
6. `payload` (discriminated by `operation_type`)

## Supported Operation Types
1. `attack_roll`
2. `save`
3. `heal`
4. `effect_application`

## Modifier Contract
Modifier specs must support:
1. Flat modifiers
2. Dice modifiers
3. Rule overrides

## Result Piping Contract
Dynamic values may be:
1. Static values
2. Dice notation
3. `ResultReference` pointers to prior operation outputs

## Determinism Rules
1. Backend remains truth authority for rule execution.
2. `operation_id` must be stable for graph references.
3. Piped references must resolve in dependency order.
4. Invalid references must deny with validation error.

## Mermaid Sequence Diagram
```mermaid
sequenceDiagram
    participant Client
    participant Runtime
    participant OperationGraph
    participant Resolver

    Client->>Runtime: execute action(operation_id)
    Runtime->>OperationGraph: load ActionOperationSpec list
    OperationGraph->>Resolver: resolve dependencies and result refs
    Resolver-->>OperationGraph: concrete payload values
    OperationGraph-->>Runtime: ordered operation outcomes
    Runtime-->>Client: resolved outcome envelope
```

## Extracted From
1. `ISSUES/archive/vertical_legacy/v05/V2_action_mechanics_specification.md`
2. `ISSUES/archive/vertical_legacy/v05/V05_architecture_Q_and_A.md`

## Canonical Symbols
1. `ActionOperationSpec`, `OperationType`, payload models in `backend/src/systems/dnd5e/content/domain/primitives.py`
2. `ModifierSpec`, `ResultReference`, `ResultAttribute` in `backend/src/systems/dnd5e/content/domain/primitives.py`
