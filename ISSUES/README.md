# Combat Slice Refactor Issue Tracker

This folder tracks the remaining PRs after PR1.

Status summary:

- PR1 completed: baseline characterization tests + ADR + context application seam.
- Remaining PRs in this folder: PR2 to PR6.

Execution order:

1. PR2 context repositories + context application extraction
2. PR3 action execution application + repositories
3. PR4 domain extraction and service cleanup
4. PR5 remove fallback bypasses
5. PR6 hardening tests/docs/guardrails

Cross-cutting constraints:

- Backend is source of truth.
- Keep WS and REST contract shapes stable unless explicitly versioned.
- Remove obsolete fallback behavior when it conflicts with MVP target architecture.
- Keep each PR independently mergeable and runnable.

Verification baseline for every PR:

1. Run targeted backend tests for touched slice.
2. Run contract drift check if models/types are touched.
3. Validate no transport-level direct persistence access is introduced.
4. Check backend container logs for regressions after restart.
