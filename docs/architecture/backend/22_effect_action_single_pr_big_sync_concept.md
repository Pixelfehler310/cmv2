# Effect and Action Single-PR Big Sync Concept

Date: 2026-03-17
Status: Proposed

This concept defines a single large synchronization PR that lands the full effect/action data-driven stack in one merge, instead of staged PR sequencing.

Primary references:

- [docs/architecture/backend/18_effect_engine_data_driven_adaptation_concept.md](docs/architecture/backend/18_effect_engine_data_driven_adaptation_concept.md)
- [docs/architecture/backend/19_effect_engine_aoe_multi_target_concept.md](docs/architecture/backend/19_effect_engine_aoe_multi_target_concept.md)
- [docs/architecture/backend/20_actions_abilities_data_driven_hybrid_concept.md](docs/architecture/backend/20_actions_abilities_data_driven_hybrid_concept.md)
- [docs/architecture/backend/21_effect_action_data_driven_pr_roadmap.md](docs/architecture/backend/21_effect_action_data_driven_pr_roadmap.md)
- [docs/architecture/frontend/16_action_visualization_contract_and_multimode_note.md](docs/architecture/frontend/16_action_visualization_contract_and_multimode_note.md)

## 1. Intent

Ship canonical contracts, persistence, executable action projection, effect execution, AoE/multi-target semantics, and frontend contract rendering in one coordinated PR.

This is a "big sync" strategy for teams that prefer one integration branch with one review/merge gate.

## 2. Architecture Constraints (Non-Negotiable)

- Backend is authoritative truth. Frontend renders backend output only.
- Rules are data-driven from canonical definitions (ActionDefinition, AbilityBinding, EffectDefinition, EffectInstance).
- Deterministic terminal response behavior must hold for all command paths.
- Canonical effect identity must be preserved end-to-end via `effect_id`.
- Preview and execute must share target derivation semantics for parity.

## 3. Big Sync Scope

The single PR must include all of the following:

1. Canonical contracts and schema docs

- ActionDefinition, AbilityBinding, EffectDefinition, EffectInstance contract stability.
- Denied reason taxonomy updates (including AoE/multi-target reasons).

2. Persistence and ingestion

- DB persistence for canonical definitions and effect instances.
- JSON content-pack ingestion and validation with conflict policy hooks.

3. Executable action projection

- Action deck snapshot projected from canonical data + runtime state.
- Stable outbound snapshot fields with backend-owned availability.

4. Effect engine integration

- Resolver to effect intent execution bridge.
- Effect apply/refresh/remove/tick lifecycle with provenance.
- Stacking and concentration semantics.

5. AoE and multi-target semantics

- Backend-derived TargetSet/derived targets for execute.
- Per-target deterministic outcomes and denied reasons.
- Preview/execute parity checks.

6. Frontend contract rendering baseline

- Command rendering from backend snapshot only.
- Select -> preview -> execute flow without local gameplay rules.

7. Hardening and release evidence

- Acceptance matrix expansion for action/effect/AoE paths.
- Regression tests for reason codes and request correlation.
- Migration/changelog updates.

## 4. Single-PR Execution Structure (Inside One PR)

Even in one PR, implementation should be organized as explicit internal phases/commits to reduce review risk:

- Phase A: Contracts + types + docs.
- Phase B: Persistence + import pipeline.
- Phase C: Snapshot projection.
- Phase D: Effect execution core.
- Phase E: AoE/multi-target parity and denied taxonomy.
- Phase F: Frontend contract-only rendering.
- Phase G: Matrix, regression, and release notes.

Recommendation: require each phase to remain independently readable and testable by commit.

## 5. Canonical effect_id Sync Requirement

The big sync PR must satisfy full canonical identity continuity:

- `effect_id` present in canonical effect definitions.
- `effect_id` carried in runtime effect instance shape.
- `effect_id` emitted in effect lifecycle outbound events.
- `effect_id` persisted in effect instance records.
- `effect_id` retained in per-target AoE/multi-target outcomes.
- `effect_id` used as canonical matching key for stacking/refresh/replace decisions.

No fallback path should silently degrade canonical identity to display name fields.

## 6. Determinism and Parity Rules

1. Target derivation

- Execute path must derive eligible/resolved targets from backend geometry + state.
- Client target hints are optional and must be validated.

2. Terminal behavior

- Commands end in a deterministic terminal outbound class: success, denied, or error.
- Denied reason vocabulary must remain canonical and stable.

3. Request correlation

- All effect lifecycle events include request/action provenance.

4. Preview/execute parity

- If world state drifts, execute returns updated deterministic results and reasons.

## 7. Risk Profile of One Big PR

Key risks:

- Cross-layer drift (backend contracts vs frontend types).
- Late discovery of regressions due broad blast radius.
- Reviewer overload from mixed concerns in one diff.

Mitigations:

- Feature flags for high-risk branches (effect execution, AoE semantics, frontend switch).
- Commit partitioning by internal phase.
- Mandatory contract diff summary in PR description.
- Mandatory backend + frontend type checks and targeted smoke logs.

## 8. Rollback Strategy

- Keep old projection and old UI controls behind temporary feature switches for one cycle.
- If big sync fails in staging, disable new flags and preserve previous stable flow.
- Avoid destructive migrations in the first merge; prefer additive schema where possible.

## 9. Merge Gate Checklist

The one PR is merge-ready only if all are true:

1. Contract docs and shipped payloads match.
2. Backend tests for effect lifecycle and AoE parity are green.
3. Frontend renders from backend snapshot with no local rules fallback.
4. Canonical `effect_id` is observable in events and persistence.
5. Docker smoke logs confirm request_id-correlated command paths.

## 10. Exit Conditions

The single-PR big sync is complete when:

1. Actions/effects are authored and modified through canonical data paths.
2. Resolver executes effect behavior from canonical definitions.
3. AoE/multi-target execution is deterministic and parity-tested.
4. Frontend action surfaces are contract-driven views of backend truth.
5. Canonical `effect_id` is end-to-end stable across definition, runtime, events, and storage.
