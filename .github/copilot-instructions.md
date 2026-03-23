# Open RPG Engine - Copilot Instructions

You are an expert AI assistant working on the Open RPG Engine.

## Context

This project is a modular Virtual Tabletop (VTT) based on SRD 5.1.
It uses a **Hybrid Architecture** with a Python Backend and React Frontend in a Monorepo.

## Critical Architecture Rules

1.  **Backend is Truth:** Frontend never calculates. It displays state provided by the backend.
2.  **Data-Driven:** Rules are defined in JSON/Database, not hardcoded logic.
3.  **Micro-Frontend Simulation:** The frontend is modular (Host, DM View, Player Sheet).
4.  **Microservice-Ready:** The backend must be loosely coupled. Separate Data Persistence from Business Logic so they can be split into different services later.

## Technology Stack

- **Backend:** Python (FastAPI), Pydantic, PostgreSQL.
- **Frontend:** React, TypeScript, Vite, pnpm workspaces, shadcn/ui.
- **Styling:** Tailwind CSS.
- **Reference:** [libsrd5](https://github.com/kupka/libsrd5) (Use this for SRD data structure logic).

## Future Extensibility (Keep in Mind)

- **Effect Processor:** A future engine component will parse `effects` lists in models. Ensure all models have this field.
- **Modding:**
  - **Frontend:** Style mods via CSS variables/JSON themes.
  - **Backend:** Content mods (JSON) and Logic mods (swappable functions).
  - **Config:** Components should be swappable via configuration.

## Development Guidelines

- When writing Python models, always inherit from `pydantic.BaseModel`.
- When writing React components, assume data comes from props/context (View Model).
- If you change a Backend Model, remind the user to update the Frontend Types.

## MVP Legacy Policy (Strict)

- During MVP, do not preserve legacy behavior unless explicitly requested.
- Prefer removing obsolete code, compatibility layers, and fallback paths over extending them.
- Favor clear structure and direct implementations, even if breaking changes occur.
- Use tests to validate the current direction, not to protect deprecated systems.

### Legacy Debt Capture (Guarded)

- If you encounter unresolved legacy code/debt during a task and do not fix it in the same scope, create a focused issue document in `ISSUES/` at the end of the task.
- Only create the issue when the debt is material (e.g., causes warnings/errors, raises maintenance risk, or blocks near-term refactors). Do not create issues for minor style nits.
- Before creating a new file, check whether an existing issue already tracks the same area and append/expand that issue instead of duplicating.
- Each legacy debt issue must include: affected files/line references, impact/risk, explicit in-scope fix list, out-of-scope notes, and verification commands.
- Keep implementation output quality first: issue capture is a finalization step and must not interrupt primary task delivery.

## Development Workflow

- Prefer container-first development for day-to-day work.
- Use VS Code tasks from `.vscode/tasks.json` with the `Docker:` prefix to start all services or individual services.
- The default full-stack path is Docker Compose (`db`, `redis`, `backend`, `frontend`).
- Existing watch behavior is provided by mounted volumes plus app-level reload (uvicorn `--reload`, Vite HMR).
- `Run Backend (Dev)` is a legacy hybrid fallback for targeted native backend debugging.

### Containerized Backend Test Workflow

- Use the dedicated `backend-test` Compose service for backend test execution.
- Preferred test command: `docker compose --profile test run --rm backend-test`.
- Optional environment switches:
  - `RUN_BACKEND_TESTS=true|false` to run or skip tests in that one-shot service.
  - `PYTEST_ARGS="tests -q"` (or any targeted subset) to control what pytest runs.
- Keep normal `backend` service startup focused on app runtime; do not couple backend boot to full pytest execution.

## Agent Verification and Restart Rules

- After implementing code changes, verify behavior using Docker logs before declaring success.
- For backend changes, check backend logs (`Docker: Logs (Backend)`), and restart backend if needed.
- For frontend changes, check frontend logs (`Docker: Logs (Frontend)`), and restart frontend if needed.
- If dependencies, Dockerfiles, or compose configuration changed, rebuild and restart affected services.
- Prefer targeted restarts of changed services instead of restarting the whole stack.

## Python Environment Awareness

- Container-first remains the default path for Python work.
- If a task or workflow runs Python natively (outside containers), use the backend virtual environment at `backend/.venv`.
- For native backend debugging, use the existing `Run Backend (Dev)` task, which manages the venv workflow.

## Project Structure

- `backend/src/models`: The Source of Truth for data structures.
- `frontend/packages/types`: TypeScript definitions synced with backend models.
