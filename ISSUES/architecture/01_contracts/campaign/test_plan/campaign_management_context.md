# Test Plan: CAM-01 Campaign Management Context

## Unit Targets

1. Campaign context envelope validation.
2. Membership/role gate validation.
3. Campaign lifecycle write-permission validation.
4. Scope-match validation between command context and target aggregate.
5. Terminal envelope outcome and reason-code completeness validation.

## Invariants

1. Campaign-scoped writes always include campaign context.
2. Non-members cannot mutate campaign-scoped entities.
3. Campaign lifecycle state can deny write operations.
4. Cross-campaign mutations are rejected.
5. Unknown role/membership values are rejected deterministically.
6. Every denied outcome includes stable reason codes.

## Edge Cases

1. Command with missing campaign id.
2. Member with inactive status attempting mutation.
3. Valid member attempting mutation against different campaign id.
4. Actor user id present but no membership record found.
5. Command denied path returning envelope without reason code.
6. Replayed command with stale campaign context.

## Expected Results

1. Invalid campaign context denies with explicit reason codes.
2. Membership and lifecycle denials are deterministic.
3. Valid context and membership allow mutation path continuation.
4. Scope mismatches deny prior to application logic invocation.
5. Context invalidation and retry flows remain correlated and terminal.
