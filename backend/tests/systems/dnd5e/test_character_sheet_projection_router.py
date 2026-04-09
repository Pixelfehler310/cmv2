from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base, get_db
from src.identity.dependencies import get_current_active_user
from src.identity.models import User
from src.legacy.campaigns.lib.campaign import Campaign, CampaignMember
from src.legacy.campaigns.lib.character import Character
from src.legacy.data.lib.class_model import ClassModel
from src.legacy.data.lib.species import Species
from src.systems.dnd5e.character.router import get_character_stream_handler, router

pytestmark = pytest.mark.asyncio


async def _build_client_with_seeded_db() -> tuple[AsyncClient, async_sessionmaker[AsyncSession], FastAPI, AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        owner = User(id="user-owner", username="owner",
                     is_active=True, is_superuser=False)
        campaign = Campaign(id="camp-1", name="Test Campaign")
        member = CampaignMember(campaign_id="camp-1",
                                user_id="user-owner", role="PLAYER")
        species = Species(id="species-1", name="Human", description="Human")
        char_class = ClassModel(
            id="class-1", name="Fighter", description="Fighter", hit_die="1d10")

        session.add_all([owner, campaign, member, species, char_class])
        await session.commit()

    app = FastAPI()
    app.include_router(router)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    async def _override_current_user() -> User:
        async with session_factory() as session:
            result = await session.execute(select(User).where(User.id == "user-owner"))
            return result.scalar_one()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_active_user] = _override_current_user

    client = AsyncClient(transport=ASGITransport(
        app=app), base_url="http://test")
    return client, session_factory, app, engine


