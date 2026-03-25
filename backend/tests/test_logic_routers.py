import pytest
from unittest.mock import MagicMock, AsyncMock
from src.main import app
from src.database import get_db
from src.campaigns.lib.campaign import Campaign
from src.campaigns.lib.character import Character
from src.identity.dependencies import get_current_active_user
from src.identity.models import User

dummy_user = User(id="dm1", username="testuser",
                  is_active=True, is_superuser=False)


@pytest.mark.anyio
async def test_create_campaign(client):
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    async def side_effect_refresh(instance):
        instance.id = "generated_id"

    mock_session.refresh = AsyncMock(side_effect=side_effect_refresh)

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = Campaign(
        id="generated_id",
        name="New Campaign",
        description="Test Desc",
        dm_id="dm1",
        context_version=1,
        characters=[]
    )
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: dummy_user

    campaign_data = {
        "name": "New Campaign",
        "description": "Test Desc",
        "dm_id": "dm1"
    }

    response = await client.post("/campaigns", json=campaign_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Campaign"
    assert mock_session.add.called
    assert mock_session.commit.called

    app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_campaigns(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # Modifying iter to yield (Campaign, Role) tuple
    mock_result.__iter__.return_value = [
        (Campaign(id="c1", name="Camp 1", description="Desc",
         dm_id="dm1", context_version=1, characters=[]), "DM")
    ]
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: dummy_user

    response = await client.get("/campaigns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Camp 1"

    app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_character(client):
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    async def side_effect_refresh(instance):
        instance.id = "generated_id"

    mock_session.refresh = AsyncMock(side_effect=side_effect_refresh)

    app.dependency_overrides[get_db] = lambda: mock_session

    character_data = {
        "name": "Legolas",
        "species_id": "species-1",
        "class_id": "class-1",
        "max_hp": 30,
        "current_hp": 30,
        "hit_dice": "3d10"
    }

    response = await client.post("/characters", json=character_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Legolas"
    assert mock_session.add.called

    app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_character(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Character(
        id="char1", name="Gimli", species_id="species-1", class_id="class-1",
        max_hp=40, current_hp=40, hit_dice="4d10",
        strength=16, dexterity=12, constitution=16, intelligence=10, wisdom=12, charisma=10,
        inventory=[], spells=[], spell_slots={}, effects=[], actions=[],
        level=1, xp=0, armor_class=10, speed=30, initiative=0, temp_hp=0
    )
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_session

    response = await client.get("/characters/char1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Gimli"

    app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_campaign_404(client):
    mock_session = AsyncMock()
    mock_result_member = MagicMock()
    mock_result_member.scalar_one_or_none.return_value = MagicMock(role="DM")
    mock_result_campaign = MagicMock()
    mock_result_campaign.scalar_one_or_none.return_value = None

    # We yield member first, then None for campaign
    mock_session.execute.side_effect = [
        mock_result_member, mock_result_campaign]

    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = lambda: dummy_user

    response = await client.get("/campaigns/nonexistent")
    assert response.status_code == 404

    app.dependency_overrides = {}


@pytest.mark.anyio
async def test_get_character_404(client):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_session

    response = await client.get("/characters/nonexistent")
    assert response.status_code == 404

    app.dependency_overrides = {}
