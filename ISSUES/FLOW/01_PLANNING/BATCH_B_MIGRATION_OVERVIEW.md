# Batch B Migration Overview

## Scope

Batch B covers the data core modules:
1. content_write
2. content_query
3. shared

Source documents analyzed:
1. ISSUES/architecture/04_module_specifications/02_content_write.md
2. ISSUES/architecture/04_module_specifications/03_content_query.md
3. ISSUES/architecture/04_module_specifications/10_shared.md
4. ISSUES/architecture/04_module_specifications/features/02_content_write_features.md
5. ISSUES/architecture/04_module_specifications/features/03_content_query_features.md
6. ISSUES/architecture/04_module_specifications/features/10_shared_features.md

Evidence sources used for state recommendations:
1. ISSUES/architecture/01_contracts/APPROVAL_LOG.md
2. ISSUES/architecture/01_contracts/FREEZE_GATE_STATUS.md
3. ISSUES/architecture/01_contracts/scorecards/02_content_write_scorecard.md
4. ISSUES/architecture/01_contracts/scorecards/03_content_query_scorecard.md
5. ISSUES/architecture/01_contracts/scorecards/10_shared_scorecard.md

## Migration Rule

Keep architecture module files in place as canonical source docs.
Create or place executable FLOW tickets that reference those files.

## Batch B File-to-State Mapping

| Actual file | Recommended FLOW state | Confidence | Why this state |
|---|---|---|---|
| ISSUES/architecture/04_module_specifications/02_content_write.md | 02_READY | High | Frozen with strong implementation anchors in compendium application service, lifecycle policies, and tests. |
| ISSUES/architecture/04_module_specifications/features/02_content_write_features.md | 02_READY | High | Draft/publish/supersede outcomes are testable with existing service and integration coverage. |
| ISSUES/architecture/04_module_specifications/03_content_query.md | 01_PLANNING | High | Frozen contract, but query service execution and pagination or hydration wiring are still incomplete. |
| ISSUES/architecture/04_module_specifications/features/03_content_query_features.md | 01_PLANNING | High | Deterministic projection outcomes depend on content_query service completion and revision-aware execution. |
| ISSUES/architecture/04_module_specifications/10_shared.md | 02_READY | Medium-High | Shared reason-code and schema primitives exist; remaining work is consolidation and consistency hardening. |
| ISSUES/architecture/04_module_specifications/features/10_shared_features.md | 02_READY | Medium-High | Error and denial semantics are largely available and can be finalized through shared-layer cleanup. |

## Overlapping Existing FLOW Ticket

Direct overlap and dependency:
1. ISSUES/FLOW/03_IN_PROGRESS/FEATURE_frontend_compendium_ui_master_blueprint.md

Practical impact:
1. Frontend compendium work depends on stable content_write and content_query behavior.
2. content_query remaining gaps are a near-term blocker for robust list/detail UI behavior.

## Practical Next Placement Actions

1. Keep content_write and shared module artifacts mapped to 02_READY through linked execution tickets.
2. Keep content_query module artifacts mapped to 01_PLANNING until service execution and revision-aware projection are fully scoped.
3. Add a dedicated planning ticket for content_query service completion before any promotion to 02_READY.

## Blocking Notes

content_query blockers before promotion to 02_READY:
1. Completion of list/detail query execution service path.
2. Revision-aware projection and gap handling with deterministic behavior.
3. Integration verification aligned with compendium endpoint usage.

shared hardening blockers before 04_REVIEW:
1. Consolidate reason-code registry behavior into a stable shared pattern.
2. Verify denial/error envelope propagation consistency across transport paths.
