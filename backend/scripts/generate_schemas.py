from models.base import GameEntity, EffectConfig
from pydantic import BaseModel
import json
import sys
from pathlib import Path
from typing import List, Type

# Add src to path so we can import models
sys.path.append(str(Path(__file__).parent.parent / "src"))


def generate_schemas():
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
    models: List[Type[BaseModel]] = [
        GameEntity,
        EffectConfig
    ]

    print(f"Generating schemas for {len(models)} models...")

    for model in models:
        schema = model.model_json_schema()
        file_name = f"{model.__name__}.json"
        output_file = output_dir / file_name

        with open(output_file, "w") as f:
            json.dump(schema, f, indent=2)

        print(f" - Generated {file_name}")

    print(f"Done. Schemas saved to {output_dir}")


if __name__ == "__main__":
    generate_schemas()
