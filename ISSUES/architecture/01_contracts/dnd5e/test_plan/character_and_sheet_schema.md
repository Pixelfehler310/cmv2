# Test Plan: DND5E-05 Character and Sheet Schema

## Unit Targets

1. Character record schema validation.
2. Character build-link resolution validation.
3. Character-sheet projection response shape validation.
4. Character-sheet denial and invalidation event payload validation.
5. Revision monotonicity checks for sheet projection publishing.

## Invariants

1. Character has campaign ownership metadata.
2. Required build references are resolvable.
3. Sheet projection contains revision metadata.
4. `sheet_revision` is monotonic per character.
5. `resolution_status` is constrained to resolved/denied/invalidated.
6. Denied outcomes include reason code and unresolved references.

## Edge Cases

1. Character without campaign id.
2. Character referencing deleted/archived required definition.
3. Projection built with stale revision input.
4. Duplicate ability id links.
5. Projection marked denied but missing denial metadata.
6. Cross-campaign reference resolution attempt.
7. Idempotent retry with same catalog revision after transient failure.

## Expected Results

1. Ownership and schema violations deny deterministically.
2. Missing required references produce explicit denial reasons.
3. Successful projection responses include stable sheet payload shape.
4. Revision regressions deny with stable contract reason-code families.
5. Invalidation events force resync and preserve request correlation.
