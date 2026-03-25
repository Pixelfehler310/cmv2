from src.schemas.campaign import CampaignCreate
from src.schemas.character import CharacterCreate
from src.schemas.definitions import BackgroundBase, ClassBase, SpeciesBase
from src.schemas.feature import FeatBase, FeatureBase
from src.schemas.item import ItemCreate
from src.schemas.monster import MonsterCreate
from src.schemas.spell import SpellCreate
from src.systems.dnd5e.schemas.contracts import ContentPack
from src.systems.dnd5e.schemas.encounter import EncounterState
import json
import sys
from pathlib import Path
from typing import Type

from pydantic import BaseModel, ValidationError

# Add backend root so script can import src.* modules when run from repo root.
BACKEND_DIR = Path(__file__).parent.parent
sys.path.append(str(BACKEND_DIR))


FIXTURES_DIR = BACKEND_DIR / "data" / "fixtures"

DIRECTORY_MODELS: dict[str, Type[BaseModel]] = {
    "items": ItemCreate,
    "spells": SpellCreate,
    "monsters": MonsterCreate,
    "campaigns": CampaignCreate,
    "characters": CharacterCreate,
    "encounters": EncounterState,
    "content_packs": ContentPack,
}

# EncounterState currently uses enum-like runtime types that are serialized as
# strings in JSON fixtures. Keep strict validation for other fixture groups.
DIRECTORY_STRICT_MODE: dict[str, bool] = {
    "items": True,
    "spells": True,
    "monsters": True,
    "campaigns": True,
    "characters": True,
    "encounters": False,
    "content_packs": True,
}

DEFINITION_PREFIX_MODELS: dict[str, Type[BaseModel]] = {
    "species_": SpeciesBase,
    "class_": ClassBase,
    "background_": BackgroundBase,
    "feat_": FeatBase,
    "feature_": FeatureBase,
}


def _load_json_object(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON decode error (line {exc.lineno}, col {exc.colno}): {exc.msg}"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            f"Expected top-level JSON object, got {type(payload).__name__}")

    return payload


def _roundtrip_validate(model: Type[BaseModel], payload: dict, *, strict: bool) -> None:
    validated = model.model_validate(payload, strict=strict)
    dumped = validated.model_dump(mode="json")

    if not isinstance(dumped, dict):
        raise ValueError(
            f"Roundtrip dump produced non-object: {type(dumped).__name__}")

    model.model_validate(dumped, strict=strict)


def _iter_json_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def _validate_mapped_directory(name: str, model: Type[BaseModel]) -> tuple[int, list[str]]:
    directory = FIXTURES_DIR / name
    if not directory.exists() or not directory.is_dir():
        return 0, [f"{name}: directory not found ({directory})"]

    validated_count = 0
    failures: list[str] = []
    strict_mode = DIRECTORY_STRICT_MODE.get(name, True)

    for path in _iter_json_files(directory):
        try:
            payload = _load_json_object(path)
            _roundtrip_validate(model, payload, strict=strict_mode)
            validated_count += 1
        except (ValueError, ValidationError) as exc:
            failures.append(f"{path.relative_to(BACKEND_DIR)}: {exc}")

    return validated_count, failures


def _resolve_definition_model(path: Path) -> Type[BaseModel]:
    file_name = path.name
    for prefix, model in DEFINITION_PREFIX_MODELS.items():
        if file_name.startswith(prefix):
            return model

    allowed = ", ".join(sorted(DEFINITION_PREFIX_MODELS.keys()))
    raise ValueError(
        f"Unknown definition prefix for '{file_name}'. Allowed prefixes: {allowed}")


def _validate_definitions_directory() -> tuple[int, list[str]]:
    directory = FIXTURES_DIR / "definitions"
    if not directory.exists() or not directory.is_dir():
        return 0, [f"definitions: directory not found ({directory})"]

    validated_count = 0
    failures: list[str] = []

    for path in _iter_json_files(directory):
        try:
            model = _resolve_definition_model(path)
            payload = _load_json_object(path)
            _roundtrip_validate(model, payload, strict=True)
            validated_count += 1
        except (ValueError, ValidationError) as exc:
            failures.append(f"{path.relative_to(BACKEND_DIR)}: {exc}")

    return validated_count, failures


def main() -> int:
    validated_total = 0
    failures: list[str] = []

    for name, model in DIRECTORY_MODELS.items():
        validated_count, directory_failures = _validate_mapped_directory(
            name, model)
        validated_total += validated_count
        failures.extend(directory_failures)

    validated_defs, definition_failures = _validate_definitions_directory()
    validated_total += validated_defs
    failures.extend(definition_failures)

    if failures:
        print(
            f"Fixture JSON validation failed: {len(failures)} error(s), {validated_total} file(s) validated."
        )
        for failure in failures:
            print(f" - {failure}")
        return 1

    print(
        f"Fixture JSON validation passed: {validated_total} file(s) validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
