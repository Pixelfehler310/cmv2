# ISSUE [CONTRACT] [CORE-03]: Query and Projection Consistency

## Why This Exists
Query correctness and projection convergence require explicit revision contracts so clients do not rely on timing heuristics or stale caches.

## Consistency Model
1. Queries execute on a fixed revision snapshot.
2. Mutations create one monotonic catalog revision.
3. Events carry revision metadata.
4. Consumers detect revision gaps and trigger invalidation or targeted refetch.

## Required Contract Fields
1. `request_id`
2. `catalog_revision`
3. `status` (`resolved`, `denied`, `error`)
4. `reason_code` for denied and error outcomes
5. `affected_definition_ids` for projection updates

## Projection Rules
1. Same input + same revision must yield deterministic ordering.
2. If incoming revision is greater than current + 1, consumer must invalidate scope.
3. Recovery policy must define full resync and targeted refetch paths.

## Mermaid Sequence Diagram
```mermaid
sequenceDiagram
    participant Client
    participant Pipeline
    participant QueryStage
    participant MutationStage
    participant ProjectionStage
    participant Store

    Client->>Pipeline: request envelope(request_id)
    Pipeline->>QueryStage: resolve revision snapshot
    QueryStage-->>Pipeline: query result + revision
    Pipeline->>ProjectionStage: build read model
    ProjectionStage-->>Store: content_projection_updated(catalog_revision)
    Store-->>Client: cache apply

    Client->>Pipeline: mutation envelope(request_id)
    Pipeline->>MutationStage: persist mutation
    MutationStage-->>Pipeline: new catalog_revision
    Pipeline->>ProjectionStage: emit update or invalidation
    ProjectionStage-->>Store: content_invalidation_required (if gap)
```

## Extracted From
1. `ISSUES/archive/vertical_legacy/v05/V05_content_management_query_and_projection_detailed_plan.mmd`
2. `ISSUES/archive/vertical_legacy/v05/V05_content_management_query_and_projection_detailed_plan_explanation.md`

## Canonical Symbols
1. `SearchIndexRepository` contract semantics in `backend/src/systems/dnd5e/content/infrastructure/search_index_repository.py`
2. `ContentMutationEvent` in `backend/src/systems/dnd5e/content/application/services.py`
