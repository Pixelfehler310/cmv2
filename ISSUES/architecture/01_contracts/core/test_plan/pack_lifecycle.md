# Test Plan: CORE-01 Pack and Definition Lifecycle

## Unit Targets
1. Transition validation policy.
2. Supersedence guard validation.
3. Delete permission validation.

## Invariants
1. `draft -> published` is legal.
2. `published -> draft` is illegal.
3. `superseded` is terminal for direct mutation.
4. Hard delete is denied for non-draft entities.

## Edge Cases
1. Publish request on already published entity.
2. Supersede request with same source and target.
3. Restore request for archived pack with missing dependencies.

## Expected Results
1. Illegal transitions return `INVALID_LIFECYCLE_TRANSITION`.
2. Invalid supersedence returns `INVALID_REPLACEMENT_TARGET`.
3. Successful transitions emit one terminal resolved outcome.
