# Module Annex: runtime

## Scope

Session lifecycle, runtime orchestration, and state synchronization boundaries.

## Primary Classes

1. `SessionManager` for campaign room lifecycle and connection registry.
2. `CampaignRoom` for per-campaign connected user aggregate and delegation map.
3. `ConnectedUser` for socket-bound identity and role record.
4. `SessionContext` for per-request authenticated and effective identity state.
5. `RuntimeSessionService` for session orchestration (start, sync, end).
6. `CampaignPolicyService` for membership, lifecycle, and scope decisions.
7. `TransportGateway` for envelope ingress/egress normalization.
8. `EventPublisher` for runtime event fanout and correlation tagging.

## Externally Callable Methods (20+)

1. `SessionManager.register_connection(campaign_id, user, game_system)`
2. `SessionManager.unregister_connection(campaign_id, user_id)`
3. `SessionManager.get_room(campaign_id)`
4. `SessionManager.list_campaign_ids()`
5. `SessionManager.get_connected_users(campaign_id)`
6. `SessionManager.broadcast(campaign_id, event)`
7. `SessionManager.send_to_user(campaign_id, user_id, event)`
8. `SessionManager.start_delegation(campaign_id, controlling_user_id, target_user_id)`
9. `SessionManager.stop_delegation(campaign_id, controlling_user_id)`
10. `SessionManager.get_delegation(campaign_id, controlling_user_id)`
11. `SessionManager.resolve_effective_user_id(campaign_id, user_id)`
12. `RuntimeSessionService.startSession(ctx)`
13. `RuntimeSessionService.syncState(ctx)`
14. `RuntimeSessionService.endSession(ctx)`
15. `CampaignPolicyService.checkMembership(ctx)`
16. `CampaignPolicyService.checkLifecycle(ctx)`
17. `CampaignPolicyService.checkScope(ctx)`
18. `TransportGateway.handleRestCommand(ctx)`
19. `TransportGateway.handleWsCommand(ctx)`
20. `TransportGateway.mapTerminalOutcome(ctx)`
21. `EventPublisher.publishDomainEvent(ctx)`
22. `EventPublisher.publishDeniedEvent(ctx)`

## Method Contract Minimums

For each method above, implementation-facing specs must include:

1. Input context object name and required attributes.
2. Output envelope or result object.
3. Deterministic denial reason family when applicable.
4. Side effects on room state, persistence, or event stream.

## Critical Flows

1. Session bootstrap (connect, context build, initial sync, joined broadcast).
2. Command dispatch with policy gating and terminal outcome mapping.
3. Delegation start and stop lifecycle with effective identity switching.
4. State sync request and response for reconnect and manual refresh.
5. Visibility-aware event broadcast to role- and owner-filtered recipients.
6. Disconnect cleanup and room teardown when last user leaves.

Each flow must define:

1. Resolved path.
2. Denied path with stable reason code.
3. Recovery or retry semantics.

## Context Objects

1. `SessionContext` with `campaign_id`, `authenticated_user_id`, `effective_user_id`, `role`, `delegation_active`, `session_id`.
2. `WsEnvelope` with `type`, `request_id`, `payload`.
3. `WsOutbound` with `type`, `request_id`, `payload`, `visibility`, `target_user_id`.
4. `CampaignRoom` with `campaign_id`, `users`, `active_delegations`.

Ownership and mutability:

1. `SessionContext` is immutable after request construction.
2. `WsEnvelope` is immutable input.
3. `WsOutbound` is immutable after emission mapping.
4. `CampaignRoom` is mutable only through `SessionManager` operations.

## Constraints and Denial Mapping

Invariants:

1. Every command envelope must terminate in resolved, denied, or error outcome.
2. `request_id` must remain stable from ingress to terminal response.
3. Delegation requires DM or owner authority.
4. Visibility filtering must prevent unauthorized event exposure.

Primary denial families:

1. `invalid_message`
2. `forbidden`
3. `not_owner`
4. `scene_combat_session_required`
5. `invalid_turn_phase`

## Recovery and Idempotency

1. Replayed request ids must return cached or equivalent terminal outcomes.
2. Disconnect/reconnect must permit deterministic `syncState` restoration.
3. Drift notifications should route to recovery module without mutating runtime envelopes.
4. Delegation resolution must be deterministic for same request and room state.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-05]_layer_ownership.md`.
3. Contracts: `ISSUES/architecture/01_contracts/campaign/ISSUE_[CONTRACT]_[CAM-01]_campaign_management_context.md`.
4. Diagrams: `ISSUES/architecture/01_contracts/overview/MASTER_SYSTEM_CLASS_SPEC.mmd` and `ISSUES/architecture/01_contracts/overview/HORIZONTAL_CONTRACT_DETAIL_OVERVIEW.mmd`.
5. Code anchors: `backend/src/core/ws_dispatcher.py` and `backend/src/core/ws_protocol.py`.
