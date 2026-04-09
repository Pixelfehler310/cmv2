# Sprint 2 Scope Decision

## Purpose

Force one explicit Sprint 2 scope choice before implementation proceeds, so freeze interpretation and delivery expectations stay aligned.

## Decision Deadline

Decision must be recorded before first Sprint 2 implementation ticket is moved to active execution.

## Selected Option (Choose Exactly One)

- [ ] Option A: Compendium-only shipping scope
- [ ] Option B: Compendium + Character scope
- [ ] Option C: Compendium + Character + Campaign scope
- [x] Option D: Full Compendium CRUD Expansion + Full Character Sheet (Backend + Frontend)

## Decision Status

1. Status: In implementation cutover.
2. Effective date: 2026-04-10.
3. Owner sign-off: pending confirmation in execution board updates.

## Included Layer 1 Modules by Option

### Option A: Compendium-only shipping scope

1. CORE-01 Pack Lifecycle
2. CORE-02 Referential Integrity
3. CORE-03 Query and Projection Consistency
4. CORE-04 Session and Event Envelopes
5. CORE-05 Layer Ownership
6. DND5E-02 Content Schema
7. DND5E-03 Action Mechanics (integration touch only)
8. DND5E-04 Content Query Projection

### Option B: Compendium + Character scope

1. All Option A modules
2. DND5E-05 Character and Sheet Schema

### Option C: Compendium + Character + Campaign scope

1. All Option B modules
2. CAM-01 Campaign Management Context

### Option D: Full Compendium CRUD Expansion + Full Character Sheet (Backend + Frontend)

1. All Option B modules.
2. DND5E-02 family expansion to include `action`, `faction`, `region`, `place`.
3. Full-stack responsibility for compendium CRUD and search UX (backend and frontend).
4. Full-stack responsibility for character write and character-sheet projection UX.

## Explicit Out-of-Scope by Option

### Option A: Compendium-only shipping scope

1. DND5E-05 Character and Sheet Schema
2. CAM-01 Campaign Management Context

### Option B: Compendium + Character scope

1. CAM-01 Campaign Management Context

### Option C: Compendium + Character + Campaign scope

1. No intentional exclusions from current known Layer 1 modules.

### Option D: Full Compendium CRUD Expansion + Full Character Sheet (Backend + Frontend)

1. CAM-01 deep campaign policy expansion remains out of scope unless needed for ownership-safe CRUD visibility.
2. Search ranking science features (semantic ranking/synonyms) remain out of scope in Sprint 2.

## Sprint 2 Impact

### Option A: Include / Defer

1. Include: CM-01, CM-02, CM-03, CM-04, CM-05
2. Defer: CM-06 until base tickets are accepted
3. Defer all character/campaign-specific implementation tickets

### Option B: Include / Defer

1. Include: CM-01, CM-02, CM-03, CM-04, CM-05
2. Include: character-focused implementation tickets derived from DND5E-05
3. Defer campaign-context implementation tickets

### Option C: Include / Defer

1. Include: CM-01, CM-02, CM-03, CM-04, CM-05
2. Include: character-focused implementation tickets derived from DND5E-05
3. Include: campaign-context implementation tickets derived from CAM-01

### Option D: Include / Defer

1. Include: CM-01, CM-02, CM-03, CM-04, CM-05.
2. Include: CM-07 and CM-08 with production frontend integration requirements.
3. Include: compendium family expansion work for `action`, `faction`, `region`, and `place`.
4. Include: practical advanced search scope (text + lifecycle + family + pack + family-aware payload filters + deterministic sorting/pagination).
5. Defer: CAM-01 full campaign policy expansion unless directly required to unblock CRUD ownership semantics.

## Sign-off

1. Owner: simon
2. Date: 2026-04-10
3. Notes: Option D cutover started. Prior Option B is superseded for Sprint 2 execution.

## Architecture Readiness Prerequisites

Before implementation starts, all of the following must be true:

1. `ISSUES/architecture/01_contracts/APPROVAL_LOG.md` marks all in-scope modules as `Frozen`.
2. Every in-scope module has a completed scorecard based on `ISSUES/architecture/01_contracts/MODULE_DETAIL_SCORECARD_TEMPLATE.md`.
3. Module score threshold is met (`>=85` each, no exceptions).
4. Portfolio threshold is met (`average >=88`, at least 4 core-heavy modules `>=90`).
5. Freeze readiness checks in `ISSUES/architecture/01_contracts/FREEZE_GATE_STATUS.md` and this scope decision remain aligned.
