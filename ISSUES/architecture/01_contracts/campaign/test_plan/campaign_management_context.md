# Test Plan: CAM-01 Campaign Management Context

## Unit Targets

1. Campaign context envelope validation.
2. Membership/role gate validation.
3. Campaign lifecycle write-permission validation.

## Invariants

1. Campaign-scoped writes always include campaign context.
2. Non-members cannot mutate campaign-scoped entities.
3. Campaign lifecycle state can deny write operations.
4. Cross-campaign mutations are rejected.

## Edge Cases

1. Command with missing campaign id.
2. Member with inactive status attempting mutation.
3. Valid member attempting mutation against different campaign id.

## Expected Results

1. Invalid campaign context denies with explicit reason codes.
2. Membership and lifecycle denials are deterministic.
3. Valid context and membership allow mutation path continuation.
