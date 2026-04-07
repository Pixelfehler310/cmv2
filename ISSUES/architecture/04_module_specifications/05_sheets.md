# Module Annex: sheets

## Scope

Character write-path integration, sheet projection, reference resolution, and invalidation behavior.

## Primary Classes

1. `CharacterSheetProjector` for deterministic projection assembly.
2. `CharacterSheetHydrator` for dependency fetch and composed projection hydration.
3. `CharacterWriteIntegrator` for mutation-to-invalidation bridge.
4. `ReferenceResolver` for required link resolution and denial mapping.
5. `SheetInvalidationManager` for invalidation and recovery coordination.
6. `SheetProjectionCache` for revision-scoped cached projection reuse.

## Externally Callable Methods (10+)

1. `CharacterSheetProjector.project(character_id, catalog_revision)`
2. `CharacterSheetProjector.validate_projection_shape(projection)`
3. `CharacterSheetHydrator.hydrate_character_sheet(character_id, campaign_id, async_mode=True)`
4. `CharacterSheetHydrator.apply_visibility_policies(projection, viewer_context)`
5. `CharacterSheetHydrator.track_hydration_performance(hydration_job_id)`
6. `CharacterWriteIntegrator.ingest_character_mutation(mutation)`
7. `CharacterWriteIntegrator.schedule_invalidation_job(character_id, reason_code)`
8. `CharacterWriteIntegrator.confirm_mutation_published(write_request_id, character_id)`
9. `ReferenceResolver.resolve_character_definitions(character_id, campaign_id, context)`
10. `ReferenceResolver.prevalidate_reference_ids(character_id, reference_id_list)`
11. `SheetInvalidationManager.initiate_invalidation(trigger_event)`
12. `SheetInvalidationManager.recover_from_invalidation(invalidation_request_id)`
13. `SheetInvalidationManager.check_invalidation_status(character_id)`

## Critical Flows

1. Character sheet hydrate and projection publish flow.
2. Character mutation ingestion and invalidation scheduling flow.
3. Reference resolution denied flow with unresolved id reporting.
4. Invalidation recovery retry flow with deadline behavior.

## Context Objects

1. `SheetProjectionRequest` with `character_id`, `campaign_id`, `catalog_revision`, `correlation_id`.
2. `ViewerContext` with role and visibility scope.
3. `CharacterMutationContext` with operation id and expected revision.
4. `ResolutionContext` with campaign ownership and strictness mode.
5. `InvalidationTriggerContext` with source operation and recovery deadline.

Mutability:

1. Projection and resolution contexts are immutable.
2. Invalidation state is mutable only within invalidation manager.
3. Cached projections are immutable snapshots keyed by revision.

## Constraints and Denial Mapping

Invariants:

1. Required class and species references must resolve.
2. Projection revisions are monotonic per character.
3. Denied projections include reason code and unresolved references.
4. Cross-campaign reference resolution is forbidden.

Reason-code families:

1. `UNRESOLVED_CLASS_DEFINITION`
2. `UNRESOLVED_SPECIES_DEFINITION`
3. `MISSING_REQUIRED_FIELD`
4. `CATALOG_REVISION_MISMATCH`
5. `CAMPAIGN_OWNERSHIP_VIOLATION`
6. `RECOVERY_DEADLINE_EXCEEDED`

## Recovery and Idempotency

1. Same correlation id must deduplicate mutation ingestion.
2. Re-projection for same `(character_id, catalog_revision)` is idempotent.
3. Recovery retries preserve request and invalidation correlation.
4. Failed recovery must terminate with explicit irrecoverable reason code.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-05]_character_and_sheet_schema.md`.
2. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-03]_query_projection_consistency.md`.
3. Diagrams: `ISSUES/architecture/01_contracts/overview/MASTER_SYSTEM_CLASS_SPEC.mmd` and `ISSUES/architecture/01_contracts/overview/SYSTEM_CRITICAL_FLOWS_ACTIVITY.mmd`.
4. Code anchors: `backend/src/schemas/character.py`, `backend/src/systems/dnd5e/engine/character_builder.py`.
