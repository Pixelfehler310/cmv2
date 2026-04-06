# Layer 1 Contract Freeze Gate Status

This file is the detailed freeze-gate source of truth for Sprint 1 contract hardening.

## Gate Criteria

1. Contract has exhaustive `Contract Invariants` section.
2. Contract has explicit `Validation Directives` section.
3. Contract has at least one Mermaid diagram.
4. Contract has a corresponding `test_plan` markdown.
5. Contract lists extracted legacy sources.
6. Contract lists canonical gold symbols.
7. Contract boundary does not overlap responsibilities with sibling contracts.
8. Contract-specific known gaps are closed for freeze readiness.

## CORE Contracts

### CORE-01: Pack Lifecycle

- [x] Invariants exhaustive
- [x] Validation directives explicit
- [x] Mermaid present
- [x] Test plan present (`core/test_plan/pack_lifecycle.md`)
- [x] Legacy sources listed
- [x] Canonical symbols listed
- [x] Boundary non-overlap confirmed
- [x] Known gaps closed

### CORE-02: Referential Integrity

- [x] Invariants exhaustive
- [x] Validation directives explicit
- [x] Mermaid present
- [x] Test plan present (`core/test_plan/referential_integrity.md`)
- [x] Legacy sources listed
- [x] Canonical symbols listed
- [x] Boundary non-overlap confirmed
- [x] Known gaps closed

### CORE-03: Query and Projection Consistency

- [x] Invariants exhaustive
- [x] Validation directives explicit
- [x] Mermaid present
- [x] Test plan present (`core/test_plan/query_projection_consistency.md`)
- [x] Legacy sources listed
- [x] Canonical symbols listed
- [x] Boundary non-overlap confirmed
- [x] Known gaps closed

### CORE-04: Session and Event Envelopes

- [x] Invariants exhaustive
- [x] Validation directives explicit
- [x] Mermaid present
- [x] Test plan present (`core/test_plan/session_event_envelopes.md`)
- [x] Legacy sources listed
- [x] Canonical symbols listed
- [x] Boundary non-overlap confirmed
- [x] Known gaps closed

### CORE-05: Layer Ownership

- [x] Invariants exhaustive
- [x] Validation directives explicit
- [x] Mermaid present
- [x] Test plan present (`core/test_plan/layer_ownership.md`)
- [x] Legacy sources listed
- [x] Canonical symbols listed
- [x] Boundary non-overlap confirmed
- [x] Known gaps closed

## DND5E Contracts

### DND5E-02: Content Schema

- [x] Invariants exhaustive
- [x] Validation directives explicit
- [x] Mermaid present
- [x] Test plan present (`dnd5e/test_plan/content_schema.md`)
- [x] Legacy sources listed
- [x] Canonical symbols listed
- [x] Boundary non-overlap confirmed
- [x] Known gaps closed

### DND5E-03: Action Mechanics

- [x] Invariants exhaustive
- [x] Validation directives explicit
- [x] Mermaid present
- [x] Test plan present (`dnd5e/test_plan/action_mechanics.md`)
- [x] Legacy sources listed
- [x] Canonical symbols listed
- [x] Boundary non-overlap confirmed
- [x] Known gaps closed

### DND5E-04: Content Query Projection

- [x] Invariants exhaustive
- [x] Validation directives explicit
- [x] Mermaid present
- [x] Test plan present (`dnd5e/test_plan/content_query_projection.md`)
- [x] Legacy sources listed
- [x] Canonical symbols listed
- [x] Boundary non-overlap confirmed
- [x] Known gaps closed

## Sprint 1 Notes

1. DND5E-01 remains an umbrella/index and is out of freeze-ready scope for this sprint.
2. Freeze readiness is granted per contract only when all eight criteria are checked.
3. Mermaid render pass status should be recorded here after validation is run.
