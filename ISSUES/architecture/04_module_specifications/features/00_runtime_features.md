# Feature Description: runtime

## Goal

Provide stable multiplayer session lifecycle and synchronized state delivery.

## Core Features

1. Deterministic session bootstrap and reconnect synchronization.
2. Role-aware event fanout and visibility routing.
3. Delegation support with effective identity switching.
4. Explicit terminal outcomes for every command envelope.

## User Outcomes

1. Players always receive authoritative current state.
2. DM controls are immediate and consistently broadcast.
3. Reconnects recover without hidden state drift.
