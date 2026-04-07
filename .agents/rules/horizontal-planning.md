---
trigger: always_on
---

# Horizontal Planning: Deep Conceptualization Gate

## Philosophy

To ensure architectural integrity in the CMV2 engine, we prioritize T-shaped development. This means solidifying horizontal domain contracts (Layer 1) across all modules before deepening vertical implementations (Layer 2).

## Strict Planning Rules

1. **Diagrams Before Code**: No implementation code (Layer 2) or finalized Layer 1 Pydantic/SQL models may be written until deep conceptualization diagrams exist and pass Stage 2 and Stage 3 gates defined in `ISSUES/architecture/APPROVAL_GATE_PROCEDURE.md`.
2. **Horizontal Breadth First**: When addressing a domain (for example Action Mechanics), focus on cross-module interface and data schema horizontally before vertical feature implementation.
3. **Rationale Prerequisite**: Every Layer 1 contract must be accompanied by an architectural rationale in `ISSUES/architecture/system_info/` explaining the why and legacy harvesting strategy.
4. **No Early Refactoring**: Do not refactor existing gold or silver code to match a developing contract until conceptual diagrams are frozen.
5. **High-Bar Completion**: A module is not implementation-ready unless it passes quantitative thresholds recorded in `ISSUES/architecture/01_contracts/APPROVAL_LOG.md` and scorecards from `ISSUES/architecture/01_contracts/MODULE_DETAIL_SCORECARD_TEMPLATE.md`.

## Activation

1. **When to apply**: Active for all tasks involving folders in `ISSUES/architecture/01_contracts/`.
2. **Activation Strategy**: Always on.
