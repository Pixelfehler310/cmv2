# Legacy Deep Dive: V05 Contract Harvest Baseline

## Purpose
Capture the important reusable architecture from legacy V05 planning before adaptation into horizontal Layer 1 contracts.

## Reusable Legacy Strengths
1. Clear split between write path and read path.
2. Explicit link integrity and cycle denial concerns.
3. Revision-driven query and projection consistency model.
4. Polymorphic action payload model for execution graphs.

## Legacy Coupling To Exclude
1. ORM and persistence details in contract docs.
2. Vertical endpoint and repository implementation decisions.
3. Campaign and asset specifics when defining generic core contracts.

## Adaptation Decision
Use gold implementation in `backend/src/systems/dnd5e/content` as canonical symbol source. Use legacy V05 as semantic source and rationale.

## Source Files
1. `ISSUES/archive/vertical_legacy/v05/V05_macro_architecture_overview.mmd`
2. `ISSUES/archive/vertical_legacy/v05/V05_business_and_content_entities_class_diagram.mmd`
3. `ISSUES/archive/vertical_legacy/v05/V05_compendium_crud_and_definition_catalog_detailed_plan.mmd`
4. `ISSUES/archive/vertical_legacy/v05/V05_content_management_query_and_projection_detailed_plan.mmd`
5. `ISSUES/archive/vertical_legacy/v05/V2_action_mechanics_specification.md`
