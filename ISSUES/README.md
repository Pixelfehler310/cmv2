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
