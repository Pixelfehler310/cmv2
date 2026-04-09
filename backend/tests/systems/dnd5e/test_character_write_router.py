from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base, get_db
from src.identity.dependencies import get_current_active_user
from src.identity.models import User
from src.legacy.campaigns.lib.campaign import Campaign, CampaignMember
from src.legacy.campaigns.lib.character import Character
from src.legacy.data.lib.class_model import ClassModel
from src.legacy.data.lib.species import Species
from src.systems.dnd5e.character.router import router

pytestmark = pytest.mark.asyncio


async def _build_client_with_seeded_db() -> tuple[AsyncClient, async_sessionmaker[AsyncSession], FastAPI, AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        owner = User(id="user-owner", username="owner",
                     is_active=True, is_superuser=False)
        outsider = User(id="user-outsider", username="outsider",
                        is_active=True, is_superuser=False)
        campaign = Campaign(id="camp-1", name="Test Campaign")
        second_campaign = Campaign(id="camp-2", name="Second Test Campaign")
        member = CampaignMember(campaign_id="camp-1",
                                user_id="user-owner", role="PLAYER")
        second_member = CampaignMember(
            campaign_id="camp-2", user_id="user-owner", role="PLAYER")
        species = Species(id="species-1", name="Human", description="Human")
        char_class = ClassModel(
            id="class-1", name="Fighter", description="Fighter", hit_die="1d10")

        session.add_all(
            [
                owner,
                outsider,
                campaign,
                second_campaign,
                member,
                second_member,
                species,
                char_class,
            ]
        )
        await session.commit()

    app = FastAPI()
    app.include_router(router)
    app.state.current_user_id = "user-owner"

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    async def _override_current_user() -> User:
        async with session_factory() as session:
            result = await session.execute(
                select(User).where(User.id == app.state.current_user_id)
            )
            return result.scalar_one()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_active_user] = _override_current_user

    client = AsyncClient(transport=ASGITransport(
        app=app), base_url="http://test")
    return client, session_factory, app, engine


def _payload(*, player_id: str = "user-owner", name: str = "Aelar", level: int = 1) -> dict:
    return {
        "name": name,
        "player_name": "Owner",
        "player_id": player_id,
        "status": "active",
        "campaign_id": "camp-1",
        "species_id": "species-1",
        "class_id": "class-1",
        "background_id": None,
        "ability_ids": [],
        "level": level,
        "xp": 0,
        "alignment": "neutral",
        "strength": 10,
        "dexterity": 12,
        "constitution": 13,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 8,
        "max_hp": 12,
        "current_hp": 12,
        "temp_hp": 0,
        "hit_dice": "1d10",
        "armor_class": 14,
        "speed": 30,
        "initiative": 1,
        "inventory": [],
        "spells": [],
        "spell_slots": {},
        "actions": [],
        "effects": [],
    }


def _assert_denied(
    response,
    *,
    status_code: int,
    reason_code: str,
    request_id: str | None = None,
    unresolved_reference_ids: list[str] | None = None,
):
    assert response.status_code == status_code
    body = response.json()
    assert body["status"] == "denied"
    assert body["reason_code"] == reason_code
    if request_id is not None:
        assert body["request_id"] == request_id
    if unresolved_reference_ids is not None:
        assert body["payload"]["unresolved_reference_ids"] == unresolved_reference_ids
    else:
        assert body["payload"]["unresolved_reference_ids"] == []
    return body


