# Actions and Abilities Fully Data-Driven (Hybrid DB + JSON) Concept

Date: 2026-03-17
Status: Proposed

Primary references:

- [docs/architecture/backend/07_dnd5e_data_models.md](docs/architecture/backend/07_dnd5e_data_models.md)
- [docs/architecture/backend/17_ws_event_command_deck_next_stages.md](docs/architecture/backend/17_ws_event_command_deck_next_stages.md)
- [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py)

## 1. Goal

Make actions and abilities fully data-driven with a hybrid content model:

- DB is runtime authority,
- JSON packs are import/export/mod content source,
- runtime command deck projection is generated from data only.

## 2. Why Hybrid

DB-first only can reduce mod portability.
JSON-first only can reduce runtime governance and consistency.

Hybrid provides:

- deterministic runtime state and versioning in DB,
- mod-friendly content workflows via JSON packs,
- explicit ingestion pipeline with validation and conflict policy.

## 3. Canonical Domain Model

## 3.1 ActionDefinition

ActionDefinition fields (authoritative schema):

- action_id: string (stable key)
- name: string
- family: attack | save | healing | utility | feature
- action_type_cost: action | bonus_action | reaction | move | free
- targeting_mode: single_target | aoe | self
- range: number | null
- save_context: object | null
- attack_context: object | null
- resource_costs[]: object
- effect_intents[]: object
- tags[]: string
- source_ref: monster | class_feature | item | spell | custom
- content_version: string
- enabled: bool

## 3.2 AbilityBinding

AbilityBinding links ActionDefinition to an actor template or runtime actor:

- binding_id: string
- actor_template_id or actor_id
- action_id
- unlock_conditions[]
- override_payload (optional)

## 3.3 ContentPack

JSON import/export unit:

- pack_id
- system
- version
- actions[]
- abilities[]
- dependencies[]
- migration_notes

## 4. Runtime Projection Contract

Executable action snapshots sent to clients should be projected from ActionDefinition + AbilityBinding + runtime state.

Projection output fields:

- action_id
- label
- family
- action_type_cost
- is_available
- unavailable_reason
- targeting_mode
- range

Availability decisions must come from backend checks only.

## 5. Ingestion Pipeline

```mermaid
flowchart LR
    A[JSON Pack Import] --> B[Schema Validate]
    B --> C[Semantic Validate]
    C --> D[Conflict Policy]
    D --> E[DB Upsert Versioned]
    E --> F[Runtime Projection Cache Invalidate]
```

Validation stages:

1. Structural schema validation.
2. Semantic checks (targeting + cost + effect references).
3. Conflict policy:
   - reject_conflict,
   - overwrite_if_newer,
   - fork_namespace.

## 6. Modding Boundaries

Permitted mod content:

- new ActionDefinitions,
- additional AbilityBindings,
- data-level parameter overrides.

Restricted by policy:

- unsafe operation families,
- disallowed resolver operations,
- invalid effect references.

## 7. Rollout Strategy

1. Introduce ActionDefinition/AbilityBinding persistence.
2. Mirror existing inferred actions into definitions.
3. Enable projection from definitions behind feature flag.
4. Remove ad-hoc inference branches once parity is proven.

## 8. Acceptance Criteria

1. Action/ability behavior can be changed by data updates without code edits.
2. Executable action snapshots are generated from canonical data model.
3. JSON import/export round-trip preserves semantic equivalence.
4. Deterministic denied reasons remain stable across hybrid source changes.
5. Frontend action rendering depends only on backend-provided snapshots.
