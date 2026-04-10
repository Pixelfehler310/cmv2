# Batch C Migration Overview

## Scope

Batch C covers the interaction modules:

1. actions
2. campaigns
3. sheets

Source documents analyzed:

1. ISSUES/architecture/04_module_specifications/01_actions.md
2. ISSUES/architecture/04_module_specifications/04_campaigns.md
3. ISSUES/architecture/04_module_specifications/05_sheets.md
4. ISSUES/architecture/04_module_specifications/features/01_actions_features.md
5. ISSUES/architecture/04_module_specifications/features/04_campaigns_features.md
6. ISSUES/architecture/04_module_specifications/features/05_sheets_features.md

Evidence sources used for state recommendations:

1. ISSUES/architecture/01_contracts/APPROVAL_LOG.md
2. ISSUES/architecture/01_contracts/FREEZE_GATE_STATUS.md
3. ISSUES/architecture/01_contracts/scorecards/01_actions_scorecard.md
4. ISSUES/architecture/01_contracts/scorecards/04_campaigns_scorecard.md
5. ISSUES/architecture/01_contracts/scorecards/05_sheets_scorecard.md

## Migration Rule

Keep architecture module files in place as canonical source docs.
Create or place executable FLOW tickets that reference those files.

## Batch C File-to-State Mapping

| Actual file                                                                    | Recommended FLOW state | Confidence | Why this state                                                                                                   |
| ------------------------------------------------------------------------------ | ---------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------- |
| ISSUES/architecture/04_module_specifications/01_actions.md                     | 02_READY               | High       | Frozen with strong implementation and test anchors for action validation, budget checks, and execution outcomes. |
| ISSUES/architecture/04_module_specifications/features/01_actions_features.md   | 02_READY               | High       | Feature outcomes are demonstrably covered by current resolver and execution tests.                               |
| ISSUES/architecture/04_module_specifications/04_campaigns.md                   | 01_PLANNING            | High       | Frozen contract exists, but service-level role and context enforcement requires additional completion.           |
| ISSUES/architecture/04_module_specifications/features/04_campaigns_features.md | 01_PLANNING            | High       | Campaign identity and context outcomes need stronger service and integration enforcement coverage.               |
| ISSUES/architecture/04_module_specifications/05_sheets.md                      | 00_BACKLOG             | High       | Core projection, hydration, and invalidation classes are not yet implemented in backend module namespace.        |
| ISSUES/architecture/04_module_specifications/features/05_sheets_features.md    | 00_BACKLOG             | High       | Deterministic sheet projection outcomes depend on missing sheets infrastructure.                                 |

## Overlapping Existing FLOW Ticket

Direct overlap and dependency:

1. ISSUES/FLOW/03_IN_PROGRESS/FEATURE_frontend_compendium_ui_master_blueprint.md

Practical impact:

1. Actions readiness supports advanced action editing UX.
2. Sheets backlog status is a known backend dependency for deeper character projection features.

## Practical Next Placement Actions

1. Keep actions module artifacts mapped to 02_READY through linked execution tickets.
2. Keep campaigns module artifacts mapped to 01_PLANNING until role/context service checks are fully scoped.
3. Keep sheets module artifacts in 00_BACKLOG and create a foundational implementation parent ticket before promotion.

## Blocking Notes

campaigns blockers before promotion to 02_READY:

1. Service-level DM and role-gated context selection enforcement.
2. Idempotent membership join and revoke behavior with integration coverage.
3. Cross-campaign denial semantics validated in tests.

sheets blockers before promotion to 01_PLANNING or 02_READY:

1. Implement sheet projector, hydrator, and invalidation manager primitives.
2. Establish dependency resolution flow for referenced compendium entities.
3. Add deterministic projection and recovery-oriented test coverage.
