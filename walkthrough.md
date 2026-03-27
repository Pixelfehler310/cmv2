# V05: From Architecture to Action

In addition to finalizing the V05 Architecture diagrams (Business Entities & Macro-Architecture), I've fully transformed the 7 theoretical V05 tickets into **Actionable Developer Specs**.

## What was updated?

The 7 tickets in `ISSUES/architecture/v05/` now provide step-by-step code guidance:

1.  **[V05-01] Baseline and Drift Audit**: Added commands for DB dumping and type comparison.
2.  **[V05-02] Definition Contract Freeze**: Instructions to create `backend/src/modules/compendium/domain/models.py` using Pydantic, merging `AbilityDefinition`, and throwing base validators.
3.  **[V05-03] Repository Boundary Lock**: Instructions to use SQLAlchemy `Base` with `JSONB` payloads for polymorphic shapes alongside clear Unit-of-Work boundaries.
4.  **[V05-04] CRUD Application Orchestration**: The business logic layer. Added conditions to safely block `updates` on `published` entities and to orchestrate the `supersede` chain.
5.  **[V05-05] REST/WS Content Streams**: Outlined FastAPI endpoints (`POST /api/compendium/definitions`) mapping HTTP limits and throwing `ContentLifecycleEvents` to WebSockets.
6.  **[V05-06] Indexing and Linked-Entry**: Defined the `LinkedEntryResolutionService` for cyclic graph parsing and the Event-driven asynchronous ReadModel indexer for full-text caching.
7.  **[V05-07] Test Matrix**: Checklists for testing the end-to-end "Homebrew Publishing Flow" and testing broken API payloads against the Pydantic contracts.

With these files rewritten, developers can move seamlessly from the V05 diagrams directly into writing code module by module.
