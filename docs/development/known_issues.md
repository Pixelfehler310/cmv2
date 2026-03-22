# CMV2 Known Issues and Recovery Guide

This document consolidates currently reported architecture and product issues, then provides a pragmatic execution plan.

Status: Active triage document
Owner: Engineering
Last updated: 2026-03-22

## A. Known Issues

## A1. System Complexity and Direction Drift

Severity: High

Symptoms:

- Feature work has outpaced architecture guardrails.
- AI/code suggestions can become inconsistent because boundaries are unclear and context is too large.

Impact:

- Slower implementation velocity.
- Increased regression risk.
- More contradictory patterns in code.

Definition of done:

- Every major feature has a single owning module and clear API boundary.
- Architecture decision records exist for major cross-cutting decisions.

## A2. Backend Is Not Clearly Modular

Severity: Critical

Symptoms:

- Domain logic, transport concerns, and persistence details are mixed.
- Service boundaries are difficult to identify and test independently.

Impact:

- Hard to reason about behavior.
- Expensive changes and brittle tests.
- Blocks future microservice split.

Definition of done:

- Clear layer separation: routers -> application services -> domain logic -> repositories.
- No direct persistence access from routers.
- Domain logic testable without FastAPI and database wiring.

## A3. Frontend and Backend Contracts Are Not Clean

Severity: Critical

Symptoms:

- Frontend must compensate for backend inconsistencies.
- Contract ownership is not explicit and can drift.

Impact:

- Runtime breakages and difficult debugging.
- Duplicate mapping logic and brittle adapters.

Definition of done:

- Contract-first schemas for WS and REST are generated from backend models.
- Frontend compiles against generated types only.
- CI fails on schema/type drift.

## A4. Frontend Experience and App Roles Are Confusing

Severity: High

Symptoms:

- Unclear distinction between test harness views and production views.
- Unclear why player experience appears test-focused.

Impact:

- Product confusion and wrong implementation priorities.
- Testing artifacts leak into user-facing flows.

Definition of done:

- Explicit app taxonomy documented (host, dm-view, player-view, management-view, test harness).
- Test harness routes are separate and visibly marked.
- Production player flow is default for player role.

## A5. Encounter Defaults Are Hardcoded (Arannis/Goblin)

Severity: Critical

Symptoms:

- Encounter UI repeatedly shows fixed entities (for example Arannis and Goblin).
- Missing campaign/scene/encounter selection in active flow.

Impact:

- Cannot steer play state by campaign context.
- Invalidates real gameplay and QA scenarios.

Definition of done:

- Campaign -> Scene -> Encounter selector exists in host/DM flow.
- Selected context drives backend subscription and state sync.
- No hardcoded combatants in production paths.

## A6. Inconsistent Typing Across JSON, Backend, and Frontend

Severity: Critical

Symptoms:

- Data imports/exports and backend models may disagree.
- Frontend types may diverge from backend truth.

Impact:

- Parse errors, runtime defects, and silent data loss.
- Slow diagnosis of WS/REST failures.

Definition of done:

- Single schema source from backend Pydantic models.
- Versioned schema artifacts.
- End-to-end contract tests for representative payloads.

## A7. Action IDs Are Over-Specific (for example attack.arannis.sword)

Severity: High

Symptoms:

- Action identity includes actor-specific prefixes.
- Semantically generic actions are modeled as instance-specific keys.

Impact:

- Redundant content definitions.
- Weak reuse and harder balancing/content tooling.

Definition of done:

- Generic action definitions (for example weapon.sword.slash) are reusable.
- Actor state references generic action definitions + context modifiers.
- Backend resolves legality and outcomes using actor inventory/traits/effects.

## B. Recommendation: Reengineer or Not?

Short answer: do not do a full rewrite.

Recommended path:

- Perform a staged architectural refactor with strict boundaries.
- Keep working vertical slices alive while replacing internal seams.
- Remove legacy/fallback paths during MVP when they conflict with target architecture.

Why this is safer:

- You preserve delivery momentum.
- You reduce risk by proving each boundary with tests.
- You avoid creating a second, equally complex system in parallel.

## C. Execution Guide (What To Do First)

## Phase 0 (1-2 days): Stabilize and Create Visibility

Actions:

1. Freeze non-critical features.
2. Declare source-of-truth contract ownership: backend models -> generated schema -> frontend types.
3. Add this issue list to sprint board with owner and acceptance test per item.
4. Define and document app modes:
   - Production: host, dm-view, player-view
   - Tooling/test: command labs, harnesses, mocks

Deliverables:

- Architecture map (one page).
- Current route map and app-mode map.
- Prioritized backlog by risk.

## Phase 1 (3-5 days): Contract First, Type Safety First

Actions:

1. Enforce backend schema generation and frontend type generation in CI.
2. Introduce payload contract tests for:
   - state_sync
   - encounter selection/loading
   - action execution envelopes
3. Remove any frontend-side combat state calculations not strictly view-model mapping.

Deliverables:

- CI gate for schema/type drift.
- Passing contract tests for critical messages.

## Phase 2 (1 week): Runtime Context Selection (Campaign/Scene/Encounter)

Actions:

1. Add explicit selector flow in host/DM entry:
   - Campaign select
   - Scene select
   - Encounter select
2. Make selector state backend-authoritative and reflected in WS subscriptions.
3. Remove hardcoded demo encounter defaults from production runtime path.

Deliverables:

- Real context steering in UI.
- State changes reflected in backend logs and WS events.

## Phase 3 (1-2 weeks): Backend Modularization by Vertical Slice

Target backend structure:

- Routers: protocol only
- Application services: orchestration/use-cases
- Domain services/entities: rules and invariants
- Repositories: persistence adapters

Actions:

1. Pick one slice first (combat context load + action resolve).
2. Move logic to service layer and create interfaces for repositories.
3. Write service-level tests independent from FastAPI and DB.
4. Repeat slice by slice.

Deliverables:

- Clear layered boundaries in first slice.
- Template for continued migrations.

## Phase 4 (parallel): Generic Action Modeling

Actions:

1. Split action identifiers into:
   - definition_id (generic, reusable)
   - actor_id (instance context)
2. Build action resolution pipeline:
   - Validate actor can use definition.
   - Apply inventory/traits/effects modifiers.
   - Emit deterministic event payload.
3. Migrate existing actor-specific IDs to generic IDs + context.

Deliverables:

- No actor-specific IDs in canonical action catalog.
- Backward-compatible migration script (if needed during transition).

## D. Suggested Backlog Order

1. Contract and type alignment (highest leverage).
2. Campaign/scene/encounter selector and hardcoded default removal.
3. First backend slice modularization.
4. Generic action ID refactor.
5. Frontend app-mode separation cleanup.

## E. Guardrails To Keep AI and Team Output Consistent

1. Keep architecture docs short and authoritative.
2. Add a "where logic belongs" table in contributor docs.
3. Require each PR to state:
   - which layer changed
   - which contract changed
   - which generated artifacts were updated
4. Reject PRs that add hardcoded gameplay state to production paths.

## F. Decision Checklist Before Any New Feature

1. Is backend the source of truth for this behavior?
2. Is the contract schema updated and generated?
3. Can this be tested without the full stack?
4. Does this introduce new hardcoded campaign/encounter content?
5. Does this preserve modular boundaries?

If any answer is no, stop and fix architecture first.
