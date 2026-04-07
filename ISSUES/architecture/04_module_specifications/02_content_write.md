# Module Annex: content_write

## Scope

Definition create/update/publish lifecycle and reference-safe mutation boundaries.

## Primary Classes

1. `DefinitionRecord` as base compendium definition model.
2. `LoreDefinition`, `SpeciesDefinition`, `ClassDefinition`, `ConditionDefinition` as family-specific models.
3. `ContentPackRecord` for pack grouping, lifecycle, and compatibility scope.
4. `LinkedEntryReference` for directional dependency edges.
5. `CompendiumApplicationService` for write-path orchestration.
6. `CompendiumUnitOfWork` for transactional boundaries.
7. `LifecycleTransitionPolicy` for legal state transition enforcement.
8. `LinkedEntryIntegrityPolicy` for link target and chain validation.

## Externally Callable Methods (20+)

1. `create_pack(pack)`
2. `get_pack(pack_id)`
3. `list_packs(lifecycle_state=None)`
4. `create_definition(definition, request_id=None, campaign_id=None)`
5. `get_definition(definition_id)`
6. `list_definitions(pack_id, family=None)`
7. `update_definition(definition_id, updates, expected_content_version, request_id=None, campaign_id=None)`
8. `delete_definition(definition_id, expected_content_version, request_id=None, campaign_id=None)`
9. `publish_definition(definition_id, request_id=None, campaign_id=None)`
10. `supersede_definition(old_definition_id, new_definition_id, request_id=None, campaign_id=None)`
11. `list_by_source_definition_id(source_def_id)`
12. `list_by_target_definition_id(target_def_id)`
13. `delete_by_source_definition_id(source_def_id)`
14. `get_replacement_target(source_def_id)`
15. `validate_target_family(source_family, target_family, relation_kind)`
16. `validate_required_targets_exist(links, target_lookup)`
17. `validate_published_targets_only(links, target_lookup)`
18. `validate_replacement_cycle_safety(source_id, replacement_target_id, lookup_fn)`
19. `deny_on_invalid_transition(current_state, target_state)`
20. `CompendiumUnitOfWork.commit()`
21. `CompendiumUnitOfWork.rollback()`

## Method Contract Minimums

1. Every mutation method defines optimistic version behavior.
2. Every mutation method defines denial reasons and side effects.
3. Every publish or supersede path defines link-integrity checks.
4. Every success path emits a mutation event with revision context.

## Critical Flows

1. Create definition draft flow.
2. Update definition with optimistic lock flow.
3. Publish definition with required-link and lifecycle checks.
4. Supersede definition with replacement-chain and cycle safety checks.
5. Delete definition with reverse-reference protection.
6. Mutation event emission and projection invalidation trigger flow.

## Context Objects

1. `ContentWriteContext` with ids, updates, version, request correlation.
2. `ContentMutationEvent` with event_type, definition_id, family, lifecycle_state, content_version.
3. `CompendiumUnitOfWork` with repos and transactional state.
4. `LinkResolutionContext` with lookup callbacks, unresolved refs, and strictness mode.

Mutability:

1. Write contexts are immutable.
2. Mutation events are immutable after emission.
3. Unit-of-work is mutable only within transaction scope.
4. Resolution contexts are immutable for deterministic publish validation.

## Constraints and Denial Mapping

Invariants:

1. `(pack_id, family, slug)` uniqueness must be preserved.
2. Lifecycle transitions must follow contract graph.
3. Strict required links must resolve to published targets.
4. Replacement links must be family-compatible and cycle-free.

Reason-code families:

1. `PACK_NOT_FOUND`, `DEFINITION_NOT_FOUND`
2. `DEFINITION_ID_CONFLICT`, `DUPLICATE_SLUG`, `VERSION_MISMATCH`
3. `IMMUTABLE_DEFINITION_ERROR`, `INVALID_LIFECYCLE_TRANSITION`
4. `LINKED_TARGET_NOT_FOUND`, `ILLEGAL_STATE_DEPENDENCY`, `CYCLE_DETECTED`, `INVALID_REPLACEMENT_TARGET`, `LINKED_TARGET_IN_USE`

## Recovery and Idempotency

1. Version mismatch requires read-refresh and retry.
2. Duplicate request ids should avoid duplicate mutation side effects where applicable.
3. Event emission must follow successful commit only.
4. Supersedence and publish actions must be replay-safe under same version preconditions.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-01]_pack_lifecycle.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-02]_referential_integrity.md`.
3. Contracts: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-02]_content_schema.md`.
4. Diagrams: `ISSUES/architecture/01_contracts/overview/MASTER_SYSTEM_CLASS_SPEC.mmd` and `ISSUES/architecture/01_contracts/overview/SYSTEM_CRITICAL_FLOWS_SEQUENCE.mmd`.
5. Code anchors: `backend/src/systems/dnd5e/content/domain/definition_models.py`, `backend/src/systems/dnd5e/content/domain/pack_models.py`, `backend/src/systems/dnd5e/content/api/router.py`.
