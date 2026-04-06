# Test Plan: DND5E-05 Character and Sheet Schema

## Unit Targets

1. Character record schema validation.
2. Character build-link resolution validation.
3. Character-sheet projection response shape validation.

## Invariants

1. Character has campaign ownership metadata.
2. Required build references are resolvable.
3. Sheet projection contains revision metadata.

## Edge Cases

1. Character without campaign id.
2. Character referencing deleted/archived required definition.
3. Projection built with stale revision input.

## Expected Results

1. Ownership and schema violations deny deterministically.
2. Missing required references produce explicit denial reasons.
3. Successful projection responses include stable sheet payload shape.
