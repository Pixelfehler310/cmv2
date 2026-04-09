# Sprint 2 Execution Control Tower

## Purpose

Provide a single always-current control view for Sprint 2 so implementation status, next steps, and test readiness are visible across devices and sessions.

This document is the grand-scope control layer.
Use `SPRINT_02_MANUAL_VERIFICATION_RUNBOOK.md` for exact verification procedures.

## Scope Baseline

1. Scope option: **Option B (Compendium + Character)**.
2. Source: `SPRINT_02_SCOPE_DECISION.md`.
3. In-scope implementation tickets:
   - CM-01, CM-02, CM-03, CM-04, CM-05, CM-07, CM-08
4. Stretch ticket:
   - CM-06
5. Out of scope in this sprint:
   - CAM-01 campaign-context implementation work

## Snapshot (2026-04-09)

### Progress Math

1. Option B required path: `7 / 7` tickets have implementation artifacts landed in git history.
2. Option B verification-locked path: `5 / 7` tickets are currently documented as complete in board evidence.
3. Full board including stretch: `7 / 8` tickets have implementation artifacts; `CM-06` remains not started.
4. Overall implementation artifact coverage: `87.5%` (`7 / 8`).

### Last-4-Commit Signal Analysis

| Commit    | Signal                                                                                                           | Impact on Sprint 2                                                                                                    |
| :-------- | :--------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `ffe5812` | CM-07/CM-08 landed (character write + sheet projection), new migrations, router wiring, generated frontend types | Moves character track from design-only to implementation-present. Validation and integration sign-off still required. |
| `c627df0` | Legacy test exclusion guard in `backend/tests/conftest.py`                                                       | Stabilizes test execution boundary and reduces noise from legacy paths.                                               |
| `750c1ef` | PR-2 transport/WS and test import fixes                                                                          | Hardens CORE-04 envelope behavior and transport-level testability.                                                    |
| `f0e68cd` | Core infrastructure + policy/test strengthening                                                                  | Consolidates CM-01..CM-05 contract implementation quality and scorecard alignment.                                    |

## Ticket Control Matrix

Legend:

- `Implemented`: code path exists in active branch.
- `Verified`: implementation + required checks passed and recorded.
- `Ready for Frontend`: endpoint and envelope behavior are stable enough for UI integration.

| Ticket | Contract Focus              | Implementation State           | Verification State                                             | Endpoint Gate                                                                 | Frontend Gate                                                                                    | Next Required Action                                            |
| :----- | :-------------------------- | :----------------------------- | :------------------------------------------------------------- | :---------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------- | :-------------------------------------------------------------- |
| CM-01  | Lifecycle write path        | Implemented                    | Verified (board evidence)                                      | Create/update/publish/delete flows deterministic                              | Safe to consume lifecycle states in UI                                                           | Keep regression checks in runbook cadence                       |
| CM-02  | Query pipeline              | Implemented                    | Verified (board evidence)                                      | List/detail/search revision-aware responses                                   | Safe for list/detail screens                                                                     | Keep deterministic ordering checks                              |
| CM-03  | Link resolution             | Implemented                    | Verified (board evidence)                                      | Missing link denials + replacement-chain behavior                             | Safe for linked-reference rendering with denial UI                                               | Keep unresolved marker checks                                   |
| CM-04  | Recovery loop               | Implemented                    | Verified (board evidence)                                      | Revision-gap invalidation and stale-event handling                            | Safe for cache invalidation behavior in UI                                                       | Keep gap/stale branch checks                                    |
| CM-05  | API/WS envelopes            | Implemented                    | Verified (board evidence)                                      | Stable `resolved/denied/error` envelope semantics                             | Safe for transport adapter + WS client mapping                                                   | Keep request-id/reason-code checks                              |
| CM-06  | Action integration smoke    | Not started                    | Not verified                                                   | No dedicated endpoint smoke implemented yet                                   | Not frontend-ready                                                                               | Create CM-06 implementation issue + minimal smoke test path     |
| CM-07  | Character write + ownership | Implemented (commit `ffe5812`) | Validation pending in sprint board                             | `POST /api/characters`, `PUT /api/characters/{id}` with deterministic denials | Backend endpoint is present; frontend form integration can begin once validation run is recorded | Execute runbook section CM-07 and record pass/fail evidence     |
| CM-08  | Sheet Projection            | Implemented (commit `ffe5812`) | Verification Complete (2026-04-09: 12/12 automated tests pass) | `GET /api/characters/{id}/sheet` with `resolved/denied/invalidated` outcomes  | Endpoint shape and envelope mapping verified; frontend sheet view integration ready to unblock   | ✅ Verification passed; ready for frontend endpoint integration |

## Readiness Ladder (When You Can Test What)

1. **Level A: Backend Contract Health (CM-01..CM-05)**
   - Goal: Domain and envelope contracts are stable.
   - Test mode: automated backend tests.

2. **Level B: Endpoint-Usable Character Write (CM-07)**
   - Goal: character create/update endpoints return stable envelopes and denial taxonomy.
   - Test mode: API-level tests + manual endpoint smoke.

3. **Level C: Endpoint-Usable Character Sheet (CM-08)**
   - Goal: projection endpoint supports resolved, denied, invalidated branches with revision metadata.
   - Test mode: API-level tests + manual endpoint smoke.

4. **Level D: Frontend Vertical Slice (CM-07 + CM-08)**
   - Goal: minimal UI can create/update character and render sheet projection outcomes.
   - Test mode: UI against live backend with known fixture flow.

5. **Level E: Action Integration Confidence (CM-06)**
   - Goal: character sheet outputs survive action payload integration touch.
   - Test mode: focused smoke scenario.

## Operational Workflow (Daily)

1. Open this file and mark the current ladder level.
2. Run only the runbook sections relevant to the active ticket.
3. Record evidence outcome in `SPRINT_02_CONTENT_MANAGEMENT_BOARD.md` completion matrix notes.
4. If a contract drift is detected, stop feature expansion and re-open architecture review gate before proceeding.

## Current Blockers and Constraints

1. Containerized verification is currently blocked on this device because Docker engine is unavailable.
2. Until Docker is running, verification evidence should be treated as pending even when implementation artifacts are present.

## Immediate Next Sequence

1. Start Docker engine and run CM-07/CM-08 targeted verification commands from the runbook.
2. Mark CM-07 and CM-08 as verified (or log failures) in the board completion matrix.
3. Build one minimal frontend vertical slice using generated character types.
4. Decide whether CM-06 remains stretch or is promoted into mandatory closure for Sprint 2.
