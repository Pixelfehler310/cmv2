# CMV2 Architecture: Archive Adaption Strategy

This strategy document defines how to harvest, extract, and adapt existing intelligence from the **Legacy Vertical Planning** (`ISSUES/archive/vertical_legacy/`) into the new **Contract-First** layered architecture.

## 1. Extraction Protocol

When moving content from the legacy vertical issues (V01-V05) to Layer 1 (Contracts), follow these steps:

### A. Identify Domain Primitives
- **Source**: `V05_business_and_content_entities_class_diagram.mmd` and `V05_business_and_content_entities_overview.md`.
- **Target**: `ISSUES/architecture/01_contracts/dnd5e/01_content_schema.md`.
- **Action**: Extract the core attributes. **Maintain the diagram in Mermaid**. If the legacy logic is complex, create a deep-dive explanation in `ISSUES/architecture/system_info/legacy/<domain>_legacy_explanation.md` BEFORE adapting.

### B. Extract Action Mechanics
- **Source**: `V2_action_mechanics_specification.md` and `ISSUE_[VERT]_V02_combat_actions_turn_economy_and_effects.md`.
- **Target**: `ISSUES/architecture/01_contracts/dnd5e/02_action_mechanics.md`.
- **Action**: Adapt the "Result Piping" and "Operation Payload" contracts. **Use Mermaid Sequence Diagrams** to document the execution order. Ensure they are platform-agnostic.

### C. Formalize Lifecycle State Machine
- **Source**: `ISSUE_[VERT]_V04_content_schema_and_pack_lifecycle.md`.
- **Target**: `ISSUES/architecture/01_contracts/core/01_pack_lifecycle.md`.
- **Action**: Standardize the "Draft", "Published", "Superseded" states and the rules for transitioning between them.

---

## 2. Adaptation and Abstraction

### Key Abstraction Rule:
> **The Archive is "How I did it once". The New Contract is "The Rule for how it MUST be done always".**

| Feature | Legacy Approach (V05) | New Strategy (L1 Contract) |
| :--- | :--- | :--- |
| **Packs** | Part of the Compendium Service. | Independent **Content Pack Protocol**. |
| **Links** | Handled by SQL Foreign Keys. | **Referential Integrity Contract** (agnostic of DB). |
| **Search** | CQRS Projection in the Service. | **Searchable Interface Contract** defined in the entity itself. |

---

## 3. The "Completion Gate" for Adaptation
An archived module is considered "fully adapted" when:
1.  All core entity models have been moved to Layer 1.
2.  A **D2 diagram** (for entities) and/or a **Mermaid diagram** (for logic flow) exists in the new structure for each adapted feature.
3.  A `test_plan/` subfolder contains natural language tests based on the legacy implementation experience.
4.  The legacy file is tagged as `[ADAPTED]` in its header.
