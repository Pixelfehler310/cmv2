# CMV2 Architecture: Archive Adaption Strategy

This strategy document defines how to harvest, extract, and adapt existing intelligence from the **Legacy Vertical Planning** (`ISSUES/archive/vertical_legacy/`) into the new **Contract-First** layered architecture.

> [!IMPORTANT]
> **Rule Alignment**: All harvesting activities are governed by the **[Horizontal Planning Rule](file:///c:/Users/simon/Documents/GitHub/cmv2/.agents/rules/horizontal-planning.md)**. The `legacy_harvest_specialist` AI skill is responsible for ensuring that extracted primitives are solidified horizontally before any implementation code is written.

## 1. Extraction Protocol

When moving content from the legacy vertical issues (V01-V05) to Layer 1 (Contracts), follow these steps:

### A. Identify Domain Primitives

- **Source**: `V05_business_and_content_entities_class_diagram.mmd` and `V05_business_and_content_entities_overview.md`.
- **Target**: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-02]_content_schema.md`.
- **Action**: Extract the core attributes. **Maintain the diagram in Mermaid**. If the legacy logic is complex, create a deep-dive explanation in `ISSUES/architecture/system_info/legacy/<domain>_legacy_explanation.md` BEFORE adapting.

### B. Extract Action Mechanics

- **Source**: `V2_action_mechanics_specification.md` and `ISSUE_[VERT]_V02_combat_actions_turn_economy_and_effects.md`.
- **Target**: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-03]_action_mechanics.md`.
- **Action**: Adapt the "Result Piping" and "Operation Payload" contracts. **Use Mermaid Sequence Diagrams** to document the execution order. Ensure they are platform-agnostic.

### C. Formalize Lifecycle State Machine

- **Source**: `ISSUE_[VERT]_V04_content_schema_and_pack_lifecycle.md`.
- **Target**: `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-01]_pack_lifecycle.md`.
- **Action**: Standardize the "Draft", "Published", "Superseded" states and the rules for transitioning between them.

### D. Split Vertical V05 into Modular Contracts

- **Source**: `V05_compendium_crud_and_definition_catalog_detailed_plan.mmd` and `V05_content_management_query_and_projection_detailed_plan.mmd`.
- **Target**:
  1.  `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-02]_referential_integrity.md`
  2.  `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-03]_query_projection_consistency.md`
  3.  `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`
  4.  `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-05]_layer_ownership.md`
  5.  `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-04]_content_query_projection.md`
- **Action**: Move cross-domain concerns into Core contracts and keep DND5E-specific rules in DND5E contracts.

---

## 2. Adaptation and Abstraction

### Key Abstraction Rule:

> **The Archive is "How I did it once". The New Contract is "The Rule for how it MUST be done always".**

| Feature    | Legacy Approach (V05)           | New Strategy (L1 Contract)                                      |
| :--------- | :------------------------------ | :-------------------------------------------------------------- |
| **Packs**  | Part of the Compendium Service. | Independent **Content Pack Protocol**.                          |
| **Links**  | Handled by SQL Foreign Keys.    | **Referential Integrity Contract** (agnostic of DB).            |
| **Search** | CQRS Projection in the Service. | **Searchable Interface Contract** defined in the entity itself. |

---

## 3. The "Completion Gate" for Adaptation

An archived module is considered "fully adapted" when:

1.  All core entity models have been moved to Layer 1.
2.  A **Mermaid diagram** (for entities and logic flow) exists in the new structure for each adapted feature.
3.  A `test_plan/` subfolder contains natural language tests based on the legacy implementation experience.
4.  The legacy file is tagged as `[ADAPTED]` in its header.

---

## 4. Active Contract Split (Now In Progress)

### A. Master Tracking Issue

- `ISSUES/architecture/01_contracts/ISSUE_[CONTRACT]_[MIG-01]_v05_horizontal_harvest.md`

### B. Core Contract Modules

1. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-01]_pack_lifecycle.md`
2. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-02]_referential_integrity.md`
3. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-03]_query_projection_consistency.md`
4. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`
5. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-05]_layer_ownership.md`

### C. DND5E Contract Modules

1. `ISSUES/architecture/01_contracts/ISSUE_[CONTRACT]_[DND5E-01]_base_rule_schema.md` (index)
2. `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-02]_content_schema.md`
3. `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-03]_action_mechanics.md`
4. `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-04]_content_query_projection.md`

### D. Gold Baseline Anchor

When source conflicts exist between archive and legacy docs, baseline symbols from:

1. `backend/src/systems/dnd5e/content/domain/primitives.py`
2. `backend/src/systems/dnd5e/content/domain/definition_models.py`
3. `backend/src/systems/dnd5e/content/domain/link_models.py`
4. `backend/src/systems/dnd5e/content/domain/invariants.py`
