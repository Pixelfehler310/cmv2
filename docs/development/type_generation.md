# Type Generator Workflow

## Overview
We use an automated script to generate TypeScript interfaces from our Backend Pydantic models. This ensures the Frontend (`@rpg/types`) is always in sync with the Backend.

## How to Run

### Command
From the root of the repository:

```bash
python backend/scripts/generate_types.py
```

### Prerequisites
- Python environment active.
- Dependencies installed (`pip install -r backend/requirements.txt`).
- Node.js environment (for `json-schema-to-typescript`).

## Workflow FAQ

### Does it run automatically?
**No.** Currently, you must run the script manually. You should run it after the backend models have been modified.

### Should it run automatically?
**Recommendation: Manual (for now).**

- **Why?** Running it automatically on every file save can trigger frequent, unnecessary frontend rebuilds/reloads if you are just experimenting with backend code.
- **Best Practice:** Run the generator when you have **finished** modifying your Pydantic models and are ready to work on the frontend.
- **Future:** We can add this to a `pre-commit` hook to ensure you never commit mismatched types. (not recommended)
