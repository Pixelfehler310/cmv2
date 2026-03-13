import pytest
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from src.database import get_db
from src.identity.models import User


@pytest.mark.asyncio
async def test_api_campaigns_with_dev_token(client):
    # Keep auth-path behavior while avoiding dependency on external DB availability.
    mock_session = AsyncMock()

    mock_user_result = MagicMock()
    mock_user_result.scalars.return_value.first.return_value = User(
        id="00000000-0000-0000-0000-000000000001",
        username="simon",
        is_active=True,
        is_superuser=True,
    )

    mock_campaigns_result = MagicMock()
    mock_campaigns_result.scalars.return_value = []

    mock_session.execute.side_effect = [
        mock_user_result, mock_campaigns_result]
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        response = await client.get("/campaigns", headers={"Authorization": "Bearer dev-token"})
        assert response.status_code == 200
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_api_campaigns_without_token(client):
    response = await client.get("/campaigns")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_campaigns_with_invalid_token(client):
    response = await client.get("/campaigns", headers={"Authorization": "Bearer some-invalid-token"})
    assert response.status_code == 401
