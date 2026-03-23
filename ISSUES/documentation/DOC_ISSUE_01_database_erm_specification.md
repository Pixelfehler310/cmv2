# DOC ISSUE 01: Full Database ERM Specification

Status: Planned  
Owner: Documentation + Backend

## Goal

Produce a complete, authoritative ERM document for the backend database layer, including entities, attributes, relationships, cardinalities, and persistence ownership boundaries.

Target output document:

- docs/documentation/database_erm_specification.md

## Scope

In scope:

- All SQLAlchemy-backed persistent entities.
- Relationships between campaign, identity, encounter/session, context catalog, and action execution data.
- Mermaid erDiagram with supporting table-by-table attribute notes.
- Data ownership notes (which service/repository writes each aggregate).

Out of scope:

- Frontend view models.
- Pure in-memory runtime snapshots that are not persisted.

## Important Source Files

Core persistence and app wiring:

- backend/src/database.py
- backend/src/main.py

Campaign and identity models:

- backend/src/campaigns/lib/campaign.py
- backend/src/campaigns/lib/character.py
- backend/src/identity/models.py

DnD5e persisted combat/context/content models:

- backend/src/systems/dnd5e/lib/combat_models.py
- backend/src/systems/dnd5e/lib/context_models.py
- backend/src/systems/dnd5e/lib/content_models.py

Repositories defining effective persistence behavior:

- backend/src/systems/dnd5e/repositories/encounter_session_repository.py
- backend/src/systems/dnd5e/repositories/context_repository.py
- backend/src/systems/dnd5e/repositories/action_execution_repository.py
- backend/src/systems/dnd5e/repositories/action_catalog_repository.py

## Deliverables

1. Canonical ERM diagram (Mermaid erDiagram) with relationship cardinalities.
2. Entity catalog table with fields, PK/FK constraints, and nullable/default rules.
3. Section on known drift (if model code and DB backfill logic diverge).
4. Verification checklist for schema-level sanity.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -q
3. docker compose logs backend --tail=200
