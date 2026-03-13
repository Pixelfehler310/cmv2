import json
import pytest
from pathlib import Path

from src.schemas.item import ItemCreate
from src.schemas.spell import SpellCreate
from src.schemas.monster import MonsterCreate
from src.schemas.definitions import SpeciesBase, ClassBase, BackgroundBase
from src.schemas.feature import FeatBase, FeatureBase
from src.schemas.campaign import CampaignCreate
from src.schemas.character import CharacterCreate
from src.systems.dnd5e.schemas.encounter import EncounterState

FIXTURES_DIR = Path(__file__).parent.parent / "data" / "fixtures"

MIN_FIXTURE_COUNTS = {
    "items": 50,
    "spells": 35,
    "monsters": 25,
    "campaigns": 5,
    "characters": 12,
    "encounters": 10,
    "definitions": 30,
}


def get_json_files(sub_dir: str):
    dir_path = FIXTURES_DIR / sub_dir
    if not dir_path.exists():
        return []
    return list(dir_path.glob("*.json"))


def load_json(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("file_path", get_json_files("items"))
def test_valid_item_fixtures(file_path):
    data = load_json(file_path)
    ItemCreate.model_validate(data)


@pytest.mark.parametrize("file_path", get_json_files("spells"))
def test_valid_spell_fixtures(file_path):
    data = load_json(file_path)
    SpellCreate.model_validate(data)


@pytest.mark.parametrize("file_path", get_json_files("monsters"))
def test_valid_monster_fixtures(file_path):
    data = load_json(file_path)
    MonsterCreate.model_validate(data)


@pytest.mark.parametrize("file_path", get_json_files("campaigns"))
def test_valid_campaign_fixtures(file_path):
    data = load_json(file_path)
    CampaignCreate.model_validate(data)


@pytest.mark.parametrize("file_path", get_json_files("characters"))
def test_valid_character_fixtures(file_path):
    data = load_json(file_path)
    CharacterCreate.model_validate(data)


@pytest.mark.parametrize("file_path", get_json_files("encounters"))
def test_valid_encounter_fixtures(file_path):
    data = load_json(file_path)
    EncounterState.model_validate(data)


@pytest.mark.parametrize("file_path", get_json_files("definitions"))
def test_valid_definition_fixtures(file_path):
    data = load_json(file_path)
    name = file_path.name
    if name.startswith("species_"):
        SpeciesBase.model_validate(data)
    elif name.startswith("class_"):
        ClassBase.model_validate(data)
    elif name.startswith("background_"):
        BackgroundBase.model_validate(data)
    elif name.startswith("feat_"):
        FeatBase.model_validate(data)
    elif name.startswith("feature_"):
        FeatureBase.model_validate(data)
    else:
        pytest.fail(f"Unknown definition prefix for {name}")


def test_fixture_volume_thresholds():
    for sub_dir, minimum in MIN_FIXTURE_COUNTS.items():
        count = len(get_json_files(sub_dir))
        assert count >= minimum, f"Expected at least {minimum} fixtures in {sub_dir}, found {count}"


def test_character_references_are_valid():
    campaign_ids = {
        load_json(path)["id"]
        for path in get_json_files("campaigns")
    }
    species_ids = {
        load_json(path)["id"]
        for path in get_json_files("definitions")
        if path.name.startswith("species_")
    }
    class_ids = {
        load_json(path)["id"]
        for path in get_json_files("definitions")
        if path.name.startswith("class_")
    }
    background_ids = {
        load_json(path)["id"]
        for path in get_json_files("definitions")
        if path.name.startswith("background_")
    }

    for character_path in get_json_files("characters"):
        character = load_json(character_path)
        assert character[
            "campaign_id"] in campaign_ids, f"Unknown campaign_id in {character_path.name}"
        assert character[
            "species_id"] in species_ids, f"Unknown species_id in {character_path.name}"
        assert character["class_id"] in class_ids, f"Unknown class_id in {character_path.name}"
        background_id = character.get("background_id")
        if background_id:
            assert background_id in background_ids, f"Unknown background_id in {character_path.name}"


def test_encounter_campaign_and_token_references_are_valid():
    campaign_ids = {
        load_json(path)["id"]
        for path in get_json_files("campaigns")
    }

    for encounter_path in get_json_files("encounters"):
        encounter = load_json(encounter_path)
        assert encounter[
            "campaign_id"] in campaign_ids, f"Unknown campaign_id in {encounter_path.name}"

        combatant_ids = {combatant["id"]
                         for combatant in encounter["combatants"]}
        token_actor_ids = {token["actor_id"]
                           for token in encounter["map"]["tokens"]}

        assert token_actor_ids == combatant_ids, (
            f"Encounter token actor IDs do not match combatants in {encounter_path.name}"
        )
        assert 0 <= encounter["active_index"] < max(1, len(encounter["combatants"])), (
            f"active_index out of range in {encounter_path.name}"
        )
