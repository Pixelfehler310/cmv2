# Combat Slice Refactor Issue Tracker

This folder tracks architecture hardening and follow-up issues for the combat slice.

Status summary:

- PR1 to PR5 completed.
- Remaining PR tracker in this folder: PR6.

Current focus:

1. PR6 hardening tests/docs/guardrails.

Cross-cutting constraints:

- Backend is source of truth.
- Keep WS and REST contract shapes stable unless explicitly versioned.
- Remove obsolete fallback behavior when it conflicts with MVP target architecture.
- Keep each change independently mergeable and runnable.

Verification baseline for every architecture issue:

1. Run targeted backend tests for touched slice.
2. Run contract drift check if models/types are touched.
3. Validate no transport-level direct persistence access is introduced.
4. Check backend container logs for regressions after restart.

Vertical architecture track (high-level only):

1. `ISSUE_[VERT]_[V00]_vertical_modularization_program_board.md`
2. `ISSUE_[VERT]_[V01]_runtime_hierarchy_and_encounter_lifecycle.md`
3. `ISSUE_[VERT]_[V02]_combat_actions_turn_economy_and_effects.md`
4. `ISSUE_[VERT]_[V03]_world_context_runtime.md`
5. `ISSUE_[VERT]_[V04]_content_schema_and_pack_lifecycle.md`
6. `ISSUE_[VERT]_[V05]_compendium_crud_and_definition_catalog.md`
7. `ISSUE_[VERT]_[V06]_event_contracts_and_frontend_projection.md`

Planning policy:

1. Deep child issues are created only for the currently active module.
