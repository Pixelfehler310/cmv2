# Open RPG Engine - Copilot Instructions

You are an expert AI assistant working on the Open RPG Engine.

## Context

This project is a modular Virtual Tabletop (VTT) based on SRD 5.1.
It uses a **Hybrid Architecture** with a Python Backend and React Frontend in a Monorepo.

## Critical Architecture Rules

1.  **Backend is Truth:** Frontend never calculates. It displays state provided by the backend.
2.  **Data-Driven:** Rules are defined in JSON/Database, not hardcoded logic.
3.  **Micro-Frontend Simulation:** The frontend is modular (Host, DM View, Player Sheet).

## Technology Stack

- **Backend:** Python (FastAPI), Pydantic, PostgreSQL.
- **Frontend:** React, TypeScript, Vite, pnpm workspaces, shadcn/ui.
- **Styling:** Tailwind CSS.

## Development Guidelines

- When writing Python models, always inherit from `pydantic.BaseModel`.
- When writing React components, assume data comes from props/context (View Model).
- If you change a Backend Model, remind the user to update the Frontend Types.

## Project Structure

- `backend/src/models`: The Source of Truth for data structures.
- `frontend/packages/types`: TypeScript definitions synced with backend models.
