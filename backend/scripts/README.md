# Type Generation Scripts

This directory contains scripts to synchronize Backend Pydantic models with Frontend TypeScript interfaces.

## Usage

1.  **Generate JSON Schemas**:
    Run the Python script to export Pydantic models as JSON Schema files to `frontend/packages/types/schemas/`.

    ```bash
    # From backend/ directory
    python scripts/generate_schemas.py
    ```

2.  **Generate TypeScript Interfaces**:
    Run the npm script in the frontend types package to convert JSON Schemas to `index.ts`.
    ```bash
    # From frontend/packages/types/ directory
    pnpm generate
    ```

## Workflow

Whenever you modify a Pydantic model in `backend/src/models/`:

1.  Run `python backend/scripts/generate_schemas.py`
2.  Run `pnpm --filter @rpg/types generate`

## Data Backfill Utilities

Backfill legacy monster action payloads to strict canonical `action_id` refs:

```bash
# From backend/ directory (dry-run by default)
python scripts/backfill_monster_action_refs.py

# Persist updates
python scripts/backfill_monster_action_refs.py --apply
```
