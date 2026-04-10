# Module Annex: shared

## Scope

Shared invariants, error taxonomy, reason-code registry, and cross-module contract primitives.

## Primary Classes

1. `ReasonCodeRegistry` for canonical denial code lookup.
2. `LicenseRegistry` for managing official and homebrew license objects.
3. `ErrorEnvelope` for standardized terminal error payloads.
4. `PolicyDecision` for allow-deny-pending outcomes.
5. `ContextEnvelope` for typed cross-module context wrapping.
6. `InvariantCatalog` for registered invariant validators.
7. `ConstraintTaxonomy` for reason class and severity mapping.

## Externally Callable Methods (10+)

1. `ReasonCodeRegistry.get_reason_code(category, code_key)`
2. `ReasonCodeRegistry.list_codes_by_category(category)`
3. `ReasonCodeRegistry.validate_code_exists(code, category)`
4. `ReasonCodeRegistry.resolve_error_descriptor(code)`
5. `ErrorEnvelope.create(error_code, message, request_id, terminal=True)`
6. `ErrorEnvelope.to_ws_response()`
7. `ErrorEnvelope.is_terminal()`
8. `PolicyDecision.allow()`
9. `PolicyDecision.deny(reason_code, category, signal={})`
10. `PolicyDecision.is_allowed()`
11. `PolicyDecision.is_denied()`
12. `ContextEnvelope.wrap(context_type, data, source_module, request_id)`
13. `ContextEnvelope.get_context()`
14. `ContextEnvelope.assert_freshness(max_age_ms)`
15. `InvariantCatalog.register(key, validator, description, domains)`
16. `InvariantCatalog.validate(key, value)`
17. `InvariantCatalog.validate_all(domain, context)`
18. `ConstraintTaxonomy.classify(reason_code)`
19. `ConstraintTaxonomy.get_severity(reason_code)`
20. `ConstraintTaxonomy.find_related_codes(reason_code)`

## Critical Flows

1. Denial-code resolution and terminal envelope formatting flow.
2. Policy check decision and application flow.
3. Context envelope wrapping and freshness validation flow.
4. Invariant validation and violation reporting flow.

## Context Objects

1. `CommandCorrelationContext` for request trace path.
2. `PolicyCheckContext` for actor-target-operation checks.
3. `DenialRecoveryContext` for retry and irrecoverability hints.
4. `InvariantViolationContext` for evidence and rollback guidance.
5. `ConstraintClassificationContext` for severity scoring.

Mutability:

1. Shared context objects are immutable.
2. Taxonomy and registry data are mutable only during startup registration.
3. Violation contexts are immutable snapshots.

## Constraints and Denial Mapping

Invariants:

1. Every reason code belongs to one category and one severity class.
2. Error envelopes always include request correlation when command-derived.
3. Allowed and denied policy flags cannot both be true.
4. Shared validators must be deterministic for same input.

Reason-code families:

1. `authorization.*`
2. `resource_exhaustion.*`
3. `validation.*`
4. `transport.*`
5. `recovery.*`

## Recovery and Idempotency

1. Shared envelope creation is pure and idempotent.
2. Registry lookups are deterministic and side-effect free.
3. Validation re-runs must produce stable pass or fail for same context.
4. Denial recovery hints must preserve reason-code fidelity across retries.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-05]_layer_ownership.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/HORIZONTAL_CONTRACT_DETAIL_OVERVIEW.mmd`.
4. Code anchors: `backend/src/core/ws_protocol.py` and shared schema primitives under `backend/src/schemas/`.
