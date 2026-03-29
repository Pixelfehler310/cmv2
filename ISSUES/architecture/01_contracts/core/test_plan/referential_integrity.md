# Test Plan: CORE-02 Referential Integrity

## Unit Targets
1. Missing-target detection.
2. Cycle detection and denial.
3. Replacement chain validation.

## Invariants
1. Required strict link must resolve.
2. Graph cycles are denied before persistence.
3. Chain resolution returns current visible terminal.

## Edge Cases
1. Self-reference link.
2. Two-node cycle (`A -> B -> A`).
3. Delete target still referenced by required links.

## Expected Results
1. Missing target returns `LINKED_TARGET_NOT_FOUND`.
2. Cycle returns `CYCLE_DETECTED` or `GRAPH_CYCLE_DETECTED`.
3. Protected delete returns `LINKED_TARGET_IN_USE`.
