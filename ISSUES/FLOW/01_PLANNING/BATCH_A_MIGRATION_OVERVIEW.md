# Batch A Migration Overview

## Scope

Batch A covers the foundation modules:

1. runtime
2. identity
3. transport

Source documents analyzed:

1. ISSUES/architecture/04_module_specifications/00_runtime.md
2. ISSUES/architecture/04_module_specifications/06_identity.md
3. ISSUES/architecture/04_module_specifications/11_transport.md
4. ISSUES/architecture/04_module_specifications/features/00_runtime_features.md
5. ISSUES/architecture/04_module_specifications/features/06_identity_features.md
6. ISSUES/architecture/04_module_specifications/features/11_transport_features.md

Evidence sources used for state recommendations:

1. ISSUES/architecture/01_contracts/APPROVAL_LOG.md
2. ISSUES/architecture/01_contracts/FREEZE_GATE_STATUS.md
3. ISSUES/architecture/01_contracts/scorecards/00_runtime_scorecard.md
4. ISSUES/architecture/01_contracts/scorecards/06_identity_scorecard.md
5. ISSUES/architecture/01_contracts/scorecards/11_transport_scorecard.md

## Migration Rule

Keep architecture module files in place as canonical source docs.
Create or place executable FLOW tickets that reference those files.

## Batch A File-to-State Mapping

| Actual file                                                                    | Recommended FLOW state | Confidence | Why this state                                                                          |
| ------------------------------------------------------------------------------ | ---------------------- | ---------- | --------------------------------------------------------------------------------------- |
| ISSUES/architecture/04_module_specifications/00_runtime.md                     | 02_READY               | High       | Frozen with strong score and existing runtime implementation anchors.                   |
| ISSUES/architecture/04_module_specifications/features/00_runtime_features.md   | 02_READY               | High       | Feature outcomes match existing session lifecycle and sync behavior.                    |
| ISSUES/architecture/04_module_specifications/06_identity.md                    | 01_PLANNING            | High       | Frozen contract exists, but membership and delegation implementation gaps remain.       |
| ISSUES/architecture/04_module_specifications/features/06_identity_features.md  | 01_PLANNING            | High       | Entitlement and effective identity behavior need additional backend completion work.    |
| ISSUES/architecture/04_module_specifications/11_transport.md                   | 02_READY               | High       | Envelope and correlation foundations are present; modular extraction work is ready.     |
| ISSUES/architecture/04_module_specifications/features/11_transport_features.md | 02_READY               | High       | Core transport outcomes are mostly present and can be finalized through modularization. |

## Overlapping Existing FLOW Ticket

Already present and aligned:

1. ISSUES/FLOW/02_READY/ISSUE_core_websocket_dispatcher_modularization.md

Recommended usage:

1. Treat this as the first executable transport and runtime-adjacent ticket in Batch A.

## Practical Next Placement Actions

1. Keep runtime and transport module artifacts mapped to 02_READY through linked execution tickets.
2. Keep identity module artifacts mapped to 01_PLANNING until missing schema and service contracts are scoped.
3. Do not move any Batch A item to 03_IN_PROGRESS while the current compendium task remains the active task pointer.

## Blocking Notes

Identity blockers before promotion to 02_READY:

1. Campaign membership model and persistence flow completion.
2. Delegation model and stop or revoke idempotency behavior.
3. Effective session context and permission snapshot service methods.

Transport hardening blockers before 04_REVIEW:

1. Extract envelope validation and error formatting to explicit transport components.
2. Isolate request correlation tracking behavior from broader session concerns.
3. Formalize visibility router behavior for role and ownership filtering.
