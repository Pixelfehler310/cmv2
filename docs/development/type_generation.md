# Type Generator Workflow

## Overview

We use a contract-first generation flow to keep Frontend types in sync with Backend schema models:

- Backend schema models (`backend/src/schemas/`) ->
- Generated JSON schema (`backend/schema.json`) ->
- Generated frontend contracts (`frontend/packages/types/src/generated.ts`).

The single source of truth is backend schema models.

## How to Run

### Generate Artifacts

From the root of the repository:

```bash
python backend/scripts/generate_types.py
```

### Verify No Drift (Fail on Mismatch)

```bash
python backend/scripts/generate_types.py --check
```

### Prerequisites

- Python environment active.
- Dependencies installed (`pip install -r backend/requirements.txt`).
- Node.js available in PATH and `json-schema-to-typescript` accessible (`json2ts` or `npx`).

## Workflow FAQ

### Does it run automatically?

**In tests/CI: yes.** The `backend-test` Docker profile runs `python scripts/generate_types.py --check` before pytest and fails fast on drift.

**In local editing flow: manual regenerate is still expected** after schema model changes.

### Should it run automatically?

**Recommendation: Keep generation manual, keep verification automatic in test/CI.**

- **Why?** Auto-generation on each save creates noisy rebuild churn during exploratory backend work.
- **Best Practice:** Regenerate when schema edits are complete, then rely on check mode to prevent drift from reaching CI.
