# Sprint 2 Scope Decision

## Purpose

Force one explicit Sprint 2 scope choice before implementation proceeds, so freeze interpretation and delivery expectations stay aligned.

## Decision Deadline

Decision must be recorded before first Sprint 2 implementation ticket is moved to active execution.

## Selected Option (Choose Exactly One)

- [ ] Option A: Compendium-only shipping scope
- [x] Option B: Compendium + Character scope
- [ ] Option C: Compendium + Character + Campaign scope

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

## Explicit Out-of-Scope by Option

### Option A: Compendium-only shipping scope

1. DND5E-05 Character and Sheet Schema
2. CAM-01 Campaign Management Context

### Option B: Compendium + Character scope

1. CAM-01 Campaign Management Context

### Option C: Compendium + Character + Campaign scope

1. No intentional exclusions from current known Layer 1 modules.

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

## Sign-off

1. Owner: simon
2. Date: 2026-04-06
3. Notes: Option B confirmed. Campaign scope (CAM-01) is deferred for Sprint 2.
