# Module Annex: transport

## Scope

REST and WebSocket command handling, envelope validation, and terminal outcome mapping.

## Primary Classes

1. `TransportEnvelopeValidator` for strict inbound-outbound schema checks.
2. `RequestCorrelationTracker` for request id registration and fulfillment tracking.
3. `VisibilityRouter` for role and ownership visibility filtering.
4. `MessageBroadcaster` for targeted or broadcast socket delivery.
5. `RestApiGateway` for HTTP-to-envelope conversion and auth extraction.
6. `TransportErrorFormatter` for exception and denial normalization.

## Externally Callable Methods (10+)

1. `TransportEnvelopeValidator.validate_inbound(raw)`
2. `TransportEnvelopeValidator.validate_outbound(envelope)`
3. `TransportEnvelopeValidator.normalize_request_id(req_id)`
4. `TransportEnvelopeValidator.resolve_error_code(reason)`
5. `TransportEnvelopeValidator.get_payload_schema(event_type)`
6. `RequestCorrelationTracker.register_request(envelope, ctx)`
7. `RequestCorrelationTracker.consume_request(request_id, terminal_event)`
8. `RequestCorrelationTracker.get_correlation_record(request_id)`
9. `RequestCorrelationTracker.prune_stale_requests()`
10. `RequestCorrelationTracker.is_replay(request_id)`
11. `VisibilityRouter.compute_terminal(event, room)`
12. `VisibilityRouter.filter_payload_for_role(payload, role, visibility)`
13. `VisibilityRouter.is_visible_to_user(user, event)`
14. `MessageBroadcaster.broadcast(campaign_id, event)`
15. `MessageBroadcaster.send_to_user(campaign_id, user_id, event)`
16. `RestApiGateway.convert_http_to_envelope(method, path, body, query)`
17. `RestApiGateway.convert_response_to_http(event)`
18. `TransportErrorFormatter.format_error(exception, ctx, request_id)`
19. `TransportErrorFormatter.format_denial(reason, event_type, ctx, request_id)`
20. `TransportErrorFormatter.format_validation_error(error, request_id)`

## Critical Flows

1. WebSocket connect lifecycle with token validation and session registration.
2. Command terminal response flow with correlation consumption.
3. Replay detection flow for duplicate request ids.
4. Visibility-aware broadcast flow by role and actor ownership.

## Context Objects

1. `WsEnvelope` as inbound command envelope.
2. `WsOutbound` as outbound terminal or state event envelope.
3. `RequestCorrelationRecord` with request and fulfillment metadata.
4. `VisibilityResolutionContext` with role and ownership scope.
5. `GatewayRequestContext` with auth claims, role, and campaign path params.

Mutability:

1. Inbound and outbound envelopes are immutable objects.
2. Correlation records mutate once from pending to fulfilled.
3. Visibility contexts are immutable per send operation.

## Constraints and Denial Mapping

Invariants:

1. Every command requires request id and exactly one terminal outcome.
2. Outbound visibility must align with event contract and recipient policy.
3. Duplicate request ids in replay window must not re-execute mutations.
4. Validation failures produce explicit error envelopes.

Reason-code families:

1. `invalid_message`
2. `unauthorized`
3. `forbidden`
4. `command_denied.*`
5. `action_denied.*`

## Recovery and Idempotency

1. Replay detection enables idempotent handling of retransmitted command ids.
2. Correlation pruning avoids stale pending records and false replay positives.
3. Delivery failures are logged and do not mutate command outcome semantics.
4. Rest-to-envelope conversions must be deterministic for same HTTP inputs.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`.
2. Contracts: `ISSUES/architecture/01_contracts/campaign/ISSUE_[CONTRACT]_[CAM-01]_campaign_management_context.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/SYSTEM_CRITICAL_FLOWS_SEQUENCE.mmd` and `ISSUES/architecture/01_contracts/overview/HORIZONTAL_CONTRACT_DETAIL_OVERVIEW.mmd`.
4. Code anchors: `backend/src/core/ws_dispatcher.py`, `backend/src/core/ws_protocol.py`, `backend/src/systems/dnd5e/ws_handler.py`.
