# Feature Description: events

## Goal

Deliver ordered, correlated, visibility-safe event propagation for all runtime interactions.

## Core Features

1. Immutable event envelopes with request correlation.
2. Causal ordering for turn and command sequences.
3. Role and ownership visibility filtering.
4. Replay-capable event log behavior for recovery paths.

## User Outcomes

1. Clients receive consistent event timelines.
2. Denials and state updates are explicit and auditable.
3. Reconnect and replay behavior remains deterministic.
