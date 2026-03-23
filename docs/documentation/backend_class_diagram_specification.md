# Backend Class Diagram Specification

Status: In Progress
Owner: Documentation + Backend

## Goal

Define a complete, viewable, and context-aware backend class diagram specification with property-level detail, split by architectural layer.

This specification follows the project rule that backend state is authoritative and frontend consumers only render server-provided state.

## Scope

In scope:

- Transport and session models.
- DND5e Pydantic schema layer.
- Service and domain DTOs involved in combat flow.
- ORM model layer for persistence interaction.

Out of scope:

- Frontend component types.
- Mock-only test helper classes.

## Source of Truth Files

- [backend/src/core/ws_protocol.py](../../backend/src/core/ws_protocol.py)
- [backend/src/core/sessions/models.py](../../backend/src/core/sessions/models.py)
- [backend/src/systems/dnd5e/event_types.py](../../backend/src/systems/dnd5e/event_types.py)
- [backend/src/systems/dnd5e/schemas/common.py](../../backend/src/systems/dnd5e/schemas/common.py)
- [backend/src/systems/dnd5e/schemas/enums.py](../../backend/src/systems/dnd5e/schemas/enums.py)
- [backend/src/systems/dnd5e/schemas/definitions.py](../../backend/src/systems/dnd5e/schemas/definitions.py)
- [backend/src/systems/dnd5e/schemas/instances.py](../../backend/src/systems/dnd5e/schemas/instances.py)
- [backend/src/systems/dnd5e/schemas/encounter.py](../../backend/src/systems/dnd5e/schemas/encounter.py)
- [backend/src/systems/dnd5e/schemas/contracts.py](../../backend/src/systems/dnd5e/schemas/contracts.py)
- [backend/src/systems/dnd5e/application/action_execution_service.py](../../backend/src/systems/dnd5e/application/action_execution_service.py)
- [backend/src/systems/dnd5e/services/combat_service.py](../../backend/src/systems/dnd5e/services/combat_service.py)
- [backend/src/systems/dnd5e/domain/authorization.py](../../backend/src/systems/dnd5e/domain/authorization.py)
- [backend/src/systems/dnd5e/domain/action_economy.py](../../backend/src/systems/dnd5e/domain/action_economy.py)
- [backend/src/systems/dnd5e/domain/action_resolution_pipeline.py](../../backend/src/systems/dnd5e/domain/action_resolution_pipeline.py)
- [backend/src/systems/dnd5e/lib/combat_models.py](../../backend/src/systems/dnd5e/lib/combat_models.py)
- [backend/src/systems/dnd5e/lib/context_models.py](../../backend/src/systems/dnd5e/lib/context_models.py)
- [backend/src/systems/dnd5e/lib/content_models.py](../../backend/src/systems/dnd5e/lib/content_models.py)
- [backend/src/campaigns/lib/campaign.py](../../backend/src/campaigns/lib/campaign.py)
- [backend/src/campaigns/lib/character.py](../../backend/src/campaigns/lib/character.py)
- [backend/src/identity/models.py](../../backend/src/identity/models.py)

## Diagram Index

Shared conventions:

- [docs/diagrams/d2/\_legend.d2](../diagrams/d2/_legend.d2)

Layered diagrams:

- [docs/diagrams/d2/D2.1_transport_session.d2](../diagrams/d2/D2.1_transport_session.d2)
- [docs/diagrams/d2/D2.2_schema_primitives_enums.d2](../diagrams/d2/D2.2_schema_primitives_enums.d2)
- [docs/diagrams/d2/D2.3_definitions_contracts.d2](../diagrams/d2/D2.3_definitions_contracts.d2)
- [docs/diagrams/d2/D2.4_runtime_instances_encounter.d2](../diagrams/d2/D2.4_runtime_instances_encounter.d2)
- [docs/diagrams/d2/D2.5_event_payload_models.d2](../diagrams/d2/D2.5_event_payload_models.d2)
- [docs/diagrams/d2/D2.6_services_application_dtos.d2](../diagrams/d2/D2.6_services_application_dtos.d2)
- [docs/diagrams/d2/D2.7_domain_policy_objects.d2](../diagrams/d2/D2.7_domain_policy_objects.d2)
- [docs/diagrams/d2/D2.8_persistence_orm_models.d2](../diagrams/d2/D2.8_persistence_orm_models.d2)

## Backend Is Truth

Authoritative runtime state classes:

- EncounterState and nested ActorInstance graph in schema runtime layer.
- SessionContext for request identity and role semantics.
- EncounterSession and related ORM records for persisted combat continuity.

Derived or projection classes:

- Outbound payload classes in event_types are delivery projections.
- ActionExecutionResult and domain result wrappers are orchestration outputs.

Design implication:

- Frontend clients should treat outbound event payloads as snapshots from backend authority and should not compute independent combat truth.

## D2 Diagram Rules

Field-level requirements:

- Include all fields for schema and ORM classes.
- Include key methods only for service and orchestration classes where behavior context is necessary.

Edge semantics:

- Solid edge: ownership, composition, or direct association.
- Dashed edge: dependency, lookup, or service usage.
- Label every non-obvious edge with relationship meaning.

Readability constraints:

- Keep each diagram focused to a single layer or bounded concern.
- Prefer splitting large model groups into additional files rather than collapsing field detail.

## Pydantic Modularization Analysis

This section is proposal-only for now.

### Candidate 1: event_types.py

Current state:

- High-density payload file with mixed command, response, and system payloads.

Split proposal:

- event_types/inbound.py
- event_types/outbound.py
- event_types/conditions.py
- event_types/damage_healing.py
- event_types/system.py

Expected gain:

- Lower cognitive load and clearer ownership by payload direction and concern.

Primary risk:

- Import churn in ws handler and tests relying on legacy path.

### Candidate 2: schemas/common.py

Current state:

- Shared primitives, spell metadata, and character-building helpers all in one file.

Split proposal:

- schemas/common/ability_stats.py
- schemas/common/spatial.py
- schemas/common/spell_components.py
- schemas/common/character_building.py

Expected gain:

- Better cohesion and reuse boundaries.

Primary risk:

- Broad import touch points across definitions and instances.

### Candidate 3: schemas/definitions.py

Current state:

- Compendium definitions mixed with character-building model definitions.

Split proposal:

- schemas/definitions/compendium.py
- schemas/definitions/character_building.py

Expected gain:

- Clearer distinction between always-used runtime references and staged character-building definitions.

Primary risk:

- Existing type imports for common level features and trait references.

### Candidate 4: schemas/instances.py

Current state:

- Actor runtime, effect runtime, spellcasting, and inventory state in a single module.

Split proposal:

- schemas/instances/actor.py
- schemas/instances/effects.py
- schemas/instances/spellcasting.py
- schemas/instances/inventory.py

Expected gain:

- Easier focused testing of effect and action-economy logic.

Primary risk:

- Circular import pressure if model ownership boundaries are not explicit.

## Implementation Status

Completed in this phase:

- Created D2 diagram source set with layer partitioning.
- Added field-level class coverage across transport, schema, DTO/domain, and persistence diagrams.
- Added master specification document and navigation index.
- Added proposal-only modularization section for Pydantic split candidates.

Next implementation increments:

- Render diagram sources to svg assets and add links.
- Add automated drift checks between source models and diagram files.
- Optionally split high-density diagram files if class count increases.

## Verification Commands

- docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
- docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
- docker compose logs backend --tail=200
