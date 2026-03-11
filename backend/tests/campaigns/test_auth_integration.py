import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_api_campaigns_with_dev_token(client):
    # This hits the actual application using the dev-token
    response = await client.get("/campaigns", headers={"Authorization": "Bearer dev-token"})
    print("Response JSON:", response.json())
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_api_campaigns_without_token(client):
    response = await client.get("/campaigns")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_api_campaigns_with_invalid_token(client):
    response = await client.get("/campaigns", headers={"Authorization": "Bearer some-invalid-token"})
    assert response.status_code == 401
