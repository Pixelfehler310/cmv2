from schemas.base import EffectConfig, GameEntity
import argparse
import json
import sys
from pathlib import Path
from typing import List, Type

from pydantic import BaseModel

# Add src to path so we can import models
sys.path.append(str(Path(__file__).parent.parent / "src"))


def _build_models() -> List[Type[BaseModel]]:
    return [
        GameEntity,
        EffectConfig,
    ]


def generate_schemas() -> None:
    # Define the output directory
    output_dir = Path(__file__).parent.parent.parent / \
        "frontend" / "packages" / "types" / "schemas"

    # Ensure directory exists and clean it
    if output_dir.exists():
        for file in output_dir.glob("*.json"):
            file.unlink()
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    # List of models to export
    models = _build_models()

    print(f"Generating schemas for {len(models)} models...")

    for model in models:
        schema = model.model_json_schema()
        file_name = f"{model.__name__}.json"
        output_file = output_dir / file_name

        output_file.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        print(f" - Generated {file_name}")

    print(f"Done. Schemas saved to {output_dir}")


def check_schemas() -> int:
    output_dir = Path(__file__).parent.parent.parent / \
        "frontend" / "packages" / "types" / "schemas"
    for model in _build_models():
        file_name = f"{model.__name__}.json"
        output_file = output_dir / file_name
        expected = json.dumps(model.model_json_schema(),
                              indent=2, sort_keys=True) + "\n"
        if not output_file.exists():
            print(f"Missing schema file: {output_file}")
            return 1
        actual = output_file.read_text(encoding="utf-8")
        if actual != expected:
            print(
                f"Schema drift detected for {file_name}. Run: python backend/scripts/generate_schemas.py")
            return 1

    print("Individual schema files are in sync.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or verify individual JSON schemas.")
    parser.add_argument("--check", action="store_true",
                        help="Exit non-zero if schema files are stale.")
    args = parser.parse_args()

    if args.check:
        raise SystemExit(check_schemas())

    generate_schemas()
