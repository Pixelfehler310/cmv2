from src.schemas.spell import SpellCreate, SpellResponse
from src.schemas.monster import MonsterCreate, MonsterResponse
from src.schemas.item import ItemCreate, ItemResponse
from src.schemas.definitions import BackgroundResponse, ClassResponse, SpeciesResponse
from src.schemas.character import CharacterCreate, CharacterResponse
from src.schemas.campaign import CampaignCreate, CampaignResponse
from src.schemas.context import (
    CampaignContextResponse,
    EncounterOptionResponse,
    SceneOptionResponse,
    SelectCampaignContextRequest,
)
import argparse
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pydantic import BaseModel

# Add backend to path to allow imports
BACKEND_DIR = Path(__file__).parent.parent
sys.path.append(str(BACKEND_DIR))


OUTPUT_SCHEMA = BACKEND_DIR / "schema.json"


def _resolve_frontend_types_dir() -> Path:
    configured = os.getenv("FRONTEND_TYPES_DIR")
    if configured:
        return Path(configured)

    local_repo = BACKEND_DIR.parent / "frontend/packages/types"
    if local_repo.exists():
        return local_repo

    mounted_workspace = Path("/workspace/frontend/packages/types")
    if mounted_workspace.exists():
        return mounted_workspace

    return local_repo


FRONTEND_TYPES_DIR = _resolve_frontend_types_dir()
OUTPUT_TS = FRONTEND_TYPES_DIR / "src/generated.ts"


class ExportModel(BaseModel):
    items: list[ItemResponse]
    item_create: list[ItemCreate]
    spells: list[SpellResponse]
    spell_create: list[SpellCreate]
    monsters: list[MonsterResponse]
    monster_create: list[MonsterCreate]
    campaigns: list[CampaignResponse]
    campaign_create: list[CampaignCreate]
    characters: list[CharacterResponse]
    character_create: list[CharacterCreate]
    campaign_context: list[CampaignContextResponse]
    scene_options: list[SceneOptionResponse]
    encounter_options: list[EncounterOptionResponse]
    select_campaign_context_request: list[SelectCampaignContextRequest]
    species: list[SpeciesResponse]
    classes: list[ClassResponse]
    backgrounds: list[BackgroundResponse]


def build_json_schema() -> dict:
    return ExportModel.model_json_schema()


def write_json_schema(path: Path, schema: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2,
                    sort_keys=True) + "\n", encoding="utf-8")


def resolve_json2ts_command() -> list[str]:
    direct = shutil.which("json2ts")
    if direct:
        return [direct]

    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if npx:
        # Pinning package version keeps generation stable in CI and local runs.
        return [npx, "--yes", "json-schema-to-typescript@13.1.1"]

    raise RuntimeError(
        "Could not find 'json2ts' or 'npx' in PATH. Install Node.js and json-schema-to-typescript."
    )


def generate_ts(schema_path: Path, output_ts_path: Path) -> None:
    output_ts_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        *resolve_json2ts_command(),
        "-i",
        str(schema_path),
        "-o",
        str(output_ts_path),
        "--unreachableDefinitions",
    ]

    subprocess.run(cmd, check=True, cwd=FRONTEND_TYPES_DIR)


def _unified_diff(expected: str, actual: str, from_name: str, to_name: str) -> str:
    diff = difflib.unified_diff(
        expected.splitlines(),
        actual.splitlines(),
        fromfile=from_name,
        tofile=to_name,
        lineterm="",
    )
    lines = list(diff)
    if not lines:
        return ""
    return "\n".join(lines[:120])


def _read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def check_for_drift() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        tmp_schema = tmp_dir / "schema.json"
        tmp_ts = tmp_dir / "generated.ts"

        write_json_schema(tmp_schema, build_json_schema())
        generate_ts(tmp_schema, tmp_ts)

        expected_schema = _read_file(tmp_schema)
        actual_schema = _read_file(OUTPUT_SCHEMA)
        expected_ts = _read_file(tmp_ts)
        actual_ts = _read_file(OUTPUT_TS)

        schema_diff = _unified_diff(actual_schema, expected_schema, str(
            OUTPUT_SCHEMA), "expected/schema.json")
        ts_diff = _unified_diff(actual_ts, expected_ts, str(
            OUTPUT_TS), "expected/generated.ts")

        has_drift = bool(schema_diff or ts_diff)
        if not has_drift:
            print("Contract artifacts are in sync.")
            return 0

        print("Contract drift detected. Regenerate artifacts before committing.")
        if schema_diff:
            print("\nSchema drift (preview):")
            print(schema_diff)
        if ts_diff:
            print("\nTypeScript drift (preview):")
            print(ts_diff)
        print("\nRun: python backend/scripts/generate_types.py")
        return 1


def write_outputs() -> int:
    write_json_schema(OUTPUT_SCHEMA, build_json_schema())
    print(f"JSON schema generated at {OUTPUT_SCHEMA}")
    generate_ts(OUTPUT_SCHEMA, OUTPUT_TS)
    print(f"TypeScript contracts generated at {OUTPUT_TS}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify backend-to-frontend contract artifacts."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when generated artifacts drift from current source models.",
    )
    args = parser.parse_args()

    try:
        if args.check:
            return check_for_drift()
        return write_outputs()
    except subprocess.CalledProcessError as exc:
        print(f"Contract generation command failed: {exc}")
        return 1
    except RuntimeError as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
