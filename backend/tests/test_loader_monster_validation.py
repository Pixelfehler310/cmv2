import pytest
from unittest.mock import AsyncMock, MagicMock

from src.legacy.data.lib.loader import DataLoader
from src.legacy.data.lib.monster import Monster


def _base_monster_payload() -> dict:
    return {
        "name": "Goblin",
        "size": "Small",
        "type": "Humanoid",
        "alignment": "Neutral Evil",
        "armor_class": 15,
        "hit_points": 7,
        "hit_dice": "2d6",
        "speed": {"walk": 30},
        "strength": 8,
        "dexterity": 14,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 8,
        "charisma": 8,
        "languages": "Goblin",
        "challenge_rating": 0.25,
        "xp": 50,
        "actions": [{"action_id": "monster.goblin.scimitar", "display_name": "Scimitar"}],
        "special_abilities": [],
        "legendary_actions": [],
        "inventory": [],
        "effects": [],
    }


@pytest.mark.asyncio
async def test_import_monsters_rejects_malformed_action_refs():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    loader = DataLoader("dummy_dir")
    malformed = _base_monster_payload()
    malformed["actions"] = [{"display_name": "Missing action id"}]
    loader.load_json_dir = MagicMock(return_value=[malformed])

    with pytest.raises(
        ValueError,
        match="Invalid monster action ref for 'Goblin' at index 0: action_id must be a non-empty string",
    ):
        await loader.import_monsters(mock_session)

    assert not mock_session.add.called
    assert not mock_session.commit.called


@pytest.mark.asyncio
async def test_import_monsters_rejects_duplicate_action_refs():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    loader = DataLoader("dummy_dir")
    duplicate = _base_monster_payload()
    duplicate["actions"] = [
        {"action_id": "monster.goblin.scimitar", "display_name": "Scimitar"},
        {"action_id": "monster.goblin.scimitar", "display_name": "Scimitar Copy"},
    ]
    loader.load_json_dir = MagicMock(return_value=[duplicate])

    with pytest.raises(
        ValueError,
        match="Duplicate monster action ref for 'Goblin': action_id 'monster.goblin.scimitar'",
    ):
        await loader.import_monsters(mock_session)

    assert not mock_session.add.called
    assert not mock_session.commit.called


@pytest.mark.asyncio
async def test_import_monsters_persists_valid_action_refs_as_json_dicts():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    loader = DataLoader("dummy_dir")
    loader.load_json_dir = MagicMock(return_value=[_base_monster_payload()])

    summary = await loader.import_monsters(mock_session)

    assert mock_session.add.called
    added_monster = mock_session.add.call_args[0][0]
    assert isinstance(added_monster, Monster)
    assert added_monster.actions == [
        {"action_id": "monster.goblin.scimitar", "display_name": "Scimitar"}]
    assert mock_session.commit.called
    assert summary["inserted"] == 1
    assert summary["skipped_existing"] == 0
    assert summary["failed"] == 0


@pytest.mark.asyncio
async def test_import_monsters_fails_fast_and_skips_remaining_entries_after_first_invalid_action_ref():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    invalid_first = _base_monster_payload()
    invalid_first["actions"] = [{"display_name": "Missing action id"}]

    valid_second = _base_monster_payload()
    valid_second["name"] = "Goblin Variant"

    loader = DataLoader("dummy_dir")
    loader.load_json_dir = MagicMock(
        return_value=[invalid_first, valid_second])

    with pytest.raises(
        ValueError,
        match="Invalid monster action ref for 'Goblin' at index 0: action_id must be a non-empty string",
    ):
        await loader.import_monsters(mock_session)

    assert not mock_session.execute.called
    assert not mock_session.add.called
    assert not mock_session.commit.called
