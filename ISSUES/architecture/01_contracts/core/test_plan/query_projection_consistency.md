# Test Plan: CORE-03 Query and Projection Consistency

## Unit Targets
1. Revision snapshot selection.
2. Monotonic revision increments.
3. Projection gap detection policy.

## Invariants
1. Same request + same revision yields deterministic ordering.
2. One successful mutation creates one new revision.
3. Projection events carry revision metadata.

## Edge Cases
1. Consumer receives revision gap larger than 1.
2. Query executed while mutation event arrives concurrently.
3. Missing revision metadata in projection event.

## Expected Results
1. Revision gap triggers invalidation event.
2. Missing revision metadata triggers denied/error terminal result.
3. No silent fallback to time-based cache heuristics.
