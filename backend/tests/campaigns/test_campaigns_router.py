import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.main import app
from src.database import get_db
from src.campaigns.lib.campaign import Campaign, CampaignMember, CampaignRole
from src.identity.models import User
from src.identity.dependencies import get_current_active_user

async def override_get_db():
    mock_session = AsyncMock()
    yield mock_session

@pytest.fixture
def override_admin_user():
    def _override():
        return User(id="admin-id", username="admin_user", is_active=True, is_superuser=False)
    return _override

@pytest.fixture
def override_normal_user():
    def _override():
        return User(id="normal-id", username="normal_user", is_active=True, is_superuser=False)
    return _override

@pytest.fixture
def override_superuser():
    def _override():
        return User(id="super-id", username="super_user", is_active=True, is_superuser=True)
    return _override

@pytest.mark.asyncio
async def test_get_campaigns_admin_bypass(client, override_admin_user):
    mock_session = AsyncMock()
    
    mock_result = MagicMock()
    mock_campaign = Campaign(id="camp1", name="Campaign 1", description="Desc")
    mock_result.scalars.return_value = [mock_campaign]
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = override_admin_user
    
    with patch("src.config.settings.ADMIN_USERNAME", "admin_user"):
        response = await client.get("/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Campaign 1"
        assert data[0]["role"] == "DM"
    
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_campaigns_normal_user(client, override_normal_user):
    mock_session = AsyncMock()
    
    mock_result = MagicMock()
    # Mock return format from select(Campaign, CampaignMember.role)
    mock_campaign = Campaign(id="camp1", name="Campaign 1", description="Desc")
    mock_result.__iter__.return_value = [(mock_campaign, "PLAYER")]
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = override_normal_user
    
    with patch("src.config.settings.ADMIN_USERNAME", "admin_user"):
        response = await client.get("/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Campaign 1"
        assert data[0]["role"] == "PLAYER"
    
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_campaign_admin_bypass(client, override_admin_user):
    mock_session = AsyncMock()
    
    mock_result = MagicMock()
    mock_campaign = Campaign(id="camp1", name="Campaign 1", description="Desc")
    mock_result.scalar_one_or_none.side_effect = [None, mock_campaign] # 1st call: member check, 2nd call: campaign fetch
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = override_admin_user
    
    with patch("src.config.settings.ADMIN_USERNAME", "admin_user"):
        response = await client.get("/campaigns/camp1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Campaign 1"
        assert data["role"] == "DM"
    
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_delete_campaign_admin_bypass(client, override_admin_user):
    mock_session = AsyncMock()
    
    mock_result = MagicMock()
    mock_campaign = Campaign(id="camp1", name="Campaign 1", description="Desc")
    # For admin, delete skips the DM check. It only queries the campaign to delete.
    mock_result.scalar_one_or_none.return_value = mock_campaign
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = override_admin_user
    
    with patch("src.config.settings.ADMIN_USERNAME", "admin_user"):
        response = await client.delete("/campaigns/camp1")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
    
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_campaigns_superuser_bypass(client, override_superuser):
    mock_session = AsyncMock()
    
    mock_result = MagicMock()
    mock_campaign = Campaign(id="camp2", name="Campaign 2", description="Desc")
    mock_result.scalars.return_value = [mock_campaign]
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_active_user] = override_superuser
    
    with patch("src.config.settings.ADMIN_USERNAME", "admin_user"):
        response = await client.get("/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Campaign 2"
        assert data[0]["role"] == "DM"
    
    app.dependency_overrides = {}
