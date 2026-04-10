# Batch D Migration Overview

## Scope

Batch D covers the resilience modules:

1. assets
2. events
3. recovery

Source documents analyzed:

1. ISSUES/architecture/04_module_specifications/07_assets.md
2. ISSUES/architecture/04_module_specifications/08_events.md
3. ISSUES/architecture/04_module_specifications/09_recovery.md
4. ISSUES/architecture/04_module_specifications/features/07_assets_features.md
5. ISSUES/architecture/04_module_specifications/features/08_events_features.md
6. ISSUES/architecture/04_module_specifications/features/09_recovery_features.md

Evidence sources used for state recommendations:

1. ISSUES/architecture/01_contracts/APPROVAL_LOG.md
2. ISSUES/architecture/01_contracts/FREEZE_GATE_STATUS.md
3. ISSUES/architecture/01_contracts/scorecards/07_assets_scorecard.md
4. ISSUES/architecture/01_contracts/scorecards/08_events_scorecard.md
5. ISSUES/architecture/01_contracts/scorecards/09_recovery_scorecard.md

## Migration Rule

Keep architecture module files in place as canonical source docs.
Create or place executable FLOW tickets that reference those files.

## Batch D File-to-State Mapping

| Actual file                                                                   | Recommended FLOW state | Confidence  | Why this state                                                                                                                      |
| ----------------------------------------------------------------------------- | ---------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| ISSUES/architecture/04_module_specifications/07_assets.md                     | 01_PLANNING            | High        | Frozen contract but no substantial assets implementation layer currently present.                                                   |
| ISSUES/architecture/04_module_specifications/features/07_assets_features.md   | 01_PLANNING            | High        | Feature outcomes depend on missing assets module classes and persistence wiring.                                                    |
| ISSUES/architecture/04_module_specifications/08_events.md                     | 01_PLANNING            | High        | Partial event scaffolding exists, but core event envelope, ordering, and visibility infrastructure needs extraction and completion. |
| ISSUES/architecture/04_module_specifications/features/08_events_features.md   | 01_PLANNING            | High        | Deterministic event/replay outcomes depend on missing event orchestration primitives.                                               |
| ISSUES/architecture/04_module_specifications/09_recovery.md                   | 00_BACKLOG             | Medium-High | Recovery is downstream and currently lacks concrete implementation anchors and checkpoint infrastructure.                           |
| ISSUES/architecture/04_module_specifications/features/09_recovery_features.md | 00_BACKLOG             | Medium-High | Recovery features are blocked by events maturity and projection consistency hardening.                                              |

## Overlapping Existing FLOW Ticket

Indirect overlap:

1. ISSUES/FLOW/03_IN_PROGRESS/FEATURE_frontend_compendium_ui_master_blueprint.md

Practical impact:

1. Frontend work may consume event notifications, but Batch D module completion is not yet in active execution.

## Practical Next Placement Actions

1. Keep assets and events module artifacts mapped to 01_PLANNING while implementation parent tickets are created.
2. Keep recovery module artifacts mapped to 00_BACKLOG until events and projection consistency dependencies mature.
3. Sequence promotion: events or assets planning first, recovery only after upstream readiness.

## Blocking Notes

assets blockers before promotion to 02_READY:

1. Missing asset registry and ownership service primitives.
2. Missing persistence and authorization integration for asset lifecycle.
3. Missing end-to-end module tests for validation and policy denials.

events blockers before promotion to 02_READY:

1. Missing extracted event envelope and ordering buffer components.
2. Missing formal visibility filter component and deterministic replay coverage.
3. Missing integrated test suite for ordering, visibility, and replay behavior.

recovery blockers before promotion from 00_BACKLOG:

1. Depends on mature events ordering and replay guarantees.
2. Depends on query/projection consistency checkpoints and drift detection infrastructure.
3. Requires dedicated recovery state and checkpoint persistence model.
