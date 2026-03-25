# Vertical Module Execution Plan

Status: Active Planning Document
Owner: Architecture + Engineering

## Purpose

This playbook defines how each vertical architecture module is executed from discovery to closure.
The goal is to complete one module end-to-end with strong tests before deepening the next module.

## Program Mode

1. Keep exactly one active module.
2. Allow one optional prep module for analysis only.
3. Create deep child issues only for the active module.
4. Require each PR to map to one primary module issue.

## Standard Module Phases

### Phase P0: Alignment and Baseline

Objectives:

1. Confirm module scope against D2.9 target architecture.
2. Confirm current behavior and known drift.
3. Define initial risk list and rollback notes.

Outputs:

1. Module brief with boundaries and dependencies.
2. Baseline verification command set.

Exit gate:

1. Scope and dependency map approved.

### Phase P1: Contract and Invariant Freeze

Objectives:

1. Define authoritative runtime/persistence contracts for the module.
2. Define domain invariants and denial semantics.
3. Mark compatibility policy for breaking changes.

Outputs:

1. Contract specification delta for the module.
2. Invariant checklist.

Exit gate:

1. Contract and invariant set is stable enough to implement.

### Phase P2: Persistence and Ownership Boundaries

Objectives:

1. Assign one write authority per mutable aggregate.
2. Lock repository boundaries and persistence mapping.
3. Remove ambiguous write paths.

Outputs:

1. Ownership matrix for module aggregates.
2. Repository boundary notes.

Exit gate:

1. No unresolved multi-writer ambiguity.

### Phase P3: Application and Domain Implementation

Objectives:

1. Implement application services and policy behavior for module scope.
2. Enforce deny and error semantics in-domain.
3. Keep transport thin and non-authoritative.

Outputs:

1. Module service behavior aligned to contracts.
2. Domain-policy conformance notes.

Exit gate:

1. Service behavior matches frozen contracts.

### Phase P4: Transport and External Interfaces

Objectives:

1. Align REST/WS payload and event surfaces with module contracts.
2. Ensure request correlation and event ordering requirements.
3. Document outbound interface behavior.

Outputs:

1. Interface mapping for API and WS paths.
2. Event ordering and visibility notes.

Exit gate:

1. Interface behavior is deterministic and documented.

### Phase P5: Frontend Projection and Type Sync

Objectives:

1. Verify frontend projection consumes backend truth without rule logic leakage.
2. Regenerate and verify shared contract artifacts.
3. Confirm adapter/store compatibility.

Outputs:

1. Projection compatibility checklist.
2. Artifact drift verification result.

Exit gate:

1. Frontend projection remains contract-stable.

### Phase P6: Test Matrix and Observability Hardening

Objectives:

1. Add deterministic tests for critical module flows.
2. Ensure log signals support rapid triage.
3. Confirm CI checks for drift and regressions.

Outputs:

1. Module test matrix with minimum required suites.
2. Observability checklist.

Exit gate:

1. All required tests and checks pass.

### Phase P7: Closure and Next-Module Handoff

Objectives:

1. Close remaining known gaps or log explicit follow-up issues.
2. Record module completion status and residual risks.
3. Hand off learned constraints to next module.

Outputs:

1. Module completion note.
2. Follow-up issue list with rationale.

Exit gate:

1. Module marked complete with verified gates.

## Per-Module Phase Emphasis

### V01 Runtime Hierarchy and Encounter Lifecycle

Priority phases: P1, P2, P3, P6

Key focus:

1. Campaign -> Scene -> Encounter ownership and transitions.
2. Encounter activation and scene linkage correctness.

### V02 Combat Actions, Turn Economy, and Effects

Priority phases: P1, P3, P4, P6

Key focus:

1. Action execution determinism and deny reason stability.
2. Effect lifecycle and turn budget policy correctness.

### V03 World Context Runtime

Priority phases: P1, P2, P3, P6

Key focus:

1. Region/place/faction/npc relationship invariants.
2. Persistence and application consistency for context entities.

### V04 Content Schema and Pack Lifecycle

Priority phases: P1, P2, P5, P6

Key focus:

1. Lifecycle states, provenance, versioning, replacement links.
2. Contract artifacts and migration notes consistency.

### V05 Compendium CRUD and Definition Catalog

Priority phases: P2, P3, P4, P6

Key focus:

1. CRUD consistency across all definition families.
2. Endpoint/repository alignment and validation behavior.

### V06 Event Contracts and Frontend Projection

Priority phases: P1, P4, P5, P6

Key focus:

1. Event payload shape, ordering, and correlation.
2. Frontend projection stability with generated types.

## Global Exit Criteria (Program)

1. Every module has passed P0 through P7 gates.
2. No unresolved critical ownership ambiguity remains.
3. Contract drift checks are green across touched artifacts.
4. Residual risks are tracked as explicit follow-up issues.
