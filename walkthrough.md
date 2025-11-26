# Walkthrough - Milestone 1.2 Verification

## Changes
- Implemented SQLAlchemy models for `Item`, `Spell`, `Monster`.
- Implemented Pydantic schemas for `Item`, `Spell`, `Monster`.
- Created `JSON Loader Service` to import data from JSON files.
- Created API endpoints for Items, Spells, and Monsters.
- Added `pytest-asyncio` to `requirements.txt` and configured `pytest.ini`.

## Verification Results

### Automated Tests
Ran `pytest` to verify models, schemas, loader service, and API endpoints.

```bash
python -m pytest
```

**Output:**
```
========================== test session starts ==========================
platform win32 -- Python 3.12.5, pytest-9.0.1, pluggy-1.6.0
rootdir: C:\Users\simon\Documents\GitHub\cmv2\backend
configfile: pytest.ini
plugins: anyio-4.11.0, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 11 items

tests\test_config.py .                                             [  9%] 
tests\test_loader.py ..                                            [ 27%] 
tests\test_main.py ..                                              [ 45%]
tests\test_routers.py ...                                          [ 72%]
tests\test_schemas.py ...                                          [100%] 

========================== 11 passed in 0.12s ===========================
```

### Manual Verification
- Verified `Monster` model includes `effects` field.
- Verified API endpoints return correct data structure (via tests).
