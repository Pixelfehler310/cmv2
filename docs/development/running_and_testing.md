# Running and Testing Guide

This guide is the authoritative day-to-day reference for running and validating CMV2.

It covers:

- Docker-first development workflow (recommended)
- Native fallback workflows
- Backend test suites (including integration tests)
- Frontend lint and tests
- Common failure modes and fixes

## 1. Prerequisites

## Required tools

- Docker Desktop (with Compose)
- Node.js 18+
- pnpm 8+
- Python 3.11+ (for native backend fallback)

## Workspace

Open the `cmv2` repo root in VS Code.

## Ports

- Frontend: `http://localhost:3020`
- Backend API: `http://localhost:8020`
- PostgreSQL: `localhost:5450`
- Redis: `localhost:6400`

## 2. Preferred Workflow: Docker-First

Use VS Code tasks from `.vscode/tasks.json` where possible.

## Start stack

- `Docker: Up All (Detached)`
- or `Docker: Up All (Foreground)`

Equivalent terminal command:

```bash
docker compose up -d
```

## Start only infrastructure

- `Docker: Up Infra (db + redis)`

Equivalent:

```bash
docker compose up db redis
```

## Stop stack

- `Docker: Down`

Equivalent:

```bash
docker compose down
```

## Logs

- `Docker: Logs (Backend)`
- `Docker: Logs (Frontend)`
- `Docker: Logs (All)`

Equivalent:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f
```

## Restart only changed service

- `Docker: Restart Backend`
- `Docker: Restart Frontend`

Equivalent:

```bash
docker compose restart backend
docker compose restart frontend
```

## 3. Backend: Running and Testing

## Test dependencies

Backend tests rely on test packages declared in `backend/requirements.txt`, including:

- `pytest`
- `pytest-asyncio`
- `aiosqlite`

If dependencies changed, rebuild or reinstall before testing.

## Full backend suite

From repo root:

```bash
docker compose --profile test run --rm backend-test
```

This runs tests in the dedicated backend test container instead of coupling test execution to the long-running app container.

## Integration tests (explicit)

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="tests/systems/dnd5e/integration -q" backend-test
```

This explicit run is useful even if included in the full suite, because it isolates system-level WS/combat failures quickly.

