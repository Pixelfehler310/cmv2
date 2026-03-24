# Backend Diagram Correctness Review

Status: Draft Review
Scope: docs/diagrams/mmd and mirrored d2 diagrams
Perspective order: Combat, Content Management (CRUD), Architecture

## Core Assumption Used For This Review

Campaigns are split into scenes.
Encounter is treated as a specialized scene state and should not be modeled as a separate top-level layer.

## Executive Summary

- Overall structure is strong and already close to a maintainable layered design.
- Most critical issues are concentrated in runtime combat modeling and persistence semantics.
- Main blockers:
  - Encounter and scene hierarchy is not represented consistently.
  - Effect runtime model does not fully carry concentration and removal semantics.
  - Content CRUD is missing lifecycle and authorship metadata in the diagramed persistence layer.

## Diagram-by-Diagram Findings

## D2.1 Transport and Session

Combat view:

- Correct as transport boundary.
- No critical combat logic leakage.

Content view:

- Acceptable for transport, but no authoring context (expected for this layer).

Architecture view:

- Good separation and low coupling.

Verdict: Correct for purpose.

## D2.2 Shared Primitives and Enums

Combat view:

- Good reusable value types for AoE, saves, abilities.
- Verify enum parity with source to avoid drift.

Content view:

- Missing content lifecycle enums (draft/published/deprecated) and classification enums.

Architecture view:

- Strong foundational layer.

Verdict: Good base, needs content-lifecycle primitives if authoring is first-class.

## D2.3 Definitions and Contracts

Combat view:

- Template side is rich and supports action and effect definitions.
- Some fields are too weakly typed for strict resolver validation.

Content view:

- Important gaps for CRUD completeness:
  - no explicit description strategy across all contract records
  - no lifecycle status model
  - no explicit author/provenance/audit fields at diagram level

Architecture view:

- Namespace naming can mislead: contracts here are content schemas, not layer interfaces.

Verdict: Functionally useful, but needs clearer schema intent and stronger content governance metadata.

## D2.4 Runtime Instances and Encounter State

Combat view:

- This is the most important combat diagram and currently the most sensitive.
- Key gaps:
  - effect lifecycle details are under-modeled for removal and concentration ownership clarity
  - encounter is shown as a top-level container without explicit scene parent
  - turn budget typing is too loose at runtime level

Content view:

- Provenance for runtime instance origin is present but too opaque.

Architecture view:

- Violates desired hierarchy unless scene contains active encounter state.

Verdict: Needs refactor to SceneState as parent container with EncounterState as specialized active combat state.

## D2.5 Event Payloads

Combat view:

- Good command and response family separation.
- Could be stricter for targeting metadata and movement cost semantics.

Content view:

- Not a CRUD layer and should stay focused on runtime transport.

Architecture view:

- Good boundary location and low risk.

Verdict: Solid, with optional stricter typing for payload internals.

## D2.6 Services and Application DTOs

Combat view:

- Correct orchestration intent.
- Validation and authorization flow should remain explicit before effect execution.

Content view:

- Content management services are not represented here.

Architecture view:

- Repository abstraction is not visible in diagram, which weakens microservice-ready narrative.

Verdict: Good start, but add repository interface layer in diagrams.

## D2.7 Domain Policy Objects

Combat view:

- Good policy separation for authorization and action economy.
- Missing explicit policy coverage for free interaction and reaction trigger context can cause future rules ambiguity.

Content view:

- No content governance policy objects represented.

Architecture view:

- Domain policy split is clear and maintainable.

Verdict: Good domain seed, needs expansion for complete combat policy semantics.

## D2.8 Persistence ORM Models

Combat view:

- Persistence entities are comprehensive but scene and encounter relation should be made unambiguous.

Content view:

- Strong base entities for actions/effects/bindings.
- Missing explicit authoring lifecycle and descriptive metadata in diagram model.

Architecture view:

- Mixed generic campaign and system-specific character concerns should be separated more clearly.

Verdict: High-value diagram, but needs scene-encounter normalization and cleaner namespace boundaries.

## Required Changes by Perspective

## Combat Perspective (Priority Order)

1. Introduce SceneState runtime container and model EncounterState as scene-specialized active state.
2. Enrich runtime effect instance semantics to clearly represent concentration ownership and removal lifecycle behavior.
3. Replace loose turn budget dict shape in diagrams with typed budget model.
4. Tighten payload typing for targeting and movement semantics where resolver correctness depends on shape.

## Content Management Perspective (Priority Order)

1. Add content lifecycle fields and enums at diagram level:
   - status
   - deprecated and replacement linkage
2. Add authoring and provenance metadata fields:
   - author
   - modified_by
   - created_at and updated_at
3. Ensure description support is explicit and consistent across content records.
4. Add clear import/export and version compatibility responsibilities in service diagrams.

## Architecture Perspective (Priority Order)

1. Enforce hierarchy: Campaign -> Scene -> optional active Encounter.
2. Add repository abstraction layer in service/application diagrams.
3. Separate generic campaign/identity persistence from system-specific DND5e persistence namespace.
4. Rename ambiguous diagram namespaces where they imply interface contracts but actually represent content schemas.

## Concrete Diagram Edit Checklist

- D2.4:
  - add SceneState
  - make EncounterState child or specialization path
  - type turn budget model
  - complete effect runtime lifecycle semantics
- D2.8:
  - normalize scene and encounter persistence relation to match scene-first model
  - split generic and DND5e-specific persistence concerns
- D2.6:
  - add repository interfaces between application and persistence
- D2.3:
  - rename contract namespace to content schema semantics
  - add lifecycle and authorship fields for content CRUD completeness
- D2.5:
  - optional tightening of targeting and movement payload schema

## Suggested Target Diagram Set Adjustment

Current set can remain, but add three focused extensions:

- D2.4.1 Scene Encounter Hierarchy Runtime
- D2.6.1 Repository Interfaces and Boundaries
- D2.8.1 Persistence Boundary Split Generic vs DND5e

This keeps readability while fixing semantic and architectural correctness.

## Final Assessment

- Combat correctness: Partially correct, with critical runtime hierarchy and effect lifecycle gaps.
- Content CRUD correctness: Partially correct, missing lifecycle and authoring metadata.
- Architectural correctness: Mostly correct layering, but needs explicit scene-first hierarchy and repository boundary in diagrams.

Overall recommendation: Proceed with targeted revision, not full rewrite.

## Implemented Consolidated Diagram

- [docs/diagrams/mmd/D2.9_target_corrected_architecture.mmd](../diagrams/mmd/D2.9_target_corrected_architecture.mmd)

This diagram implements the proposed corrections in one synthesized target view:

- Scene-first hierarchy with Encounter as specialized active scene state.
- Explicit repository boundary between application services and persistence.
- Typed turn budget model with free interaction slot.
- Enriched effect runtime semantics for concentration ownership and removal triggers.
- Content lifecycle and authorship metadata for CRUD completeness.
- Split persistence perspective into generic campaign/identity and DND5e-specific records.
