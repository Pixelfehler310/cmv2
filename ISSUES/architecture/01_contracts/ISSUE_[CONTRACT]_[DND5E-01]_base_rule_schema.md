# ISSUE [CONTRACT] [DND5E-01]: DND5E Contract Index

## Why This Exists

This is the umbrella index for DND5E Layer 1 contracts. The original base schema draft has been split into focused modules to support independent implementation and testing.

## Active DND5E Contract Modules

1. Content schema: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-02]_content_schema.md`
2. Action mechanics: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-03]_action_mechanics.md`
3. Content query and read-model contracts: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-04]_content_query_projection.md`

## Planned Layer 1 Modules (Coverage Gaps)

1. Character and character-sheet schema contract: `ISSUES/architecture/01_contracts/dnd5e/ISSUE_[CONTRACT]_[DND5E-05]_character_and_sheet_schema.md`
2. Campaign management context contract: `ISSUES/architecture/01_contracts/campaign/ISSUE_[CONTRACT]_[CAM-01]_campaign_management_context.md`

## Coverage Notes

1. Current active modules primarily cover compendium/content management behavior.
2. Character and campaign-management domains are not yet freeze-ready and must be defined before broad-scope Layer 2 rollout.

## Core Contract Dependencies

DND5E contracts depend on these Core modules:

1. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-01]_pack_lifecycle.md`
2. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-02]_referential_integrity.md`
3. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-03]_query_projection_consistency.md`
4. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-04]_session_event_envelopes.md`
5. `ISSUES/architecture/01_contracts/core/ISSUE_[CONTRACT]_[CORE-05]_layer_ownership.md`

## Canonical Symbol Baseline

When ambiguity exists, use symbols from the gold implementation:

1. `backend/src/systems/dnd5e/content/domain/primitives.py`
2. `backend/src/systems/dnd5e/content/domain/definition_models.py`
3. `backend/src/systems/dnd5e/content/domain/link_models.py`
4. `backend/src/systems/dnd5e/content/domain/invariants.py`

## Status

- [x] DND5E contract split initialized.
- [x] DND5E module-level diagrams created.
- [x] DND5E test plans scaffolded.
- [ ] Freeze gate review complete.
- [ ] Character-sheet contract module defined (DND5E-05).
- [ ] Campaign management contract module defined (CAM-01).
