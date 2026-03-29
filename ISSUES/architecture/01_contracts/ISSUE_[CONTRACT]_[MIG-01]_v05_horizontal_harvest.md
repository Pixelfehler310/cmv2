# ISSUE [CONTRACT] [MIG-01]: V05 to Horizontal Contract Harvest

## Goal
Create a modular Layer 1 contract set from legacy V05 architecture, while using the implemented gold content system as the canonical naming and behavior baseline.

## Fixed Decisions
1. Scope: Build Core and DND5E contracts in parallel.
2. Conflict policy: Gold implementation is source of truth when legacy and archive docs differ.
3. Deliverable pattern: One master migration issue plus per-module contract files.

## Contract Module Map

| Module ID | Target File | Purpose | Status |
| :--- | :--- | :--- | :--- |
| CORE-01 | `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-01]_pack_lifecycle.md` | Lifecycle state machine and legal transitions | Planned |
| CORE-02 | `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-02]_referential_integrity.md` | Linked graph contracts and cycle denial | Planned |
| CORE-03 | `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-03]_query_projection_consistency.md` | Revision, projection, and invalidation consistency | Planned |
| CORE-04 | `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md` | Request and event envelope contracts | Planned |
| CORE-05 | `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-05]_layer_ownership.md` | Allowed dependency directions across layers | Planned |
| DND5E-02 | `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-02]_content_schema.md` | Canonical DND5E definition schemas | Planned |
| DND5E-03 | `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-03]_action_mechanics.md` | ActionOperationSpec and ModifierSpec contracts | Planned |
| DND5E-04 | `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-04]_content_query_projection.md` | DND5E query/read-model contracts | Planned |

## Legacy to Contract Traceability

| Legacy Source | Contract Target | Extract Rule |
| :--- | :--- | :--- |
| `ISSUES/archive/vertical_legacy/v05/V05_macro_architecture_overview.mmd` | CORE-05 | Layer boundaries and call direction |
| `ISSUES/archive/vertical_legacy/v05/V05_business_and_content_entities_class_diagram.mmd` | DND5E-02 | Entity and relationship shape |
| `ISSUES/archive/vertical_legacy/v05/V05_compendium_crud_and_definition_catalog_detailed_plan.mmd` | CORE-01, CORE-05 | Lifecycle and ownership orchestration |
| `ISSUES/archive/vertical_legacy/v05/V05_content_management_query_and_projection_detailed_plan.mmd` | CORE-03, CORE-04, DND5E-04 | Query pipeline and projection semantics |
| `ISSUES/archive/vertical_legacy/v05/V2_action_mechanics_specification.md` | DND5E-03 | Polymorphic operation payload rules |
| `ISSUES/archive/vertical_legacy/v05/v05_migration_notes.md` | CORE-02, DND5E-02 | Link graph and schema drift constraints |

## Gold Baseline Symbols
Use the following symbols and enum values as canonical unless an explicit contract override is approved:
1. `DefinitionFamily`, `LifecycleState`, `OperationType`, `ActionOperationSpec` in `backend/src/systems/dnd5e/content/domain/primitives.py`
2. `DefinitionRecord` and family-specific definitions in `backend/src/systems/dnd5e/content/domain/definition_models.py`
3. `LinkedEntryReference`, `RelationKind`, `ResolveMode`, `ReplacementChain` in `backend/src/systems/dnd5e/content/domain/link_models.py`
4. `CompendiumErrorCode` in `backend/src/systems/dnd5e/content/domain/invariants.py`

## Diagram Backlog

| Module | Required Primary Diagram |
| :--- | :--- |
| CORE-01 | Mermaid `stateDiagram-v2` for transition legality |
| CORE-02 | Mermaid `classDiagram` for link graph contracts |
| CORE-03 | Mermaid `sequenceDiagram` for revision and projection flow |
| CORE-04 | Mermaid `sequenceDiagram` for envelope lifecycle |
| CORE-05 | Mermaid `flowchart` for dependency direction |
| DND5E-02 | Mermaid `classDiagram` for schema inheritance |
| DND5E-03 | Mermaid `sequenceDiagram` for operation execution and result piping |
| DND5E-04 | Mermaid `flowchart` for query and read-model handoff |

## Execution Order
1. Lock Core contracts CORE-01 to CORE-05.
2. Lock DND5E contracts DND5E-02 to DND5E-04.
3. Convert DND5E-01 to umbrella index and link to split modules.
4. Pass contract freeze gate before any new Layer 2 implementation issue.

## Contract Freeze Gate
- [ ] Each module has one explanation markdown.
- [ ] Each module contains at least one Mermaid diagram.
- [ ] Each module has a corresponding `test_plan` markdown.
- [ ] Each module lists extracted legacy sources.
- [ ] Each module lists canonical gold symbols it depends on.
- [ ] Module boundaries are non-overlapping.
