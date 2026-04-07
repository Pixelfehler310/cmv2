import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from types import SimpleNamespace
from src.main import app
from src.database import get_db
from src.legacy.campaigns.lib.campaign import Campaign, CampaignMember, CampaignRole
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
    mock_campaign = Campaign(
        id="camp1", name="Campaign 1", description="Desc", context_version=1)
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
    mock_campaign = Campaign(
        id="camp1", name="Campaign 1", description="Desc", context_version=1)
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
    mock_campaign = Campaign(
        id="camp1", name="Campaign 1", description="Desc", context_version=1)
    # 1st call: member check, 2nd call: campaign fetch
    mock_result.scalar_one_or_none.side_effect = [None, mock_campaign]
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
    mock_campaign = Campaign(
        id="camp1", name="Campaign 1", description="Desc", context_version=1)
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
    mock_campaign = Campaign(
        id="camp2", name="Campaign 2", description="Desc", context_version=1)
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


@pytest.mark.asyncio
async def test_get_campaign_context_returns_backend_context(client, override_normal_user, monkeypatch):
    class FakeCombatService:
        def __init__(self, _db):
            self.db = _db

        async def get_context(self, campaign_id: str):
            assert campaign_id == "camp1"
            return SimpleNamespace(
                id="camp1",
                current_scene="scene.default",
                active_encounter_id="enc.default",
                context_version=4,
            )

    async def fake_resolve_member(_db, campaign_id, _current_user):
        assert campaign_id == "camp1"
        return SimpleNamespace(role=CampaignRole.PLAYER), False

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_active_user] = override_normal_user
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns.CampaignContextApplicationService", FakeCombatService)
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns._resolve_member_or_raise", fake_resolve_member)

    response = await client.get("/campaigns/camp1/context")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "campaign_id": "camp1",
        "scene_id": "scene.default",
        "encounter_id": "enc.default",
        "context_version": 4,
    }

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_list_campaign_scenes_returns_scene_options(client, override_normal_user, monkeypatch):
    class FakeCombatService:
        def __init__(self, _db):
            self.db = _db

        async def list_scenes(self, campaign_id: str):
            assert campaign_id == "camp1"
            return [
                SimpleNamespace(scene_id="scene.a", name="Scene A"),
                SimpleNamespace(scene_id="scene.b", name="Scene B"),
            ]

    async def fake_resolve_member(_db, campaign_id, _current_user):
        assert campaign_id == "camp1"
        return SimpleNamespace(role=CampaignRole.PLAYER), False

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_active_user] = override_normal_user
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns.CampaignContextApplicationService", FakeCombatService)
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns._resolve_member_or_raise", fake_resolve_member)

    response = await client.get("/campaigns/camp1/scenes")
    assert response.status_code == 200
    assert response.json() == [
        {"scene_id": "scene.a", "name": "Scene A"},
        {"scene_id": "scene.b", "name": "Scene B"},
    ]

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_list_scene_encounters_returns_encounter_options(client, override_normal_user, monkeypatch):
    class FakeCombatService:
        def __init__(self, _db):
            self.db = _db

        async def list_encounters(self, campaign_id: str, scene_id: str):
            assert campaign_id == "camp1"
            assert scene_id == "scene.default"
            return [
                SimpleNamespace(encounter_id="enc.1",
                                scene_id="scene.default", name="Encounter 1"),
                SimpleNamespace(encounter_id="enc.2",
                                scene_id="scene.default", name="Encounter 2"),
            ]

    async def fake_resolve_member(_db, campaign_id, _current_user):
        assert campaign_id == "camp1"
        return SimpleNamespace(role=CampaignRole.PLAYER), False

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_active_user] = override_normal_user
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns.CampaignContextApplicationService", FakeCombatService)
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns._resolve_member_or_raise", fake_resolve_member)

    response = await client.get("/campaigns/camp1/scenes/scene.default/encounters")
    assert response.status_code == 200
    assert response.json() == [
        {"encounter_id": "enc.1", "scene_id": "scene.default", "name": "Encounter 1"},
        {"encounter_id": "enc.2", "scene_id": "scene.default", "name": "Encounter 2"},
    ]

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_select_campaign_context_requires_dm_role(client, override_normal_user, monkeypatch):
    async def fake_resolve_member(_db, _campaign_id, _current_user):
        return SimpleNamespace(role=CampaignRole.PLAYER), False

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_active_user] = override_normal_user
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns._resolve_member_or_raise", fake_resolve_member)

    response = await client.post(
        "/campaigns/camp1/context/select",
        json={"scene_id": "scene.default", "encounter_id": "enc.default"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only DM can change campaign context"

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_select_campaign_context_updates_context_for_dm(client, override_normal_user, monkeypatch):
    class FakeCombatService:
        def __init__(self, _db):
            self.db = _db

        async def select_context(self, campaign_id: str, scene_id: str, encounter_id: str):
            assert campaign_id == "camp1"
            assert scene_id == "scene.default"
            assert encounter_id == "enc.default"
            return SimpleNamespace(
                id="camp1",
                current_scene=scene_id,
                active_encounter_id=encounter_id,
                context_version=5,
            )

    async def fake_resolve_member(_db, campaign_id, _current_user):
        assert campaign_id == "camp1"
        return SimpleNamespace(role=CampaignRole.DM), False

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_active_user] = override_normal_user
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns.CampaignContextApplicationService", FakeCombatService)
    monkeypatch.setattr(
        "src.legacy.campaigns.routers.campaigns._resolve_member_or_raise", fake_resolve_member)

    response = await client.post(
        "/campaigns/camp1/context/select",
        json={"scene_id": "scene.default", "encounter_id": "enc.default"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "campaign_id": "camp1",
        "scene_id": "scene.default",
        "encounter_id": "enc.default",
        "context_version": 5,
    }

    app.dependency_overrides = {}
