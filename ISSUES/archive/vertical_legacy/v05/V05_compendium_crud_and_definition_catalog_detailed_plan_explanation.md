# V05 Detailed Plan Explanation: Compendium CRUD and Definition Catalog

This file explains the architecture in:

- V05_compendium_crud_and_definition_catalog_detailed_plan.mmd

## 1. Structural Overview

This module is not one service. It is a layered system with strict ownership boundaries.

Structural slices:

1. Catalog Core slice
- Source-of-truth definitions and content packs.

2. Integrity slice
- Linked-entry graph and replacement-chain correctness.

3. Lifecycle slice
- Draft, publish, archive, restore, supersede transitions.

4. Query/Index slice
- Searchable projection documents with deterministic ordering.

5. Transport slice
- REST and optional WS mapping to stable contracts.

6. Projection boundary slice
- Frontend read-model expectations and invalidation rules.

7. Quality gate slice
- Tests that prove the structure is deterministic.

Why structured this way:

1. Write correctness and read performance are different concerns.
2. Link integrity cannot be left to UI heuristics.
3. Lifecycle transitions require explicit domain rules.
4. Frontend needs revision-aware contracts, not inferred state.

## 2. Dependency Direction (Hard Rule)

Allowed direction only:

1. TransportLayer -> ApplicationLayer
2. ApplicationLayer -> PolicyLayer
3. ApplicationLayer -> RepositoryLayer
4. RepositoryLayer -> persistence only
5. EventContracts and FrontendProjectionBoundary are contract targets, not rule owners

Forbidden direction examples:

1. TransportLayer -> RepositoryLayer direct writes
2. FrontendProjectionBoundary -> PolicyLayer business decisions
3. SearchIndexRepository -> DefinitionRepository mutation side effects

Why this matters:

1. Prevents split-brain logic.
2. Makes testing predictable.
3. Keeps backend as truth authority.

## 3. Namespace Structure And Responsibilities

## ContentDomain (state model)

What it owns:

1. DefinitionRecord
2. ContentPackRecord
3. LinkedEntryReference
4. ReplacementChain
5. CatalogRevision
6. IndexDocument
7. ContentQueryRequest and ContentQueryResult
8. V05Invariants

What it does not own:

1. HTTP behavior
2. Database transaction orchestration
3. UI rendering

## PolicyLayer (rule engine)

What it owns:

1. Contract validity rules
2. Lifecycle transition legality
3. Linked-entry and cycle rules
4. Visibility permissions
5. Query determinism rules

What it does not own:

1. Data writes
2. Event publication
3. Endpoint logic

## ApplicationLayer (use-case orchestration)

What it owns:

1. Request-level orchestration order
2. Policy invocation sequence
3. Repository call sequence
4. Mutation result envelope

What it does not own:

1. SQL/ORM details
2. Route parsing

## RepositoryLayer (persistence boundaries)

What it owns:

1. Storage operations by aggregate type
2. Transaction commit/rollback via UnitOfWork

What it does not own:

1. Cross-aggregate business decisions
2. Denial taxonomy

## TransportLayer (adapters)

What it owns:

1. REST and WS command/response mapping
2. Outbound event mapping shape

What it does not own:

1. Lifecycle legality
2. Link graph validation
3. Revision semantics

## EventContracts (integration contract surface)

What it owns:

1. Outbound event shape families
2. Stable fields for projection updates and denied outcomes

What it does not own:

1. Event production rules (those remain in Application + Policy)

## FrontendProjectionBoundary (consumer contract)

What it owns:

1. Expected read-model behavior
2. Invalidation triggers
3. Replacement-chain consumption behavior

What it does not own:

1. Domain mutation
2. Policy decisions

## TestingAndGate (closure structure)

What it owns:

1. Completion criteria for deterministic behavior
2. Enforcement that every structural layer is covered

What it does not own:

1. Runtime features

## 4. Ownership Matrix (Who Writes What)

1. Definition records
- Write owner: CompendiumApplicationService
- Repository path: DefinitionRepository

2. Lifecycle state fields
- Write owner: ContentLifecycleApplicationService
- Repository path: DefinitionRepository and ContentPackRepository

3. Linked-entry graph
- Write owner: CompendiumApplicationService after LinkedEntryIntegrityPolicy pass
- Repository path: LinkedEntryRepository

4. Catalog revision
- Write owner: application services at terminal mutation step
- Repository path: CatalogRevisionRepository

5. Search index projection
- Write owner: application services after successful mutation and revision creation
- Repository path: SearchIndexRepository

Single-writer rule:

1. Each mutable aggregate has exactly one orchestrating service owner.
2. If more than one service can write same field, structure is broken.

## 5. Transaction Boundary Structure

Atomic mutation unit should include:

1. Definition change
2. Linked-entry change
3. Revision creation
4. Index update marker

Commit order intent:

1. Validate policies first
2. Persist source-of-truth state
3. Create revision
4. Apply/queue index projection with that revision
5. Emit events mapped to same revision context

Why this order:

1. Prevents event/index drift from source-of-truth state.

## 6. Proposed Implementation Layout (Concrete Structure)

This is a suggested code layout for this module structure.

backend/src/systems/dnd5e/content/
	domain/
		definition_models.py
		pack_models.py
		link_models.py
		revision_models.py
		invariants.py
	policies/
		definition_contract_policy.py
		lifecycle_transition_policy.py
		linked_entry_integrity_policy.py
		visibility_policy.py
		query_determinism_policy.py
	application/
		compendium_application_service.py
		content_lifecycle_application_service.py
		linked_entry_resolution_service.py
		content_query_application_service.py
		result_models.py
	repositories/
		definition_repository.py
		content_pack_repository.py
		linked_entry_repository.py
		search_index_repository.py
		catalog_revision_repository.py
		unit_of_work.py
	transport/
		rest_compendium_router.py
		ws_content_stream_handler.py
		content_events_mapper.py
	contracts/
		content_events.py
		content_payloads.py
	tests/
		contract/
		ownership/
		linked_entry/
		query/
		parity/

## 7. Critical Structural Invariants

1. A definition cannot be published if required links are unresolved.
2. Replacement chains must stay acyclic.
3. Query pagination must be deterministic under same revision.
4. Revision must be monotonic and tied to mutation outcomes.
5. Frontend invalidation must be revision-driven, not time-driven.

## 8. Why This System Should Be Constructed This Way

1. It scales by adding definition families without rewriting orchestration rules.
2. It keeps UI complexity lower because backend provides stable projection contracts.
3. It prevents data corruption from hidden cross-layer writes.
4. It supports hybrid play use case where content lookup quality is more important than combat automation.
5. It creates a testable architecture where failures are attributable to one structural layer.

## 9. If You Only Remember Five Things

1. Domain holds truth, not routers.
2. Policies decide legality, not repositories.
3. Application layer is the single orchestrator.
4. Revisions are the backbone of consistency.
5. Tests gate structure, not just features.