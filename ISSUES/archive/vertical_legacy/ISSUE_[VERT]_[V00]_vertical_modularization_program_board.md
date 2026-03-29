# ISSUE [VERT][V00]: Vertical Modularization Program Board

Status: Active Planning
Owner: Architecture

## Why This Exists

This issue is the single control board for the vertical refactor program.
It keeps sequencing, dependencies, risk, and completion criteria coherent while only one module is deepened at a time.

Reference playbook:

- docs/architecture/shared/05_vertical_module_execution_plan.md

## Scope

In scope:

- Define module order and dependency policy.
- Define module Definition of Done gates.
- Define planning rule: only active module receives child issues.

Out of scope:

- Detailed implementation tasks for all modules upfront.

## Module Order (Initial)

1. V01 Runtime Hierarchy and Scene Combat Lifecycle.
2. V02 Combat Actions, Turn Economy, and Effects.
3. V03 World Context Runtime.
4. V04 Content Schema and Pack Lifecycle.
5. V05 Compendium CRUD and Definition Catalog.
6. V06 Event Contracts and Frontend Projection.

## Active Module Window

Primary active module:

- V05 Compendium CRUD and Definition Catalog

Optional prep module:

- V06 Event Contracts and Frontend Projection

Active child issue set:

1. V05-01 Baseline and Drift Audit.
2. V05-02 Definition Contract and Validation Freeze.
3. V05-03 Ownership and Repository Boundary Lock.
4. V05-04 CRUD Application Orchestration.
5. V05-05 REST/WS Contract Convergence for Content Streams.
6. V05-06 Indexing, Search, and Linked-Entry Resolution Policy.
7. V05-07 Test Matrix and Completion Gate.

Activation rationale:

1. Temporary production goal prioritizes content lookup and character-sheet support over map/combat automation.
2. V05 creates the highest near-term utility for hybrid tabletop sessions.
3. V06 prep is enabled to avoid projection drift while V05 contracts are frozen.

## Program Rules

1. Keep one primary active module and one optional prep module.
2. Create deep child issues only for the active module.
3. Every PR must map to one primary module issue.
4. Child issues for inactive modules are not created until activation is explicit in this board.

## Definition of Done Gate (Per Module)

1. Ownership boundaries are explicit and testable.
2. Contracts are documented and deterministic.
3. Persistence path is clear and bounded.
4. Integration tests and drift checks pass.
