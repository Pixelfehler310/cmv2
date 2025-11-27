import json
import sys
import os
import subprocess
from pathlib import Path

# Add backend to path to allow imports
BACKEND_DIR = Path(__file__).parent.parent
sys.path.append(str(BACKEND_DIR))

from src.schemas.item import ItemResponse, ItemCreate
from src.schemas.spell import SpellResponse, SpellCreate
from src.schemas.monster import MonsterResponse, MonsterCreate
from src.schemas.campaign import CampaignResponse, CampaignCreate
from src.schemas.character import CharacterResponse, CharacterCreate
from src.schemas.definitions import SpeciesResponse, ClassResponse, BackgroundResponse
# Import other schemas as needed

OUTPUT_SCHEMA = BACKEND_DIR / "schema.json"
OUTPUT_TS = BACKEND_DIR.parent / "frontend/packages/types/src/generated.ts"

def generate_json_schema():
    """
    Generates a combined JSON schema for all relevant models.
    """
    # We can use Pydantic's TypeAdapter to generate a schema for a Union of all types
    # or just generate individual definitions.
    # A clean way is to create a dummy model that holds everything we want to export.
    from pydantic import BaseModel
    from typing import List, Optional

    class ExportModel(BaseModel):
        items: List[ItemResponse]
        spells: List[SpellResponse]
        monsters: List[MonsterResponse]
        campaigns: List[CampaignResponse]
        characters: List[CharacterResponse]
        species: List[SpeciesResponse]
        classes: List[ClassResponse]
        backgrounds: List[BackgroundResponse]
        # Add others...

    schema = ExportModel.model_json_schema()
    
    # We want to export the 'definitions' (or '$defs' in Pydantic V2) as top-level types
    # json-schema-to-typescript handles this well if we pass the whole schema.
    
    with open(OUTPUT_SCHEMA, "w") as f:
        json.dump(schema, f, indent=2)
    
    print(f"JSON Schema generated at {OUTPUT_SCHEMA}")

def generate_ts():
    """
    Runs json-schema-to-typescript.
    """
    # We use npx to run the local package
    # --unreachableDefinitions: generate types even if not referenced in root
    cmd = [
        "npx.cmd", "json2ts", # Windows might need npx.cmd
        "-i", str(OUTPUT_SCHEMA),
        "-o", str(OUTPUT_TS),
        "--unreachableDefinitions" 
    ]
    
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, shell=True, cwd=BACKEND_DIR.parent / "frontend/packages/types")
        print(f"TypeScript types generated at {OUTPUT_TS}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating TS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_json_schema()
    generate_ts()
