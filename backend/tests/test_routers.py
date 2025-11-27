import pytest
from unittest.mock import MagicMock, AsyncMock
from src.main import app
from src.common.database import get_db
from src.data.lib.item import Item
from src.data.lib.spell import Spell
from src.data.lib.monster import Monster

# Mock DB Dependency
async def override_get_db():
    mock_session = AsyncMock()
    
    # Mock execute result for Items
    mock_result_items = MagicMock()
    mock_result_items.scalars.return_value.all.return_value = [
        Item(id="1", name="Test Item", description="Desc", type="Weapon", rarity="Common", weight=1.0, price=10, properties={}, effects=[])
    ]
    mock_result_items.scalar_one_or_none.return_value = Item(id="1", name="Test Item", description="Desc", type="Weapon", rarity="Common", weight=1.0, price=10, properties={}, effects=[])
    
    # Mock execute result for Spells
    mock_result_spells = MagicMock()
    mock_result_spells.scalars.return_value.all.return_value = [
        Spell(id="2", name="Test Spell", description="Desc", level=1, school="Evo", casting_time="1A", range="30ft", components={}, duration="Inst", effects=[])
    ] 
    # It's hard to distinguish calls to execute(select(Item)) vs execute(select(Spell)) easily with simple mocks without inspecting args.
    # So we will define separate tests with separate overrides or smarter mocks.
    
    yield mock_session

# We will use specific overrides in tests instead of a global one

@pytest.mark.anyio
async def test_get_items(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Item(id="1", name="Test Item", description="Desc", type="Weapon", rarity="Common", weight=1.0, price=10, properties={}, effects=[])
    ]
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = await client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Item"
    
    app.dependency_overrides = {}

@pytest.mark.anyio
async def test_get_spells(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Spell(id="2", name="Test Spell", description="Desc", level=1, school="Evo", casting_time="1A", range="30ft", components={}, duration="Inst", effects=[])
    ]
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = await client.get("/spells/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Spell"
    
    app.dependency_overrides = {}

@pytest.mark.anyio
async def test_get_monsters(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Monster(id="3", name="Test Monster", description="Desc", size="M", type="Beast", alignment="U", armor_class=10, hit_points=10, hit_dice="1d10", speed={}, strength=10, dexterity=10, constitution=10, intelligence=10, wisdom=10, charisma=10, languages="Common", challenge_rating=1.0, xp=100, effects=[], proficiencies=[], special_abilities=[], actions=[], legendary_actions=[], senses={}, inventory=[])
    ]
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = await client.get("/monsters/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Monster"
    
    app.dependency_overrides = {}

@pytest.mark.anyio
async def test_get_item_404(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = await client.get("/items/nonexistent")
    assert response.status_code == 404
    
    app.dependency_overrides = {}

@pytest.mark.anyio
async def test_get_spell_404(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = await client.get("/spells/nonexistent")
    assert response.status_code == 404
    
    app.dependency_overrides = {}

@pytest.mark.anyio
async def test_get_monster_404(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = await client.get("/monsters/nonexistent")
    assert response.status_code == 404
    
    app.dependency_overrides = {}
