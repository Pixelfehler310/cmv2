# CMV2 Planning Guide: Contract-First Layered Modularization

This document defines the authoritative methodology for planning and evolving the CMV2 engine. All AI agents and human contributors MUST follow these protocols to ensure architectural integrity.

## 1. Core Philosophy: The "T-Shaped" Roadmap
We separate **Domain Contracts** (What it is) from **Implementations** (How it works).
- **Layer 1 (Contracts)**: Must be solidified horizontally across all related modules before deepening implementation.
- **Layer 2 (Implementations)**: Developed in vertical sprints once contracts are frozen.

> [!IMPORTANT]
> **The Horizontal Planning Rule: Deep Conceptualization Gate**
> No implementation code (Layer 2) or finalized Layer 1 Pydantic/SQL models may be written until a **DEEP conceptualization using diagrams** (Mermaid or D2) has been created and approved.
> Reference: [Horizontal Planning Rule](file:///c:/Users/simon/Documents/GitHub/cmv2/.agents/rules/horizontal-planning.md)

---

## 2. Agent Skills & Governance

To enforce this architecture, the CMV2 engine leverages specialized AI skills:

| Skill | Responsibility in Horizontal Planning |
| :--- | :--- |
| **documentation_architect** | Establishes strict standards for Horizontal-First plans and Hybrid Diagrams. |
| **legacy_harvest_specialist** | Dedicated to extracting domain primitives from the Legacy Archive for L1 contracts. |
| **backend_architect** | Focuses on TDD for complex game mechanics and PSQ Purity Guardrails. |
| **campaign_world_lore_master** | Ensures technical structures support the creative nuances of the campaign world. |

---

## 2. Module Blueprinting & Diagramming Requirements

Every important module MUST include the following documentation artifacts, using the **Hybrid Diagramming Strategy**:

### A. Markdown-Embedded Diagrams (Layer 1 & 2)
- **Path**: Embedded directly in `.md` files (Contracts or Implementations).
- **Tool**: **Mermaid**.
- **Requirement**: Use Mermaid for all diagrams intended for web/GitHub viewing. This includes Entity Class Diagrams, Logic Flows, and Sequence Diagrams.

### B. Standalone Architectural Maps (Cross-Module)
- **Path**: `ISSUES/architecture/*.d2`
- **Tool**: **D2**.
- **Requirement**: Use D2 for permanent, high-fidelity system maps where layout precision is critical. These act as the "Master Layouts" for the system.

### C. Describing Explanation Markdown
- **Path**: `ISSUES/architecture/01_contracts/<module>/<module>_entities_explanation.md`
- **Goal**: Human and AI-readable rationale for the architecture. Explain "Why" before "What".

### D. Cross-Module Overviews
- **Goal**: High-level understanding of how modules (e.g., Combat -> Compendium) interact.
- **Path**: `ISSUES/architecture/PLANNING_OVERVIEW.md` (Source of truth maintained in D2).

### E. Managed Context Documents
- **Goal**: Provide instant context for current work.
- **Paths**:
    - `ISSUES/architecture/WHAT_WE_ARE_DOING.md`: High-level strategic roadmap for the current phase.
    - `ISSUES/architecture/CURRENT_TASK.md`: Why the current task is happening, what happened before, and what comes next.

### F. System Information Repository
- **Goal**: Centralized storage for deep technical explanations.
- **Path**: `ISSUES/architecture/system_info/`
    - `legacy/`: Descriptions of legacy systems being adapted.
    - `architecture/`: Explanations of new architecture designs (e.g., Result Piping).

---

## 3. Test-Plan Protocol (The "Shift-Left" Strategy)

When scoping a **Contract**, you MUST define the testing interface upfront.

### Subfolder: `test_plan/`
- Every contract issue should have a corresponding `test_plan/` subfolder.
- **Format**: `.md` file in plain natural language.
- **Content**:
    - **Unit Targets**: What functions/methods are being tested.
    - **Invariants**: What rules must *always* be true (e.g., "A Spell must have a level >= 0").
    - **Edge Cases**: List problematic inputs (e.g., "Infinite loops in recursive links").
    - **Expected Results**: Clearly state the success/failure conditions.

---

## 4. Issue Naming and Structure
- **Contracts**: `ISSUES/architecture/01_contracts/ISSUE_[CONTRACT]_[DOMAIN-ID]_title.md`
- **Implementations**: `ISSUES/architecture/02_implementations/ISSUE_[IMPLEMENT]_[MODULE-ID]_title.md`

## 5. Agent Instructions
1.  **Read the Contracts First**: Before implementing any feature, read the relevant files in `01_contracts`.
2.  **Check for Instant Context**: Always read `WHAT_WE_ARE_DOING.md` and `CURRENT_TASK.md` at the start of a session.
3.  **Update the Context**: When completing a task or starting a new one, you MUST update `CURRENT_TASK.md` to reflect the change.
4.  **Document Deep Context**: If you encounter or design a complex system, create or update a file in `system_info/`.
5.  **Validate against Invariants**: Ensure your implementation strictly adheres to the test plan described in the contract.
6.  **Update the Map**: If your implementation requires a change to the contract, you MUST update the D2/Mermaid diagrams and explanation files before proceeding.

---

## 6. Production Status & Quality Tiers (PSQ)

To manage technical debt during re-engineering, every Python module MUST declare its maturity tier via the `__production_status__` metadata at the top of the file.

### Tier Definitions

| Tier | Status | Requirements |
| :--- | :--- | :--- |
| **Gold** | `"gold"` | 90%+ Test coverage, Pydantic validation, full documentation, performance optimized. |
| **Silver** | `"silver"` | Stable logic, full Type-Hints, passes all core invariants. Clean Code standard. |
| **Bronze** | `"bronze"` | MVP/Prototype code. Functional but "unclean", undocumented, or lacking tests. |
| **Broken** | `"broken"` | Unusable code. Architecturally or logically false, unused, or fundamentally flawed. |
| **Unchecked** | `Default` | Legacy code not yet audited. Treated as **Bronze** by guardrails. |

### The "Purity Guardrail"
- Modules in **Production Scopes** (e.g., `src/systems/dnd5e/`, `src/core/`) are strictly forbidden from importing **Bronze** or **Unchecked** modules.
- Violations will trigger a `QualityViolation` failure in the CI/CD pipeline.
- **Reference**: `ISSUES/archive/quality/ISSUE_[QUALITY]_[SYS-01]_production_status_quarantine.md`

---

## 7. Archiving Policy: Preserving the "Brain"

Finished issues and superseded documentation MUST NOT be deleted. Instead, they are moved to the `ISSUES/archive/` directory to preserve the historical rationale for both human developers and AI agents.

### Archiving Rules
1.  **Maintain Path Context**: Move items from `ISSUES/architecture/<folder>/` to `ISSUES/archive/<folder>/`.
2.  **No Deletions**: Historical context is essential for AI agents to understand why decisions were made.
3.  **Cross-References**: When archiving a foundational issue, update any "Live" documents (like this one) to point to the new location in the archive.
