# Sprint 2 Execution Control Tower

## Purpose

Provide a single always-current control view for Sprint 2 so implementation status, next steps, and test readiness are visible across devices and sessions.

This document is the grand-scope control layer.
Use `SPRINT_02_MANUAL_VERIFICATION_RUNBOOK.md` for exact verification procedures.

## Scope Baseline

1. Scope option: **Option D (Full Compendium CRUD Expansion + Full Character Sheet)**.
2. Source: `SPRINT_02_SCOPE_DECISION.md`.
3. In-scope implementation tickets:
   - CM-01, CM-02, CM-03, CM-04, CM-05, CM-07, CM-08, CM-09, CM-10, CM-11, CM-12
4. Stretch ticket:
   - CM-06
5. Out of scope in this sprint:
   - CAM-01 deep campaign policy expansion work

## Snapshot (2026-04-10 updated)

### Progress Math

1. Option D required path: `8 / 11` tickets have implementation artifacts landed in git history (CM-01..CM-05, CM-07, CM-08, CM-11).
2. Option D verification-locked path: `6 / 11` tickets are currently documented as complete in board evidence (CM-01..CM-05, CM-08, CM-11).
3. Full board including stretch: `8 / 12` tickets have implementation artifacts; `CM-06`, `CM-09`, `CM-10`, `CM-12` incomplete.
4. Overall implementation artifact coverage: `66.7%` (`8 / 12`).
5. **CM-11 Status Update**: Advanced search backend contract completed 2026-04-10 with 27 passing tests, frontend bridge integration complete, host build passing. Ready for frontend filter UI wiring.

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

| Ticket | Contract Focus              | Implementation State           | Verification State                                             | Endpoint Gate                                                                 | Frontend Gate                                                                                    | Next Required Action                                             |
| :----- | :-------------------------- | :----------------------------- | :------------------------------------------------------------- | :---------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------- | :--------------------------------------------------------------- |
| CM-01  | Lifecycle write path        | Implemented                    | Verified (board evidence)                                      | Create/update/publish/delete flows deterministic                              | Safe to consume lifecycle states in UI                                                           | Keep regression checks in runbook cadence                        |
| CM-02  | Query pipeline              | Implemented                    | Verified (board evidence)                                      | List/detail/search revision-aware responses                                   | Safe for list/detail screens                                                                     | Keep deterministic ordering checks                               |
| CM-03  | Link resolution             | Implemented                    | Verified (board evidence)                                      | Missing link denials + replacement-chain behavior                             | Safe for linked-reference rendering with denial UI                                               | Keep unresolved marker checks                                    |
| CM-04  | Recovery loop               | Implemented                    | Verified (board evidence)                                      | Revision-gap invalidation and stale-event handling                            | Safe for cache invalidation behavior in UI                                                       | Keep gap/stale branch checks                                     |
| CM-05  | API/WS envelopes            | Implemented                    | Verified (board evidence)                                      | Stable `resolved/denied/error` envelope semantics                             | Safe for transport adapter + WS client mapping                                                   | Keep request-id/reason-code checks                               |
| CM-06  | Action integration smoke    | Not started                    | Not verified                                                   | No dedicated endpoint smoke implemented yet                                   | Not frontend-ready                                                                               | Create CM-06 implementation issue + minimal smoke test path      |
| CM-07  | Character write + ownership | Implemented (commit `ffe5812`) | Validation pending in sprint board                             | `POST /api/characters`, `PUT /api/characters/{id}` with deterministic denials | Backend endpoint is present; frontend form integration can begin once validation run is recorded | Execute runbook section CM-07 and record pass/fail evidence      |
| CM-08  | Sheet Projection            | Implemented (commit `ffe5812`) | Verification Complete (2026-04-09: 12/12 automated tests pass) | `GET /api/characters/{id}/sheet` with `resolved/denied/invalidated` outcomes  | Endpoint shape and envelope mapping verified; frontend sheet view integration ready to unblock   | ✅ Verification passed; ready for frontend endpoint integration  |
| CM-09  | Family Expansion            | In Progress                    | Partial verification complete (targeted transport + parity)    | Unified compendium accepts `action/faction/region/place` family payloads      | Enables frontend CRUD waves for added families                                                   | Complete contract drift artifacts + full backend test matrix     |
| CM-10  | Frontend CRUD Cutover       | Not started                    | Not verified                                                   | Requires mutation-capable frontend API bridge                                 | Production CRUD views must replace legacy object-route dependence                                | Implement unified compendium client + CRUD view shells           |
| CM-11  | Advanced Search             | Implemented (verified)         | Verified (27 tests passing 2026-04-10, frontend build clean)   | Family-aware payload filters, deterministic ordering, pagination stable       | Safe to wire family filter selectors and advanced search UI in compendium                        | ✅ Verification passed; ready for frontend filter UI integration |
| CM-12  | Production Character FE     | Not started                    | Not verified                                                   | Requires CM-07 and CM-08 endpoint integration                                 | Character create/edit/sheet must be production-routed, not debug-only                            | Build character flow route and wire projection states            |

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

6. **Level F: Full Product Vertical (CM-09..CM-12)**
   - Goal: full-stack compendium CRUD and character-sheet delivery across all in-scope families.
   - Test mode: backend + frontend integrated verification matrix.

## Operational Workflow (Daily)

1. Open this file and mark the current ladder level.
2. Run only the runbook sections relevant to the active ticket.
3. Record evidence outcome in `SPRINT_02_CONTENT_MANAGEMENT_BOARD.md` completion matrix notes.
4. If a contract drift is detected, stop feature expansion and re-open architecture review gate before proceeding.

## Current Blockers and Constraints

1. Contract drift updates for DND5E-02 expansion require approval-log/freeze-gate sync before broad implementation proceeds.
2. Full `backend-test` service currently fails fixture JSON gate in this branch; targeted verification requires running with `RUN_JSON_FIXTURE_CHECKS=false` until fixture schema alignment work lands.

## Immediate Next Sequence

1. Complete CM-09 contract-gate paperwork (approval/freeze alignment for new families).
2. ✅ **COMPLETED**: CM-11 backend practical advanced search (family-aware payload filters + deterministic ordering) — landed 2026-04-10 with full test coverage and frontend build passing.
3. **IN PROGRESS**: CM-12 production character frontend route wiring on top of CM-07/CM-08 endpoints.
4. CM-10 frontend unified compendium client mutation surface (runs in parallel with CM-12).
5. Frontend CRUD wave deliveries for all in-scope families (dependent on CM-09 contract approval and CM-10 hook availability).
