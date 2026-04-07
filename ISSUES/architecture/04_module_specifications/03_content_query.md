# Module Annex: content_query

## Scope

Deterministic list/detail projection reads, hydration, and revision-aware query responses.

## Primary Classes

1. `ContentQueryService` for read orchestration.
2. `ListQueryExecutor` for deterministic list and pagination.
3. `DetailQueryExecutor` for detail retrieval and expansion.
4. `RevisionAwareProjector` for revision stamping and gap detection.
5. `HydrationOrchestrator` for eager relation hydration.
6. `LinkExpansionResolver` for linked graph traversal.
7. `QueryValidationPolicy` for query and expansion constraint checks.
8. `InvalidationCoordinator` for mutation-driven invalidation propagation.
9. `CacheInvalidationManager` for cache freshness and dirty marking.

## Externally Callable Methods (20+)

1. `ContentQueryService.list_definitions(query_spec, context)`
2. `ContentQueryService.get_definition_detail(definition_id, context)`
3. `ContentQueryService.search_definitions(search_params, context)`
4. `ContentQueryService.resolve_character_sheet_references(actor_id, context)`
5. `ContentQueryService.validate_query_parameters(...)`
6. `ListQueryExecutor.execute(filter_spec, pagination, context)`
7. `ListQueryExecutor.apply_filters(stmt, filter_spec)`
8. `ListQueryExecutor.apply_deterministic_ordering(stmt, sort_spec)`
9. `ListQueryExecutor.compute_pagination_bounds(limit, offset)`
10. `DetailQueryExecutor.fetch_definition(definition_id, context)`
11. `DetailQueryExecutor.fetch_with_expansion(definition_id, expansion_flags)`
12. `DetailQueryExecutor.resolve_replacement_target(definition_id)`
13. `DetailQueryExecutor.hydrate_linked_references(definition)`
14. `RevisionAwareProjector.project_with_revision_context(data, current_revision)`
15. `RevisionAwareProjector.detect_revision_gap(last_known_revision, current_revision)`
16. `RevisionAwareProjector.resolve_invalidation_strategy(gap)`
17. `HydrationOrchestrator.batch_hydrate(dependency_graph)`
18. `HydrationOrchestrator.hydrate_action_definitions(definition_ids)`
19. `HydrationOrchestrator.hydrate_effect_definitions(effect_ids)`
20. `LinkExpansionResolver.resolve_forward_links(definition_id, max_depth)`
21. `LinkExpansionResolver.resolve_reverse_links(definition_id)`
22. `InvalidationCoordinator.on_definition_updated(definition_id, changes, context)`
23. `CacheInvalidationManager.check_cache_validity(key, last_known_revision)`
24. `CacheInvalidationManager.increment_revision_after_mutation()`

## Method Contract Minimums

1. Deterministic ordering and stable pagination behavior must be explicit.
2. Revision metadata must be attached to all read-model responses.
3. Expansion and hydration failures must map to explicit denial or invalidation states.
4. Cache invalidation and replay interactions must preserve consistency guarantees.

## Critical Flows

1. Deterministic list query with filters and pagination.
2. Detail query with link expansion and replacement target resolution.
3. Async-safe hydration flow to prevent greenlet and N+1 issues.
4. Revision-gap detection and invalidation-required response flow.
5. Mutation-triggered cache invalidation and subscriber notification flow.
6. Character-sheet reference projection flow for hydrated definitions.

## Context Objects

1. `QueryExecutionContext` with `user_id`, `campaign_id`, `request_id`, `current_revision`.
2. `HydrationContext` with `db_session`, `eager_load_depth`, `memo`, `hydration_errors`.
3. `RevisionContext` with `last_known_revision`, `current_revision`, `gap_threshold`, `invalidation_triggered`.
4. `ProjectionContext` with read model type, target families, visibility filter, expansion flags.
5. `InvalidationContext` with mutation event, affected ids, strategy and cascade depth.

Mutability:

1. Execution and projection contexts are immutable.
2. Hydration context memo and error list are mutable inside single query boundary only.
3. Invalidation contexts are immutable once published to downstream processors.

## Constraints and Denial Mapping

Invariants:

1. Same query plus same revision returns deterministic ordering.
2. Revision gaps above threshold must trigger explicit invalidation guidance.
3. Link expansion must not create infinite traversal loops.
4. Hydration must remain async-session-safe.

Reason-code families:

1. `invalid_query_parameters`
2. `unsupported_sort_or_filter`
3. `definition_not_found`
4. `revision_gap_detected`
5. `expansion_depth_exceeded`
6. `hydration_failed`

## Recovery and Idempotency

1. Read requests are replay-safe and idempotent by definition.
2. Revision gap responses must include enough context for deterministic resync.
3. Cache invalidation is event-driven and must not silently suppress stale reads.
4. Hydration failures must permit controlled retries without altering persistent state.

## Traceability

1. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-03]_query_projection_consistency.md`.
2. Contracts: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-04]_content_query_projection.md`.
3. Contracts: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-02]_referential_integrity.md`.
4. Diagrams: `ISSUES/architecture/01_contracts/overview/SYSTEM_CRITICAL_FLOWS_SEQUENCE.mmd` and `ISSUES/architecture/01_contracts/overview/SYSTEM_CRITICAL_FLOWS_ACTIVITY.mmd`.
5. Code anchors: `backend/src/systems/dnd5e/content/api/router.py`, `backend/src/systems/dnd5e/content/domain/definition_models.py`.
