# ISSUE [ARCH][M00]: Target Architecture Recursive Module Map

Status: Planned
Owner: Architecture

## Why This Exists

Current work is feature-driven and improving, but structural changes need a stable decomposition strategy.
This issue defines the top-level modules and the recursion rule so every future feature/restructure can be tracked as a child issue.

## Scope

In scope:

- Define high-level modules for backend, transport, persistence, frontend projection, and quality gates.
- Define DnD business-domain streams based on the target architecture diagram.
- Define interface-first workflow between modules.
- Define recursion policy: split each module into smaller submodules only when that module becomes active.

Out of scope:

- Deep implementation details of each module.
- Immediate code migration.

## Proposed Top-Level Modules

1. M01 Backend Truth and Domain Contracts.
2. M02 Transport and Session Orchestration.
3. M03 Action Execution and Rules Engine.
4. M04 Persistence Boundaries and Repository Contracts.
5. M05 Frontend Read Models and Projection Boundaries.
6. M06 Contract Artifacts and Drift Gates.
7. M07 Observability, Test Harness, and Guardrails.

## Domain Streams (D2.9 aligned)

Source:

- docs/diagrams/mmd/D2.9_target_corrected_architecture.mmd

Streams:

1. D01 Runtime Hierarchy and Encounter Lifecycle.
2. D02 Combat Actions, Turn Economy, and Effects.
3. D03 World Context Runtime.
4. D04 Content Schema and Content Pack Lifecycle.
5. D05 Compendium CRUD and Definition Catalog.
6. D06 Event Contracts and Frontend Projection Feed.

## Planning Rule (Two-Dimensional)

1. Pick one primary Dxx stream for business scope.
2. Pick one primary Mxx module for technical boundary hardening.
3. Optional secondary tags allowed, but one Dxx + one Mxx must stay primary.

## Interface-First Rule

1. Define contract before implementation changes.
2. Contracts are explicit payload/schema interfaces and ownership boundaries.
3. No module may directly reach into another module internal persistence details.

## Acceptance Criteria

1. All top-level module issues exist and are linked from this issue.
2. Every new architecture task is tagged to one top-level module.
3. Every new architecture task is tagged to one primary Dxx stream.
4. Child issues are created only when parent module becomes in-progress.
