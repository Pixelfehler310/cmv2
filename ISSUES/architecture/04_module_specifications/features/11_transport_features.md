# Feature Description: transport

## Goal

Normalize REST and WebSocket traffic into contract-safe envelopes with strict correlation and visibility behavior.

## Core Features

1. Inbound and outbound envelope schema validation.
2. Request-id correlation and replay detection.
3. Visibility-aware routing and targeted broadcasting.
4. Deterministic terminal error and denial mapping.

## User Outcomes

1. Command lifecycle is consistent across transport channels.
2. Duplicate transmission does not double-execute mutations.
3. Visibility leaks are prevented by policy-bound routing.
