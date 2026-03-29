# CMV2 Planning Guide: Contract-First Layered Modularization

This document defines the authoritative methodology for planning and evolving the CMV2 engine. All AI agents and human contributors MUST follow these protocols to ensure architectural integrity.

## 1. Core Philosophy: The "T-Shaped" Roadmap
We separate **Domain Contracts** (What it is) from **Implementations** (How it works).
- **Layer 1 (Contracts)**: Must be solidified horizontally across all related modules before deepening implementation.
- **Layer 2 (Implementations)**: Developed in vertical sprints once contracts are frozen.

---

## 2. Module Blueprinting Requirements (Per Module)

Every important module (e.g., Compendium, Combat, Campaign) MUST include the following documentation artifacts:

### A. Mermaid Class Diagrams
- **Path**: `ISSUES/architecture/01_contracts/<module>/<module>_entities.mmd`
- **Goal**: Visual representation of entity relationships, attributes, and inheritance.
- **Requirement**: Use valid Mermaid syntax. Avoid HTML tags in labels. Use quotes for special characters.

### B. Describing Explanation Markdown
- **Path**: `ISSUES/architecture/01_contracts/<module>/<module>_entities_explanation.md`
- **Goal**: Human and AI-readable rationale for the diagram. Explain "Why" before "What".

### C. Complexity Diagrams (Activity/Sequence)
- **Requirement**: For complex logic like "Action Execution" or "Linked Entry Resolution", provide a Sequence Diagram (`.mmd`) and an Explanation file.

### D. Cross-Module Overviews
- **Goal**: High-level understanding of how modules (e.g., Combat -> Compendium) interact.
- **Path**: `ISSUES/architecture/PLANNING_OVERVIEW.md` (Maintained as the source of truth).

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
2.  **Validate against Invariants**: Ensure your implementation strictly adheres to the test plan described in the contract.
3.  **Update the Map**: If your implementation requires a change to the contract, you MUST update the Mermaid diagrams and explanation files before proceeding.
