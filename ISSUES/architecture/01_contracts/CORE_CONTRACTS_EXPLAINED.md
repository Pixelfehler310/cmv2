# Core Contracts Explained (Plain-Language)

This document explains what each CORE contract does, why it matters, and what should be tested before calling it freeze-ready for implementation.

## CORE-01: Pack and Definition Lifecycle

## What it governs

The allowed state changes for packs and definitions (`draft`, `published`, `archived`, `superseded`).

## Why it exists

Without this contract, one API path may allow a transition that another path denies, causing inconsistent behavior and broken authoring workflows.

## What to test

1. Legal transitions resolve.
2. Illegal transitions deny with explicit reason code.
3. Delete is only allowed for draft records.
4. Supersedence requires valid replacement target.

## CORE-02: Referential Integrity and Link Graph

## What it governs

How references between definitions are validated and resolved, including cycle protection and replacement-chain handling.

## Why it exists

Content entries are connected (spells, items, lore, monsters). Broken links or hidden cycles create runtime failures and unreadable compendium data.

## What to test

1. Required missing target denies.
2. Cycle creation denies before persistence.
3. Strict vs best-effort resolution behavior is deterministic.
4. Replacement chains resolve to the current visible target.

## CORE-03: Query and Projection Consistency

## What it governs

Revision semantics and deterministic read behavior across list/detail/read-model outputs.

## Why it exists

Without revision consistency, clients can apply stale data or out-of-order updates and diverge from backend truth.

## What to test

1. Same query + same revision returns deterministic results.
2. Revision gaps trigger invalidation/recovery behavior.
3. Outdated events are rejected or ignored deterministically.
4. Terminal outcomes include required status metadata.

## CORE-04: Session and Event Envelopes

## What it governs

The command/result/event envelope shape and correlation rules (`request_id`, status, reason codes, revision metadata).

## Why it exists

Adapters and clients must rely on stable machine-readable outcomes to render state without transport-specific branching.

## What to test

1. Required envelope fields are always present.
2. Denied/error outcomes always carry reason codes.
3. Request correlation remains stable end-to-end.
4. Projection events include revision context.

## CORE-05: Layer Ownership and Dependency Direction

## What it governs

Which layer may call which other layer, and who owns mutation orchestration.

## Why it exists

This prevents hidden coupling and logic leakage that causes long-term rework and unpredictable behavior.

## What to test

1. Transport does not write directly to repositories.
2. Repository does not implement policy decisions.
3. Domain does not depend on transport concerns.
4. Each mutable aggregate has one clear application-service owner.

## Testing Practicality Checklist

Before claiming contract freeze, each CORE contract should support:

1. At least one success path test.
2. At least one denial path test.
3. Deterministic reason-code assertions for failures.
4. Clear mapping between contract invariants and test-plan items.
