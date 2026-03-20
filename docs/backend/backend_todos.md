# Backend Architecture and Refactoring Todos

This document outlines partially implemented features, missing features, and outdated functionality in the backend, parsed into actionable 1-PR scoped tasks.

## 1. Extract Business Logic from `ws_handler.py`
**Problem:** `ws_handler.py` is nearly 100KB and leaks massive amounts of combat business logic (action preview generation, budget deductions, and effect intents resolution) that should be strictly in the `CombatService` or `ActionResolver`.
**1-PR Fix Concept:** Move all target eligibility (preview) checks and nested budget calculations into the `CombatService.check_can_act` and action resolver pipeline. Refactor `ws_handler.py` so it strictly deserializes `WsEnvelope` payloads, checks initial role permissions, delegates directly to the service, and constructs the resulting `WsOutbound` responses. Add unit tests ensuring the router itself contains no rule-engine math.

## 2. Enforce Database Persistence for Encounters
**Problem:** The current real-time system caches the `EncounterState` in an in-memory `_encounters` dict singleton (MVP hack) rather than reliably streaming mutations to the `AsyncSessionLocal` database.
**1-PR Fix Concept:** Completely remove the `_encounters` singleton from the system. Update the initial websocket connection handler to exclusively fetch the `EncounterState` from the database via `CombatService._load_session()`. Ensure that all terminal action resolvers trigger a `save_full_state()` before broadcasting the state-sync back to the users.

## 3. Standardize Campaign Connection Lifecycle (Missing Feature)
**Problem:** With the legacy `campaigns/router.py` JSON engine removed, campaigns currently lack a dedicated lifecycle hook to construct their native D&D `EncounterState` upon creation.
**1-PR Fix Concept:** Update the `create_campaign` endpoint in `campaigns/routers/campaigns.py` to immediately initialize and persist an empty D&D 5e `EncounterState` to the database right after the `Campaign` model is committed. Ensure this starting state conforms to the latest Phase 2-4 schemas (including an empty `MapState` and properly dimensioned grid).

## 4. Granular Actor Tracking Resources (Missing Feature)
**Problem:** The system tracks Hit Points and strict `TurnBudgets` (Actions, Bonus Actions), but lacks a system for tracking granular sub-resources like Sorcery Points, Ki, or Battlemaster Superiority Dice.
**1-PR Fix Concept:** Introduce a `ResourceTracker` sub-model to the `ActorInstance` schema that stores key-value pairs of string limits (e.g. `{"ki": {"current": 4, "max": 4}}`). Inject a new stateless calculation stage into the `action_resolver.py` that asserts a requested action's `ActionDefinition` cost matches available pools and deducts the precise resource alongside the standard Turn Budget. 
