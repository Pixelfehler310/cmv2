import pytest
from unittest.mock import MagicMock, AsyncMock
from src.main import app
from src.database import get_db
from src.data.lib.species import Species
from src.data.lib.class_model import ClassModel
from src.data.lib.background import Background

pytestmark = pytest.mark.legacy


@pytest.mark.anyio
async def test_create_species(client):
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    async def side_effect_refresh(instance):
        instance.id = "species-1"

    mock_session.refresh = AsyncMock(side_effect=side_effect_refresh)

    app.dependency_overrides[get_db] = lambda: mock_session

    data = {
        "name": "Elf",
        "description": "Pointy ears",
        "speed": 30,
        "size": "Medium"
    }

    response = await client.post("/definitions/species", json=data)
    assert response.status_code == 200
    assert response.json()["name"] == "Elf"
    assert response.json()["id"] == "species-1"

    app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_class(client):
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    async def side_effect_refresh(instance):
        instance.id = "class-1"

    mock_session.refresh = AsyncMock(side_effect=side_effect_refresh)

    app.dependency_overrides[get_db] = lambda: mock_session

    data = {
        "name": "Wizard",
        "description": "Magic user",
        "hit_die": "1d6"
    }

    response = await client.post("/definitions/classes", json=data)
    assert response.status_code == 200
    assert response.json()["name"] == "Wizard"

    app.dependency_overrides = {}


@pytest.mark.anyio
async def test_create_background(client):
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    async def side_effect_refresh(instance):
        instance.id = "bg-1"

    mock_session.refresh = AsyncMock(side_effect=side_effect_refresh)

    app.dependency_overrides[get_db] = lambda: mock_session

    data = {
        "name": "Sage",
        "description": "Learned scholar"
    }

    response = await client.post("/definitions/backgrounds", json=data)
    assert response.status_code == 200
    assert response.json()["name"] == "Sage"

    app.dependency_overrides = {}
