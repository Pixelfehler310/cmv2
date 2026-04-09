# Sprint 2 Manual Verification Runbook

## Purpose

Define deterministic verification procedures for each Sprint 2 implementation ticket, including:

1. Backend automated checks (contract confidence)
2. Endpoint-level manual checks (API behavior)
3. Frontend integration gates (when UI work is safe)

Use with:

- `SPRINT_02_EXECUTION_CONTROL_TOWER.md` for status tracking
- `SPRINT_02_CONTENT_MANAGEMENT_BOARD.md` for recording evidence

## Verification Modes

### Mode 1: Contract-Automated (Primary)

Use targeted backend tests as the fastest reliable signal.

Preferred command pattern:

```bash
docker compose --profile test run --rm \
  -e RUN_BACKEND_TESTS=true \
  -e PYTEST_ARGS="<targeted tests> -q" \
  backend-test
```

### Mode 2: Endpoint Manual Smoke (Secondary)

Use live API calls once backend is running to validate behavior quickly from outside tests.

### Mode 3: Frontend Vertical Slice (Tertiary)

Use one thin UI path to ensure endpoint + envelope semantics are consumable by frontend code.

## Global Preconditions

1. Backend is running (`Docker: Up Backend` or full stack).
2. Database schema migrations are applied (startup path or Alembic path).
3. For live endpoint checks, request identity context is available (authenticated user/session).
4. For socket checks, at least one campaign room has an active WS client (`/ws/{campaign_id}`).

## CM-01 Verification: Definition Write + Lifecycle

### Automated checks

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="backend/tests/systems/dnd5e/content/test_compendium_service.py backend/tests/systems/dnd5e/content/integration/test_error_case_matrix.py -q" backend-test
```

### Endpoint smoke targets

1. `POST /api/compendium/definitions`
2. `PUT /api/compendium/definitions/{definition_id}`
3. `POST /api/compendium/definitions/{definition_id}/publish`
4. `DELETE /api/compendium/definitions/{definition_id}`
5. `POST /api/compendium/definitions/{definition_id}/supersede`

### Expected outcomes

1. Illegal lifecycle transitions return deterministic denial reason codes.
2. Draft-only delete rule is enforced.
3. Supersedence requires valid replacement target.

### Frontend gate

Safe to wire lifecycle controls after denial reason codes and lifecycle transitions are observed as stable.

## CM-02 Verification: Query List/Detail Determinism

### Automated checks

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="backend/tests/systems/dnd5e/content/integration/test_api_transport.py backend/tests/systems/dnd5e/content/test_search_index.py -q" backend-test
```

### Endpoint smoke targets

1. `GET /api/compendium/definitions?pack_id=<id>`
2. `GET /api/compendium/definitions/{definition_id}`
3. `GET /api/compendium/search`

### Expected outcomes

1. Deterministic ordering for same input and revision.
2. Revision metadata present for successful envelope paths.
3. Unsupported filter/sort combinations deny explicitly.

### Frontend gate

Safe to wire compendium list/detail/search UI after deterministic order and revision-bearing responses are confirmed.

## CM-03 Verification: Linked References + Denials

### Automated checks

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="backend/tests/systems/dnd5e/content/test_link_resolution.py backend/tests/systems/dnd5e/content/test_compendium_service.py -q" backend-test
```

### Endpoint smoke targets

1. `GET /api/compendium/definitions/{definition_id}/links`
2. `GET /api/compendium/definitions/{definition_id}/replacement-chain`

### Expected outcomes

1. Required missing references deny with stable reason code.
2. Replacement chains resolve to current visible terminal.
3. Partial-resolution behavior marks unresolved references explicitly.

### Frontend gate

Safe to render linked-reference sections with unresolved-reference UI states.

## CM-04 Verification: Projection Recovery Loop

### Automated checks

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="backend/tests/systems/dnd5e/content/test_ws_events_contract.py -q" backend-test
```

### Event smoke targets

1. `content_projection_updated`
2. `content_invalidation_required`
3. Stale revision event ignore behavior

### Expected outcomes

1. `incoming_revision == current + 1` follows targeted update behavior.
2. `incoming_revision > current + 1` emits invalidation semantics.
3. `incoming_revision < current` is ignored deterministically.

### Frontend gate

Safe to implement projection cache refresh/invalidation hooks.

## CM-05 Verification: API + WS Envelope Mapping

### Automated checks

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="backend/tests/systems/dnd5e/content/integration/test_api_transport.py backend/tests/systems/dnd5e/content/test_ws_events_contract.py -q" backend-test
```

### Endpoint and WS targets

1. API resolved/denied/error terminal envelope shape
2. WS events carrying request correlation and revision metadata

### Expected outcomes

1. One terminal envelope outcome per command.
2. Denied/error outcomes include explicit reason code.
3. Request correlation and revision metadata are preserved.

### Frontend gate

Safe to implement a unified transport adapter (REST + WS) that keys by request and revision.

## CM-07 Verification: Character Write + Ownership

### Automated checks

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="backend/tests/systems/dnd5e/test_character_write_router.py -q" backend-test
```

### Endpoint smoke targets

1. `POST /api/characters`
2. `PUT /api/characters/{character_id}`

### Expected outcomes

1. Valid create/update returns `status=resolved`.
2. Missing ownership fields deny with stable reason code (for example `MISSING_PLAYER_ID`, `MISSING_CAMPAIGN_ID`).
3. Ownership violations map to deterministic denial reasons and status codes.

### Frontend gate

Safe to wire character create/update form once resolved and denied envelope branches are confirmed.

## CM-08 Verification: Character Sheet Projection

### Automated checks

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="backend/tests/systems/dnd5e/test_character_sheet_projection_router.py -q" backend-test
```

### Endpoint smoke target

1. `GET /api/characters/{character_id}/sheet?catalog_revision=<n>`

### Expected outcomes

1. Resolved path returns `sheet_revision`, `catalog_revision`, `resolution_status=resolved`.
2. Missing references return denied outcomes with unresolved reference IDs.
3. Revision gap produces `status=invalidated` and revision mismatch semantics.
4. Stale revision requests do not regress projection state.

### Frontend gate

Safe to wire character sheet screen with three UI states:

1. Resolved projection view
2. Denied unresolved-reference alert state
3. Invalidated/reload-required state

## CM-06 Verification: Action Integration Smoke (Stretch)

### Current state

1. Ticket exists on board as planned stretch.
2. Dedicated implementation artifact is not yet in active tree.

### Required before frontend action integration sign-off

1. Define minimal action smoke scenario using character sheet outputs.
2. Add focused automated test target.
3. Confirm round-trip payload compatibility with DND5E-03 touchpoint.

## Frontend Milestone Gates (Practical)

1. **Milestone F1 (Compendium UI safe)**
   - Requires CM-01..CM-05 verification evidence.
2. **Milestone F2 (Character write UI safe)**
   - Requires CM-07 verification evidence.
3. **Milestone F3 (Character sheet UI safe)**
   - Requires CM-08 verification evidence.
4. **Milestone F4 (Action integration UI safe)**
   - Requires CM-06 completion.

## Evidence Logging Template

For each verification run, append one line to sprint notes or board notes:

1. Date/time
2. Command used
3. Ticket(s) covered
4. Result (`pass`, `fail`, `blocked`)
5. If failed or blocked: short reason + next action

## Current Known Constraint (2026-04-09)

Containerized test execution is currently blocked on this device due to unavailable Docker engine.
Treat CM-07 and CM-08 as implementation-present and verification-pending until Docker-backed checks run successfully.
