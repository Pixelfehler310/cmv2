import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.ws_handler import set_encounter
from src.database import get_db
from src.data.lib.loader import DataLoader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dev", tags=["dev"])

FIXTURES_DIR = Path(__file__).parent.parent.parent / "data" / "fixtures"
ENCOUNTERS_DIR = FIXTURES_DIR / "encounters"


@router.post("/load-seeds")
async def load_seeds(session: AsyncSession = Depends(get_db)):
    """Load all JSON database seeds and memory encounters."""
    logger.info("POST /api/dev/load-seeds called. fixtures_dir=%s encounters_dir=%s",
                FIXTURES_DIR, ENCOUNTERS_DIR)
    if not FIXTURES_DIR.exists():
        logger.error(f"Fixtures directory not found at {FIXTURES_DIR}")
        raise HTTPException(
            status_code=404, detail="Fixtures directory not found")

    summary = {
        "db_seeds_loaded": True,
        "db_import_summary": {},
        "encounters_total": 0,
        "encounters_loaded": 0,
        "encounters_failed": 0
    }

    # 1. Load Postgres Database Seeds (Campaigns, Characters, Definitions, Items, Spells, Monsters)
    loader = DataLoader(str(FIXTURES_DIR))
    try:
        summary["db_import_summary"] = await loader.load_all(session)
    except Exception as e:
        logger.error(f"Failed to load DB seeds: {e}")
        summary["db_seeds_loaded"] = False

    # 2. Load In-Memory Encounters
    loaded_files = []
    errors = {}

    if ENCOUNTERS_DIR.exists():
        encounter_files = sorted(ENCOUNTERS_DIR.glob("*.json"))
        logger.info("Found %s encounter fixture file(s).",
                    len(encounter_files))
        for file_path in encounter_files:
            summary["encounters_total"] += 1
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                encounter = EncounterState.model_validate(data)
                set_encounter(encounter.campaign_id, encounter)

                summary["encounters_loaded"] += 1
                loaded_files.append(file_path.name)
                logger.info("Loaded encounter fixture: %s (campaign_id=%s)",
                            file_path.name, encounter.campaign_id)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON in {file_path.name}: {e}")
                summary["encounters_failed"] += 1
                errors[file_path.name] = f"JSON Decode Error: {e}"
            except ValidationError as e:
                logger.error(f"Validation Error for {file_path.name}: {e}")
                summary["encounters_failed"] += 1
                errors[file_path.name] = f"Validation Error: {e.errors()[0]['type']} - {e.errors()[0]['loc']}"
            except Exception as e:
                logger.exception(f"Unexpected error loading {file_path.name}")
                summary["encounters_failed"] += 1
                errors[file_path.name] = f"Unexpected error: {str(e)}"
    else:
        logger.warning(
            "Encounters directory does not exist: %s", ENCOUNTERS_DIR)

    status = "success"
    if summary["encounters_loaded"] == 0 and summary["encounters_total"] > 0:
        status = "failed"
    elif summary["encounters_failed"] > 0 or not summary["db_seeds_loaded"]:
        status = "partial_success"

    logger.info("Seed load finished with status=%s summary=%s",
                status, summary)

    return {
        "status": status,
        "summary": summary,
        "encounters_loaded_files": loaded_files,
        "errors": errors
    }