async def test_create_character_resolved_envelope():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        response = await client.post(
            "/api/characters",
            json=_payload(),
            headers={"x-request-id": "req-create-1"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["request_id"] == "req-create-1"
        assert body["status"] == "resolved"
        assert body["reason_code"] is None
        assert body["payload"]["player_id"] == "user-owner"
        assert body["payload"]["status"] == "active"
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_generates_request_id_when_missing_header():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        response = await client.post(
            "/api/characters",
            json=_payload(),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "resolved"
        assert isinstance(body["request_id"], str)
        assert body["request_id"]
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_when_missing_player_id():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload(player_id="")
        response = await client.post(
            "/api/characters",
            json=bad_payload,
            headers={"x-request-id": "req-missing-player"},
        )
        _assert_denied(
            response,
            status_code=400,
            reason_code="MISSING_PLAYER_ID",
            request_id="req-missing-player",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_on_ownership_violation():
    client, _, app, engine = await _build_client_with_seeded_db()
    try:
        app.state.current_user_id = "user-outsider"
        response = await client.post("/api/characters", json=_payload(player_id="user-owner"))
        _assert_denied(
            response,
            status_code=403,
            reason_code="PLAYER_OWNERSHIP_VIOLATION",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_when_missing_campaign_id():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload()
        bad_payload["campaign_id"] = ""
        response = await client.post("/api/characters", json=bad_payload)
        _assert_denied(
            response,
            status_code=400,
            reason_code="MISSING_CAMPAIGN_ID",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_when_missing_name():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload(name="")
        response = await client.post("/api/characters", json=bad_payload)
        _assert_denied(
            response,
            status_code=400,
            reason_code="MISSING_REQUIRED_FIELD",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_when_invalid_level():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        response = await client.post("/api/characters", json=_payload(level=0))
        _assert_denied(
            response,
            status_code=400,
            reason_code="INVALID_LEVEL_VALUE",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_when_user_not_campaign_member():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload()
        bad_payload["campaign_id"] = "missing-campaign"
        response = await client.post("/api/characters", json=bad_payload)
        _assert_denied(
            response,
            status_code=403,
            reason_code="CAMPAIGN_MEMBERSHIP_REQUIRED",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_update_character_happy_path():
    client, session_factory, _, engine = await _build_client_with_seeded_db()
    try:
        create_response = await client.post("/api/characters", json=_payload())
        assert create_response.status_code == 200
        character_id = create_response.json()["payload"]["id"]

        update_payload = _payload(name="Aelar Updated", level=2)
        update_response = await client.put(f"/api/characters/{character_id}", json=update_payload)
        assert update_response.status_code == 200
        body = update_response.json()
        assert body["status"] == "resolved"
        assert body["payload"]["name"] == "Aelar Updated"
        assert body["payload"]["level"] == 2

        async with session_factory() as session:
            persisted = await session.get(Character, character_id)
            assert persisted is not None
            assert persisted.name == "Aelar Updated"
            assert persisted.level == 2
    finally:
        await client.aclose()
        await engine.dispose()


async def test_update_character_denied_when_character_not_found():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        response = await client.put("/api/characters/missing-character", json=_payload())
        _assert_denied(
            response,
            status_code=404,
            reason_code="CHARACTER_NOT_FOUND",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_update_character_denied_on_player_ownership_violation():
    client, _, app, engine = await _build_client_with_seeded_db()
    try:
        create_response = await client.post("/api/characters", json=_payload())
        assert create_response.status_code == 200
        character_id = create_response.json()["payload"]["id"]

        app.state.current_user_id = "user-outsider"
        response = await client.put(f"/api/characters/{character_id}", json=_payload())
        _assert_denied(
            response,
            status_code=403,
            reason_code="PLAYER_OWNERSHIP_VIOLATION",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_update_character_denied_on_unresolved_required_reference():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        create_response = await client.post("/api/characters", json=_payload())
        assert create_response.status_code == 200
        character_id = create_response.json()["payload"]["id"]

        bad_payload = _payload()
        bad_payload["class_id"] = "missing-class"
        response = await client.put(f"/api/characters/{character_id}", json=bad_payload)
        _assert_denied(
            response,
            status_code=400,
            reason_code="UNRESOLVED_CLASS_DEFINITION",
            unresolved_reference_ids=["missing-class"],
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_on_duplicate_ability_ids():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload()
        bad_payload["ability_ids"] = ["ability-1", "ability-1"]
        response = await client.post("/api/characters", json=bad_payload)
        _assert_denied(
            response,
            status_code=400,
            reason_code="DUPLICATE_ABILITY_IDS",
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_on_unresolved_required_reference():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload()
        bad_payload["class_id"] = "missing-class"
        response = await client.post("/api/characters", json=bad_payload)
        _assert_denied(
            response,
            status_code=400,
            reason_code="UNRESOLVED_CLASS_DEFINITION",
            unresolved_reference_ids=["missing-class"],
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_on_unresolved_species_reference():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload()
        bad_payload["species_id"] = "missing-species"
        response = await client.post("/api/characters", json=bad_payload)
        _assert_denied(
            response,
            status_code=400,
            reason_code="UNRESOLVED_SPECIES_DEFINITION",
            unresolved_reference_ids=["missing-species"],
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_on_unresolved_background_reference():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload()
        bad_payload["background_id"] = "missing-background"
        response = await client.post("/api/characters", json=bad_payload)
        _assert_denied(
            response,
            status_code=400,
            reason_code="UNRESOLVED_BACKGROUND_DEFINITION",
            unresolved_reference_ids=["missing-background"],
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_create_character_denied_on_unresolved_ability_reference():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        bad_payload = _payload()
        bad_payload["ability_ids"] = ["missing-ability"]
        response = await client.post("/api/characters", json=bad_payload)
        _assert_denied(
            response,
            status_code=400,
            reason_code="UNRESOLVED_ABILITY_DEFINITION",
            unresolved_reference_ids=["missing-ability"],
        )
    finally:
        await client.aclose()
        await engine.dispose()


async def test_update_character_denied_on_campaign_reassignment():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        create_response = await client.post("/api/characters", json=_payload())
        assert create_response.status_code == 200
        character_id = create_response.json()["payload"]["id"]

        update_payload = _payload(name="Aelar Updated", level=2)
        update_payload["campaign_id"] = "camp-2"
        response = await client.put(f"/api/characters/{character_id}", json=update_payload)
        _assert_denied(
            response,
            status_code=403,
            reason_code="CAMPAIGN_OWNERSHIP_VIOLATION",
        )
    finally:
        await client.aclose()
        await engine.dispose()
