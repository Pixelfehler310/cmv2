# ISSUE [VERT][V00]: Vertical Modularization Program Board

Status: Planned
Owner: Architecture

## Why This Exists

This issue is the single control board for the vertical refactor program.
It keeps sequencing, dependencies, risk, and completion criteria coherent while only one module is deepened at a time.

## Scope

In scope:

- Define module order and dependency policy.
- Define module Definition of Done gates.
- Define planning rule: only active module receives child issues.

Out of scope:

- Detailed implementation tasks for all modules upfront.

## Module Order (Initial)

1. V01 Runtime Hierarchy and Encounter Lifecycle.
2. V02 Combat Actions, Turn Economy, and Effects.
3. V03 World Context Runtime.
4. V04 Content Schema and Pack Lifecycle.
5. V05 Compendium CRUD and Definition Catalog.
6. V06 Event Contracts and Frontend Projection.

## Program Rules

1. Keep one primary active module and one optional prep module.
2. Create deep child issues only for the active module.
3. Every PR must map to one primary module issue.

## Definition of Done Gate (Per Module)

1. Ownership boundaries are explicit and testable.
2. Contracts are documented and deterministic.
3. Persistence path is clear and bounded.
4. Integration tests and drift checks pass.
