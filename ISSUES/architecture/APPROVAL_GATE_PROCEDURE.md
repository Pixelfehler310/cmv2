# Architecture Approval Gate Procedure

This procedure defines the mandatory approval gates for architecture-spec work before implementation starts.

## Scope

Applies to all Layer 1 and pre-implementation Layer 2 architecture artifacts in:

1. `ISSUES/architecture/01_contracts/`
2. `ISSUES/architecture/04_module_specifications/`
3. `ISSUES/architecture/02_implementations/` planning artifacts that claim readiness

## Stage Model

### Stage 1: Draft

Required outputs:

1. Contract or module annex draft exists.
2. Mermaid diagrams render.
3. Test-plan intent exists.

Exit condition:

1. Artifact is reviewable and linked in `ISSUES/architecture/01_contracts/APPROVAL_LOG.md`.

### Stage 2: Diagram Review

Required outputs:

1. Class, sequence, and activity diagrams are reviewed for boundary correctness.
2. Context objects and constraints are aligned to sibling modules.
3. Review feedback is applied at least once.

Exit condition:

1. Reviewer marks Stage 2 approved in `ISSUES/architecture/01_contracts/APPROVAL_LOG.md`.

### Stage 3: Freeze Review

Required outputs:

1. Module annex passes all high-bar completion criteria.
2. Scorecard threshold is met.
3. Traceability links are complete.

Exit condition:

1. Module is marked `Frozen` in `ISSUES/architecture/01_contracts/APPROVAL_LOG.md` and referenced in `ISSUES/architecture/01_contracts/FREEZE_GATE_STATUS.md`.

### Stage 4: Drift Control

Required outputs:

1. Any post-freeze change to diagrams, method contracts, constraints, or context objects triggers re-review.
2. Drift entries are logged with reason and approval date.

Exit condition:

1. Module returns to `Frozen` with updated scorecard and approval record.

## High-Bar Completion Criteria

A module is not complete unless all criteria below pass.

1. Diagram set completeness:

- One class diagram per module.
- Minimum two sequence diagrams per module.
- Minimum one activity diagram per module.

2. Class depth:

- Core-heavy modules (`runtime`, `actions`, `content_write`, `content_query`) require at least 8 primary classes.
- Support modules (`campaigns`, `sheets`, `identity`, `assets`, `events`, `recovery`, `shared`, `transport`) require at least 5 primary classes.
- Each primary class has at least 3 primary methods, except pure value objects.

3. Method coverage:

- Core-heavy modules require at least 20 externally callable methods.
- Support modules require at least 10 externally callable methods.
- Every method must include input, output, denial code family, and side effects.

4. Context object coverage:

- Minimum 4 named context objects per module.
- Each context object defines required fields, optional fields, producer, consumers, and mutation authority.

5. Critical-flow coverage:

- Core-heavy modules require at least 6 critical flows.
- Support modules require at least 4 critical flows.
- Every critical flow has resolved plus denied or recovery branches.

6. Quality score:

- Per-module minimum score: 85 out of 100.
- No module may pass below 85.
- At least 4 core-heavy modules must score 90 or above.
- Portfolio average must be at least 88.

## Scoring Source

Use `ISSUES/architecture/01_contracts/MODULE_DETAIL_SCORECARD_TEMPLATE.md` for scoring and evidence.

## Approval Authority

1. Primary approver: repository owner.
2. Optional reviewer: secondary architecture reviewer.
3. Freeze opens implementation only when explicit approval date is recorded.

## Implementation Start Rule

No implementation work may begin until:

1. Scope decision is documented in `ISSUES/architecture/02_implementations/SPRINT_02_SCOPE_DECISION.md`.
2. All in-scope modules are `Frozen` in `ISSUES/architecture/01_contracts/APPROVAL_LOG.md`.
3. `ISSUES/architecture/01_contracts/FREEZE_GATE_STATUS.md` references the same approved scope.
