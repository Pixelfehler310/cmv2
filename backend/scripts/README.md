# Type Generation Scripts

This directory contains scripts that lock the contract chain:

- Backend schema models (`backend/src/schemas`) ->
- Generated JSON schema (`backend/schema.json`) ->
- Generated frontend TypeScript contracts (`frontend/packages/types/src/generated.ts`).

## Canonical Commands

Generate/update canonical contract artifacts:

```bash
python backend/scripts/generate_types.py
```

Verify contract artifacts are in sync (non-zero exit on drift):

```bash
python backend/scripts/generate_types.py --check
```

Optional helper for individual JSON files in `frontend/packages/types/schemas/`:

```bash
python backend/scripts/generate_schemas.py
python backend/scripts/generate_schemas.py --check
```

## Workflow

Whenever you modify backend schema contracts in `backend/src/schemas/`:

1. Run `python backend/scripts/generate_types.py`.
2. Commit both generated artifacts (`backend/schema.json`, `frontend/packages/types/src/generated.ts`).
3. Ensure `python backend/scripts/generate_types.py --check` passes.

## CI/Test Gate

`backend-test` runs `python scripts/generate_types.py --check` before pytest by default.
Disable only when intentionally debugging unrelated failures:

```bash
RUN_CONTRACT_CHECKS=false docker compose --profile test run --rm backend-test
```

## Data Backfill Utilities

Backfill legacy monster action payloads to strict canonical `action_id` refs:

```bash
# From backend/ directory (dry-run by default)
python scripts/backfill_monster_action_refs.py

# Persist updates
python scripts/backfill_monster_action_refs.py --apply
```
