import pytest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from src.data.lib.loader import DataLoader
from src.data.lib.item import Item

@pytest.mark.asyncio
async def test_import_items():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    # Mock execute to return None (item does not exist)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    loader = DataLoader("dummy_dir")
    sample_json = '[{"name": "Sword", "description": "Sharp", "type": "Weapon", "rarity": "Common", "weight": 2, "price": 10, "properties": {}, "effects": []}]'
    
    with patch("builtins.open", mock_open(read_data=sample_json)):
        with patch("os.path.exists", return_value=True):
            await loader.import_items(mock_session, "items.json")

    assert mock_session.add.called
    args, _ = mock_session.add.call_args
    added_item = args[0]
    assert isinstance(added_item, Item)
    assert added_item.name == "Sword"
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_import_items_existing():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    # Mock execute to return existing item
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Item(name="Sword")
    mock_session.execute.return_value = mock_result
    
    loader = DataLoader("dummy_dir")
    
    sample_json = '[{"name": "Sword", "description": "Sharp", "type": "Weapon", "rarity": "Common", "weight": 2, "price": 10, "properties": {}, "effects": []}]'
    
    with patch("builtins.open", mock_open(read_data=sample_json)):
        with patch("os.path.exists", return_value=True):
            await loader.import_items(mock_session, "items.json")
            
    # Verify add was NOT called
    assert not mock_session.add.called
    assert mock_session.commit.called
