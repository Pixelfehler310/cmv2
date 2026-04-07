# Module Annex: identity

## Scope

Identity resolution, entitlement checks, and pack access policy boundaries.

## Primary Classes

1. `User` as canonical account aggregate.
2. `UserSession` as token issuance and revocation state.
3. `CampaignMembership` as campaign entitlement binding.
4. `EffectiveSessionContext` as immutable resolved identity for request processing.
5. `Delegation` as temporary authority transfer record.
6. `PermissionSet` as derived permission cache snapshot.

## Externally Callable Methods (10+)

1. `authenticate_user(authentication_request)`
2. `issue_session_token(user_id, token_type='Bearer')`
3. `revoke_session_token(session_id)`
4. `resolve_effective_session_context(user_id, campaign_id, request_id)`
5. `grant_campaign_membership(campaign_id, user_id, role, granted_by_user_id)`
6. `revoke_campaign_membership(campaign_id, user_id, revoked_by_user_id)`
7. `grant_resource_access(campaign_id, user_id, resource_type, resource_ids)`
8. `revoke_resource_access(campaign_id, user_id, resource_type, resource_ids)`
9. `start_delegation(campaign_id, delegating_user_id, receiving_user_id, reason)`
10. `stop_delegation(campaign_id, delegation_id)`
11. `compute_permission_set(effective_context)`
12. `check_entitlement(effective_context, resource_type, resource_id, operation)`

## Critical Flows

1. Login and session issuance flow.
2. Session context resolution for campaign-scoped command flow.
3. Membership grant and revoke flow.
4. Delegation start and stop flow with role elevation boundaries.

## Context Objects

1. `AuthenticationRequest` with username-password or refresh pathway.
2. `AuthenticationResult` with token metadata and expiry.
3. `CampaignMembershipContext` for grant-revoke operations.
4. `PermissionEvaluationContext` for per-resource operation checks.
5. `EffectiveSessionContext` for downstream module authorization decisions.

Mutability:

1. Request and result contexts are immutable.
2. Membership records are mutable only through identity entitlement methods.
3. Effective session context is immutable per request.

## Constraints and Denial Mapping

Invariants:

1. Username uniqueness is global.
2. Deactivated users cannot authenticate.
3. Membership pair `(campaign_id, user_id)` is unique.
4. Delegation cannot be recursive or self-referential.

Reason-code families:

1. `invalid_credentials`
2. `user_inactive`
3. `session_expired`
4. `membership_not_found`
5. `insufficient_entitlement`
6. `invalid_delegation_request`

## Recovery and Idempotency

1. Token issuance retries require replay-safe request correlation checks.
2. Membership grant should be idempotent for identical active grant.
3. Delegation stop should be idempotent for already-ended delegation.
4. Permission set recomputation must be deterministic for same inputs.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/campaign/ISSUE_[CONTRACT]_[CAM-01]_campaign_management_context.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/MASTER_SYSTEM_CLASS_SPEC.mmd` and `ISSUES/architecture/01_contracts/overview/HORIZONTAL_CONTRACT_DETAIL_OVERVIEW.mmd`.
4. Code anchors: `backend/src/identity/models.py`, `backend/src/identity/schemas.py`, `backend/src/identity/router.py`.
