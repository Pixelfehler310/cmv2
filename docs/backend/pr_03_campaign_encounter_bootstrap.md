# PR Concept: Campaign Encounter Bootstrap

## Overview
Currently, the REST API successfully manages the creation of new `Campaign` objects and handles user enrollment (DM/Player roles). However, because of the legacy removal of the old JSON state router, a freshly created campaign lacks a pre-initialized D&D 5e `EncounterState` in the database. When the Virtual Tabletop loads, the WebSocket handler attempts to pull an encounter that hasn't been instantiated.

## 1-PR Scoped Fix Concept

### Objective
Ensure that every successful `Campaign` creation operation synchronously bootstraps a default, valid `EncounterState` Pydantic schema and saves it to the database so it is immediately ready for WebSocket connections.

### Acceptance Criteria
1. Whenever `POST /campaigns` successfully creates a campaign DB row, the engine must serialize a structurally perfect `EncounterState` (with defaults like a 40x40 `MapState`, turn index 0, and an empty combatant list) and associate it to that campaign ID.
2. The WebSocket `on_connect` hook should cleanly pull this empty state without needing to resort to "hardcoded mock encounters" (which currently injects "Arannis" and a "Goblin").

### Execution Steps
1. Open `backend/src/campaigns/routers/campaigns.py`.
2. Locate the `create_campaign()` function pipeline.
3. Import the `EncounterState` model from `systems.dnd5e.schemas.encounter`.
4. Right after `db.commit()` of the new Campaign ORM model, instantiate `EncounterState(id=uuid(), campaign_id=new_campaign.id)`.
5. Insert this serialized state into the `encounter_sessions` table via the `AsyncSession`.
6. Remove the hardcoded "Arannis/Goblin" MVP fallback logic from `ws_handler.py`.
