# Test Plan: CORE-05 Layer Ownership and Dependency Direction

## Unit Targets
1. Static dependency policy checks.
2. Service ownership checks for mutable aggregates.

## Invariants
1. Transport cannot write repositories directly.
2. Application is the only orchestration owner.
3. Domain has no transport dependencies.

## Edge Cases
1. Repository imports policy decision classes.
2. Transport calls repository mutation path directly.
3. Projection layer attempts direct mutation shortcut.

## Expected Results
1. Forbidden directions fail architecture gate.
2. Ownership violations are blocked before merge.
