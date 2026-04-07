# Module Annex: events

## Scope

Domain event publication, ordering guarantees, visibility rules, and terminal-denial emission.

## Primary Classes

1. `EventEnvelope` immutable event contract container.
2. `EventPublisher` routing and publish orchestrator.
3. `EventLog` append-only persistence for replay and audit.
4. `EventCorrelationContext` request and trace correlation carrier.
5. `EventOrderingBuffer` causal sequencing queue.
6. `VisibilityFilter` recipient and payload filtering policy.

## Externally Callable Methods (10+)

1. `EventEnvelope.create(type, payload, request_id, visibility)`
2. `EventEnvelope.with_visibility(visibility, target_user_id=None)`
3. `EventEnvelope.to_dict()`
4. `EventEnvelope.is_denial()`
5. `EventPublisher.publish(event, context)`
6. `EventPublisher.publish_batch(events, context)`
7. `EventPublisher.get_replay_events_since(event_num, scope)`
8. `EventPublisher.compute_visibility(event_type, context)`
9. `EventLog.append(event, context)`
10. `EventLog.query_range(scope, from_event_num, to_event_num)`
11. `EventOrderingBuffer.enqueue(event)`
12. `EventOrderingBuffer.flush(ordering_key)`
13. `VisibilityFilter.should_send(user, event)`
14. `VisibilityFilter.filter_envelopes(user, envelopes)`
15. `EventCorrelationContext.from_session_context(session_context, request_id)`

## Critical Flows

1. Command ingress to resolved event publication.
2. Authorization denial to terminal denied event publication.
3. Turn-ordered multi-event sequencing flow.
4. Offline reconnect replay and visibility refilter flow.

## Context Objects

1. `EventCorrelationContext` with `request_id`, `correlation_id`, `ordering_key`, `campaign_id`.
2. `EventEnvelope` with type, payload, request_id, visibility and target.
3. `VisibilityResolutionContext` with role, ownership and campaign state.
4. `EventReplayWindow` with from-to event numbers and revision bounds.
5. `OrderingConstraint` with sequence and dependency metadata.

Mutability:

1. Event envelopes and correlation contexts are immutable.
2. Ordering buffer is mutable internal queue state only.
3. Replay windows are immutable query inputs.

## Constraints and Denial Mapping

Invariants:

1. Request id propagation is mandatory for command-derived events.
2. Event ordering per ordering key is monotonic.
3. Visibility assignment is immutable after publish.
4. Denied events are explicit and terminal.

Reason-code families:

1. `action_denied.*`
2. `command_denied.*`
3. `event_ordering.*`
4. `event_visibility.*`

## Recovery and Idempotency

1. Duplicate request ids should map to deterministic terminal event semantics.
2. Replay must preserve original ordering and visibility guarantees.
3. Event append and publish failures must be detectable through audit correlation ids.
4. Buffered ordering recovery must not reorder previously committed sequence numbers.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-03]_query_projection_consistency.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/SYSTEM_CRITICAL_FLOWS_SEQUENCE.mmd`.
4. Code anchors: `backend/src/systems/dnd5e/event_types.py`, `backend/src/systems/dnd5e/reason_codes.py`.
