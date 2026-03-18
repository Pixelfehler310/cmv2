import json
import re
from pathlib import Path

from src.schemas.monster import MonsterCreate
from src.systems.dnd5e.schemas.contracts import ContentPack


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"
MONSTER_FIXTURES_DIR = FIXTURES_DIR / "monsters"
MONSTER_CONTENT_PACK_PATH = FIXTURES_DIR / \
    "content_packs" / "001_monster_action_refs.json"
CANONICAL_ACTION_ID_PATTERN = re.compile(
    r"^monster\.[a-z0-9_]+\.[a-z0-9_]+(?:\.[a-z0-9_]+)*$")


def _fixture_slug(path: Path) -> str:
    return re.sub(r"^[0-9]+_", "", path.stem)


def test_monster_action_refs_fixture_shape_is_strict_and_schema_valid() -> None:
    fixture_files = sorted(MONSTER_FIXTURES_DIR.glob("*.json"))
    assert fixture_files, "Expected monster fixture files"

    for fixture_file in fixture_files:
        payload = json.loads(fixture_file.read_text(encoding="utf-8"))
        MonsterCreate.model_validate(payload)
        seen_action_ids: set[str] = set()

        for action in payload.get("actions", []):
            assert set(action.keys()).issubset({"action_id", "display_name"})
            assert isinstance(action["action_id"], str)
            assert action["action_id"].strip()
            assert CANONICAL_ACTION_ID_PATTERN.match(
                action["action_id"]) is not None
            assert action["action_id"] not in seen_action_ids
            seen_action_ids.add(action["action_id"])


def test_monster_action_refs_are_backed_by_content_pack_definitions_and_bindings() -> None:
    pack_payload = json.loads(
        MONSTER_CONTENT_PACK_PATH.read_text(encoding="utf-8"))
    pack = ContentPack.model_validate(pack_payload)

    action_ids = {action.action_id for action in pack.actions}
    bound_pairs = {
        (binding.actor_template_id, binding.action_id)
        for binding in pack.abilities
        if binding.actor_template_id
    }

    fixture_files = sorted(MONSTER_FIXTURES_DIR.glob("*.json"))
    assert fixture_files, "Expected monster fixture files"

    for fixture_file in fixture_files:
        payload = json.loads(fixture_file.read_text(encoding="utf-8"))
        slug = _fixture_slug(fixture_file)
        for action in payload.get("actions", []):
            action_id = action["action_id"]
            assert action_id in action_ids
            assert (slug, action_id) in bound_pairs
