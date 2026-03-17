import pytest
from unittest.mock import MagicMock, AsyncMock
from src.data.lib.loader import DataLoader
from src.data.lib.item import Item


@pytest.mark.asyncio
async def test_import_items():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    # Item does not exist yet
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    loader = DataLoader("dummy_dir")

    loader.load_json_dir = MagicMock(return_value=[
        {
            "name": "Sword",
            "description": "Sharp",
            "type": "Weapon",
            "rarity": "Common",
            "weight": 2,
            "price": 10,
            "properties": {},
            "effects": []
        }
    ])

    summary = await loader.import_items(mock_session)

    assert mock_session.add.called
    args, _ = mock_session.add.call_args
    added_item = args[0]
    assert isinstance(added_item, Item)
    assert added_item.name == "Sword"
    assert mock_session.commit.called
    assert summary["inserted"] == 1
    assert summary["skipped_existing"] == 0
    assert summary["failed"] == 0


@pytest.mark.asyncio
async def test_import_items_existing():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    # Existing item found in DB
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Item(name="Sword")
    mock_session.execute.return_value = mock_result

    loader = DataLoader("dummy_dir")

    loader.load_json_dir = MagicMock(return_value=[
        {
            "name": "Sword",
            "description": "Sharp",
            "type": "Weapon",
            "rarity": "Common",
            "weight": 2,
            "price": 10,
            "properties": {},
            "effects": []
        }
    ])

    summary = await loader.import_items(mock_session)

    assert not mock_session.add.called
    assert mock_session.commit.called
    assert summary["inserted"] == 0
    assert summary["skipped_existing"] == 1
    assert summary["failed"] == 0


@pytest.mark.asyncio
async def test_import_items_missing_name_counts_failed():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    loader = DataLoader("dummy_dir")
    loader.load_json_dir = MagicMock(return_value=[
        {
            "description": "Missing name field",
            "type": "weapon",
            "rarity": "common",
            "weight": 1,
            "price": 1,
            "properties": {},
            "effects": []
        }
    ])

    summary = await loader.import_items(mock_session)

    assert not mock_session.add.called
    assert mock_session.commit.called
    assert summary["inserted"] == 0
    assert summary["skipped_existing"] == 0
    assert summary["failed"] == 1


@pytest.mark.asyncio
async def test_load_all_aggregates_all_sections():
    loader = DataLoader("dummy_dir")
    mock_session = AsyncMock()

    loader.import_definitions = AsyncMock(
        return_value={"inserted": 10, "failed": 0})
    loader.import_items = AsyncMock(return_value={"inserted": 50, "failed": 0})
    loader.import_spells = AsyncMock(
        return_value={"inserted": 35, "failed": 0})
    loader.import_monsters = AsyncMock(
        return_value={"inserted": 25, "failed": 0})
    loader.import_campaigns = AsyncMock(
        return_value={"inserted": 5, "failed": 0})
    loader.import_characters = AsyncMock(
        return_value={"inserted": 12, "failed": 0})
    loader.import_content_packs = AsyncMock(
        return_value={"imported": 1, "failed": 0})

    summary = await loader.load_all(mock_session)

    assert set(summary.keys()) == {
        "definitions",
        "items",
        "spells",
        "monsters",
        "campaigns",
        "characters",
        "content_packs",
    }
    assert summary["definitions"]["inserted"] == 10
    assert summary["items"]["inserted"] == 50
    assert summary["spells"]["inserted"] == 35
    assert summary["monsters"]["inserted"] == 25
    assert summary["campaigns"]["inserted"] == 5
    assert summary["characters"]["inserted"] == 12
    assert summary["content_packs"]["imported"] == 1

    loader.import_definitions.assert_awaited_once_with(mock_session)
    loader.import_items.assert_awaited_once_with(mock_session)
    loader.import_spells.assert_awaited_once_with(mock_session)
    loader.import_monsters.assert_awaited_once_with(mock_session)
    loader.import_campaigns.assert_awaited_once_with(mock_session)
    loader.import_characters.assert_awaited_once_with(mock_session)
    loader.import_content_packs.assert_awaited_once_with(mock_session)