def _payload() -> dict:
    return {
        "name": "Aelar",
        "player_name": "Owner",
        "player_id": "user-owner",
        "status": "active",
        "campaign_id": "camp-1",
        "species_id": "species-1",
        "class_id": "class-1",
        "background_id": None,
        "ability_ids": [],
        "level": 1,
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


class StubCharacterSheetWsHandler:
    def __init__(self):
        self.projection_updated_events: list[dict] = []
        self.references_denied_events: list[dict] = []
        self.invalidation_required_events: list[dict] = []

    async def emit_character_sheet_projection_updated(
        self,
        *,
        campaign_id: str,
        request_id: str | None,
        character_id: str,
        sheet_revision: int,
        catalog_revision: int,
    ) -> None:
        self.projection_updated_events.append(
            {
                "campaign_id": campaign_id,
                "request_id": request_id,
                "character_id": character_id,
                "sheet_revision": sheet_revision,
                "catalog_revision": catalog_revision,
            }
        )

    async def emit_character_sheet_references_denied(
        self,
        *,
        campaign_id: str,
        request_id: str | None,
        character_id: str,
        sheet_revision: int,
        reason_code: str,
        unresolved_reference_ids: list[str],
    ) -> None:
        self.references_denied_events.append(
            {
                "campaign_id": campaign_id,
                "request_id": request_id,
                "character_id": character_id,
                "sheet_revision": sheet_revision,
                "reason_code": reason_code,
                "unresolved_reference_ids": unresolved_reference_ids,
            }
        )

    async def emit_character_sheet_invalidation_required(
        self,
        *,
        campaign_id: str,
        request_id: str | None,
        character_id: str,
        invalidated_at_revision: int,
        reason_code: str,
    ) -> None:
        self.invalidation_required_events.append(
            {
                "campaign_id": campaign_id,
                "request_id": request_id,
                "character_id": character_id,
                "invalidated_at_revision": invalidated_at_revision,
                "reason_code": reason_code,
            }
        )


async def _create_character(client: AsyncClient) -> str:
    response = await client.post("/api/characters", json=_payload())
    assert response.status_code == 200
    return response.json()["payload"]["id"]


async def test_character_sheet_projection_resolved_contract_shape():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        character_id = await _create_character(client)

        response = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
            headers={"x-request-id": "req-sheet-1"},
        )
        assert response.status_code == 200

        body = response.json()
        assert body["request_id"] == "req-sheet-1"
        assert body["status"] == "resolved"
        assert body["catalog_revision"] == 1

        projection = body["payload"]
        assert projection["character_id"] == character_id
        assert projection["catalog_revision"] == 1
        assert projection["sheet_revision"] == 1
        assert projection["resolution_status"] == "resolved"
        assert projection["computed_fields"]["class_id"] == "class-1"
        assert projection["computed_fields"]["species_id"] == "species-1"
        assert projection["last_resolved_at"]
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_generates_request_id_when_missing_header():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        character_id = await _create_character(client)

        response = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
        )
        assert response.status_code == 200

        body = response.json()
        assert body["status"] == "resolved"
        assert isinstance(body["request_id"], str)
        assert body["request_id"]
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_denied_for_missing_character():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        response = await client.get(
            "/api/characters/missing-character/sheet",
            params={"catalog_revision": 1},
            headers={"x-request-id": "req-sheet-missing-character"},
        )
        assert response.status_code == 404

        body = response.json()
        assert body["request_id"] == "req-sheet-missing-character"
        assert body["status"] == "denied"
        assert body["reason_code"] == "CHARACTER_NOT_FOUND"
        assert body["payload"]["unresolved_reference_ids"] == []
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_rejects_negative_catalog_revision():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        character_id = await _create_character(client)

        response = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": -1},
        )
        assert response.status_code == 422

        body = response.json()
        assert body["detail"][0]["loc"] == ["query", "catalog_revision"]
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_is_deterministic_for_same_revision():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        character_id = await _create_character(client)

        first = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
        )
        second = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["payload"] == second.json()["payload"]
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_denied_for_unresolved_reference():
    client, session_factory, _, engine = await _build_client_with_seeded_db()
    try:
        character_id = await _create_character(client)

        async with session_factory() as session:
            cls = await session.get(ClassModel, "class-1")
            assert cls is not None
            await session.delete(cls)
            await session.commit()

        response = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
        )
        assert response.status_code == 400

        body = response.json()
        assert body["status"] == "denied"
        assert body["reason_code"] == "UNRESOLVED_CLASS_DEFINITION"
        assert body["payload"]["resolution_status"] == "denied"
        assert body["payload"]["unresolved_reference_ids"] == ["class-1"]
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_marks_revision_gap_invalidated():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        character_id = await _create_character(client)

        first = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
        )
        assert first.status_code == 200
        assert first.json()["payload"]["sheet_revision"] == 1

        gap = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 4},
        )
        assert gap.status_code == 409
        body = gap.json()
        assert body["status"] == "invalidated"
        assert body["reason_code"] == "CATALOG_REVISION_MISMATCH"
        assert body["payload"]["resolution_status"] == "invalidated"
        assert body["payload"]["sheet_revision"] == 1
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_ignores_stale_revision_requests():
    client, _, _, engine = await _build_client_with_seeded_db()
    try:
        character_id = await _create_character(client)

        current = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 2},
        )
        assert current.status_code == 200
        assert current.json()["payload"]["catalog_revision"] == 2

        stale = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
        )
        assert stale.status_code == 200
        stale_payload = stale.json()["payload"]
        assert stale_payload["catalog_revision"] == 2
        assert stale_payload["sheet_revision"] == 1
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_denied_for_unresolved_ability_reference():
    client, session_factory, _, engine = await _build_client_with_seeded_db()
    try:
        character_id = await _create_character(client)

        async with session_factory() as session:
            character = await session.get(Character, character_id)
            assert character is not None
            character.ability_ids = ["missing-ability"]
            await session.commit()

        response = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
        )
        assert response.status_code == 400

        body = response.json()
        assert body["status"] == "denied"
        assert body["reason_code"] == "UNRESOLVED_ABILITY_DEFINITION"
        assert body["payload"]["resolution_status"] == "denied"
        assert body["payload"]["unresolved_reference_ids"] == [
            "missing-ability"]
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_emits_projection_updated_event_on_resolved_status():
    client, _, app, engine = await _build_client_with_seeded_db()
    ws_stub = StubCharacterSheetWsHandler()
    app.dependency_overrides[get_character_stream_handler] = lambda: ws_stub
    try:
        character_id = await _create_character(client)

        response = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
            headers={"x-request-id": "req-sheet-ws-resolved"},
        )
        assert response.status_code == 200

        assert len(ws_stub.projection_updated_events) == 1
        event = ws_stub.projection_updated_events[0]
        assert event["request_id"] == "req-sheet-ws-resolved"
        assert event["character_id"] == character_id
        assert event["catalog_revision"] == 1
        assert event["campaign_id"] == "camp-1"
        assert len(ws_stub.references_denied_events) == 0
        assert len(ws_stub.invalidation_required_events) == 0
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_emits_references_denied_event_on_denied_status():
    client, session_factory, app, engine = await _build_client_with_seeded_db()
    ws_stub = StubCharacterSheetWsHandler()
    app.dependency_overrides[get_character_stream_handler] = lambda: ws_stub
    try:
        character_id = await _create_character(client)

        async with session_factory() as session:
            cls = await session.get(ClassModel, "class-1")
            assert cls is not None
            await session.delete(cls)
            await session.commit()

        response = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
            headers={"x-request-id": "req-sheet-ws-denied"},
        )
        assert response.status_code == 400

        assert len(ws_stub.references_denied_events) == 1
        event = ws_stub.references_denied_events[0]
        assert event["request_id"] == "req-sheet-ws-denied"
        assert event["character_id"] == character_id
        assert event["reason_code"] == "UNRESOLVED_CLASS_DEFINITION"
        assert event["unresolved_reference_ids"] == ["class-1"]
        assert event["campaign_id"] == "camp-1"
        assert len(ws_stub.projection_updated_events) == 0
        assert len(ws_stub.invalidation_required_events) == 0
    finally:
        await client.aclose()
        await engine.dispose()


async def test_character_sheet_projection_emits_invalidation_event_on_invalidated_status():
    client, _, app, engine = await _build_client_with_seeded_db()
    ws_stub = StubCharacterSheetWsHandler()
    app.dependency_overrides[get_character_stream_handler] = lambda: ws_stub
    try:
        character_id = await _create_character(client)

        first = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 1},
            headers={"x-request-id": "req-sheet-ws-first"},
        )
        assert first.status_code == 200

        gap = await client.get(
            f"/api/characters/{character_id}/sheet",
            params={"catalog_revision": 4},
            headers={"x-request-id": "req-sheet-ws-invalidated"},
        )
        assert gap.status_code == 409

        assert len(ws_stub.projection_updated_events) == 1
        assert len(ws_stub.references_denied_events) == 0
        assert len(ws_stub.invalidation_required_events) == 1
        event = ws_stub.invalidation_required_events[0]
        assert event["request_id"] == "req-sheet-ws-invalidated"
        assert event["character_id"] == character_id
        assert event["invalidated_at_revision"] == 1
        assert event["reason_code"] == "CATALOG_REVISION_MISMATCH"
        assert event["campaign_id"] == "camp-1"
    finally:
        await client.aclose()
        await engine.dispose()
