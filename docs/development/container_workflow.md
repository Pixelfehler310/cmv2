# Container-First Development Workflow

This project is developed primarily inside Docker containers.

For complete run and test procedures (backend + frontend + troubleshooting), see `docs/development/running_and_testing.md`.

## Quick Start (VS Code)

Run one of the following tasks from "Tasks: Run Task":

- Docker: Up All (Foreground)
- Docker: Up All (Detached)
- Docker: Up Infra (db + redis)
- Docker: Up Backend
- Docker: Up Frontend
- Docker: Down

## Backend Tests in Containers

Use the dedicated one-shot test service:

```bash
docker compose --profile test run --rm backend-test
```

For targeted runs:

```bash
docker compose --profile test run --rm -e PYTEST_ARGS="tests/systems/dnd5e/integration -q" backend-test
```

## Logs

Use these tasks when you need log tails:

- Docker: Logs (All)
- Docker: Logs (Backend)
- Docker: Logs (Frontend)

When validating code changes, check the relevant logs before concluding work is complete.

- Backend changes: verify with backend logs.
- Frontend changes: verify with frontend logs.

## Ports

- Frontend: http://localhost:3020
- Backend API: http://localhost:8020
- PostgreSQL: localhost:5450
- Redis: localhost:6400

## Watch and Reload

No extra Docker watch feature is required for day-to-day development in this repo.

- Backend reload is handled by uvicorn `--reload`.
- Frontend reload is handled by Vite HMR.
- Source code is mounted via Docker volumes.

## Restart Guidance

Restart only the changed service whenever possible.

- Backend-only changes: restart backend.
- Frontend-only changes: restart frontend.
- Compose or image/dependency changes: rebuild and restart affected services.

## Legacy Hybrid Flow

The task `Run Backend (Dev)` remains available for the hybrid workflow (local Python backend, Docker infra).

If running Python outside Docker, use `backend/.venv`.

Prefer Docker tasks above unless you are doing targeted native backend debugging.