## Useful targeted backend runs

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="tests/systems/dnd5e/test_ws_integration.py -q" backend-test
docker compose --profile test run --rm -e PYTEST_ARGS="tests/systems/dnd5e/integration/test_ws_server_client.py -q" backend-test
docker compose --profile test run --rm -e PYTEST_ARGS="tests/systems/dnd5e/test_combat_service.py -q" backend-test
```

## Optional backend-test toggles

```bash
RUN_BACKEND_TESTS=false docker compose --profile test run --rm backend-test
PYTEST_ARGS="tests/test_loader.py tests/systems/dnd5e/test_content_pack_importer.py -q" docker compose --profile test run --rm backend-test
```

## Why pytest config matters

`backend/pytest.ini` is configured to keep collection deterministic:

- `testpaths = tests`
- `addopts = --import-mode=importlib`

This prevents import-name collisions between helper scripts and test modules.

## Native backend fallback (targeted debugging)

If you need local Python debugging outside Docker:

1. Use the `Run Backend (Dev)` task.
2. Or activate `backend/.venv` and run from `backend` directory.

Example:

```bash
cd backend
python -m venv .venv
# activate .venv for your shell
pip install -r requirements.txt
pytest -q
```

Note: native backend still expects Postgres/Redis unless tests mock dependencies.

## 4. Frontend: Running, Linting, Testing

Run frontend commands from `frontend` directory.

## Install workspace dependencies

```bash
pnpm install
```

## Dev mode

```bash
pnpm dev
```

## Build workspace

```bash
pnpm build
```

## Lint workspace

```bash
pnpm lint
```

Current lint strategy is TypeScript validation (`tsc --noEmit`) per package.

## Test workspace

```bash
pnpm test
```

Current test coverage is present in `@rpg/management-view` (Vitest). Root test command uses workspace recursion with `--if-present`.

## Useful targeted frontend runs

```bash
pnpm --filter @rpg/management-view lint
pnpm --filter @rpg/management-view test
pnpm --filter @rpg/host build
pnpm --filter @rpg/dm-view lint
```

## 5. Validation Checklist for Changes

After backend code changes:

1. Run backend targeted tests for touched area.
2. Run full backend suite.
3. Run explicit integration subset (`tests/systems/dnd5e/integration`).
4. Check backend logs.

After frontend code changes:

1. Run package-specific lint/test/build for touched packages.
2. Run workspace `pnpm lint` and `pnpm test`.
3. Check frontend logs and browser behavior.

After dependency or compose changes:

1. Rebuild affected images.
2. Restart affected services.
3. Re-run both backend and frontend validation.

## 6. Common Issues and Fixes

## Backend: `pytest: not found`

Cause: stale image cache, or running tests in the wrong container.

Fix:

```bash
docker compose build --no-cache backend-test
```

Then run tests through the test service:

```bash
docker compose --profile test run --rm backend-test
```

## Backend: `ModuleNotFoundError: src` during pytest

Cause: direct ad-hoc pytest invocation from an incorrect path.

Fix: use the dedicated test service command, which is already configured to run from the correct working directory:

```bash
docker compose --profile test run --rm backend-test
```

## Backend: flaky WS turn assertions

Cause: initiative order can change active actor.

Fix: use current active actor from `combat_started` payload, not hardcoded actor IDs.

## Frontend: workspace lint/test stops on missing scripts

Cause: recursive workspace command without `--if-present`.

Fix: keep root scripts as:

- `pnpm -r --if-present lint`
- `pnpm -r --if-present test`

## Frontend: bridge `import.meta.env` type errors in consuming packages

Cause: consuming package TS config may not include Vite env types.

Fix: in shared bridge code, use defensive `import.meta` env access and default to `"/api"`.

## Frontend: management-view Vitest worker ESM bootstrap errors

Cause: test environment incompatibility in local setup.

Fix: use `happy-dom` in `vitest.config.ts` and ensure dependency is installed.

## Frontend: DM view Tailwind variable syntax warnings

Cause: outdated variable syntax.

Fix: use modern utility form (for example `border-(--border-default)`).

## 7. Suggested CI Baseline

Use this sequence in CI for broad confidence:

1. Backend full tests.
2. Backend integration subset.
3. Frontend install.
4. Frontend lint.
5. Frontend test.
6. Frontend build.

Example pseudo-pipeline:

```bash
# backend
docker compose up -d db redis backend
docker compose --profile test run --rm backend-test
docker compose --profile test run --rm -e PYTEST_ARGS="tests/systems/dnd5e/integration -q" backend-test

# frontend
cd frontend
pnpm install
pnpm lint
pnpm test
pnpm build
```

## 8. Quick Commands Cheat Sheet

```bash
# Start stack
docker compose up -d

# Backend full + integration
docker compose exec backend sh -lc "cd /app && pytest -q"
docker compose exec backend sh -lc "cd /app && pytest -q tests/systems/dnd5e/integration"

# Frontend checks
cd frontend
pnpm install
pnpm lint
pnpm test
pnpm build

# Logs
docker compose logs -f backend
docker compose logs -f frontend
```

## 9. Current Baseline Notes (March 2026)

These notes capture the currently expected baseline from local verification.

- Backend full suite: `631 passed`, with a remaining upstream warning from passlib/crypt.
- Backend integration subset (`tests/systems/dnd5e/integration`): passing.
- Frontend workspace lint: passing.
- Frontend workspace tests: passing (`@rpg/management-view` currently provides test coverage).

If results differ from this baseline, check dependency drift first (`pip install -r requirements.txt` in backend container and `pnpm install` in frontend workspace), then rerun the exact commands from Sections 3 and 4.
