# Current Task Context: Documentation Infrastructure & Architectural Clarity

This document provides a focal point for the current session's objectives and the immediate history of the task.

## **Task**: Start Horizontal Contract Harvest Implementation

### **Why we are doing this?**

To provide instant clear context for both human developers and AI agents during the transition from Vertical Legacy thinking to Horizontal-First architecture.

### **Directly Beforehand**:

1.  Defined the "Horizontal-First" strategy in `HOW_TO_PLAN.md`.
2.  Audited the **V05 Compendium** implementation for architectural drift.
3.  Identified the need for "Living" documents that simplify the developer's first contact with the architecture.

### **Current Objective**:

- [x] Create `WHAT_WE_ARE_DOING.md` for high-level strategy.
- [x] Establish **Archiving Policy** in `HOW_TO_PLAN.md` and archive the `00_quality` tickets.
- [x] Implement `system_info/` directory for technical deep-dives.
- [x] Adapt `PLANNING_OVERVIEW.md` and `HOW_TO_PLAN.md` to this new documentation pattern.
- [x] Adapt and archive `ARCHIVE_ADAPTION_STRATEGY.md` into the MIG-01 master strategy.
- [x] Create a master migration issue for V05 -> Horizontal split.
- [x] Split Layer 1 contracts into Core and DND5E modules with Mermaid diagrams.
- [x] Add `test_plan/` artifacts for new contract modules.

### **Next Steps**:

1. Complete freeze-gate review across CORE-01..CORE-05 and DND5E-02..DND5E-04.
2. Run Mermaid render pass and fix any syntax drift.
3. Add `[ADAPTED]` headers to legacy V05 source docs once traceability review passes.
4. Start Layer 2 implementation issues only after contract freeze sign-off.

---

> [!IMPORTANT]
> **Active Governance**: All tasks are subject to the **[Horizontal Planning: Deep Conceptualization Gate](../../.agents/rules/horizontal-planning.md)** rule.
> AI agents must verify that Layer 1 Contracts are documented with diagrams before proposing Layer 2 implementations.

> [!TIP]
> **Check the [WHAT_WE_ARE_DOING](WHAT_WE_ARE_DOING.md)** for a broad perspective on the current phase.
