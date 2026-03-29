# Test Plan: DND5E-04 Content Query and Read-Model

## Unit Targets
1. Query envelope filter and cursor validation.
2. Link expansion behavior.
3. Projection invalidation behavior.

## Invariants
1. Same query + revision yields stable ordering.
2. Link expansion is explicit and deterministic.
3. Replacement chain resolution returns visible terminal.

## Edge Cases
1. Revision gap between consumer and event stream.
2. Missing linked targets during detail hydration.
3. Invalid cursor contract.

## Expected Results
1. Invalid queries are denied with reason code.
2. Revision gap triggers invalidation/refetch path.
3. Broken required links return terminal denied result.
