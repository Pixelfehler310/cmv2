from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import Base, get_db
from src.systems.dnd5e.content.api.router import (
    get_content_stream_handler,
    router as compendium_router,
)
from src.systems.dnd5e.content.infrastructure.orm import (
    CompendiumDefinitionModel,
    ContentPackModel,
    LinkedEntryModel,
    SearchIndexModel,
)


class StubContentStreamWsHandler:
    def __init__(self):
        self.events = []

    async def publish_mutation_event(self, event) -> None:
        self.events.append(event)


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def _create_tables(sync_conn):
        Base.metadata.tables[ContentPackModel.__tablename__].create(sync_conn)
        Base.metadata.tables[CompendiumDefinitionModel.__tablename__].create(
            sync_conn)
        Base.metadata.tables[SearchIndexModel.__tablename__].create(sync_conn)
        Base.metadata.tables[LinkedEntryModel.__tablename__].create(sync_conn)

    async with engine.begin() as conn:
        await conn.run_sync(_create_tables)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client_and_ws(db_session):
    app = FastAPI()
    app.include_router(compendium_router)

    async def override_get_db():
        yield db_session

    ws_handler = StubContentStreamWsHandler()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_content_stream_handler] = lambda: ws_handler

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client, ws_handler


def _monster_payload(*, definition_id: str, pack_id: str, slug: str) -> dict:
    return {
        "id": definition_id,
        "family": "monster",
        "slug": slug,
        "name": f"Monster {definition_id}",
        "lifecycle_state": "draft",
        "content_version": 1,
        "schema_version": 1,
        "pack_id": pack_id,
        "provenance_source": "tests",
        "provenance_author": "api-tests",
        "provenance_updated_at": datetime.now(timezone.utc).isoformat(),
        "challenge_rating": 0.25,
        "armor_class": 13,
        "hit_points_formula": "2d6",
        "action_operation_specs": [],
    }


@pytest.mark.anyio
async def test_pack_endpoints_roundtrip(client_and_ws):
    client, _ = client_and_ws

    create_response = await client.post(
        "/api/compendium/packs",
        json={
            "id": "pack-router-1",
            "title": "Router Pack",
            "author_user_id": "user-1",
            "is_homebrew": True,
            "pack_key": "router-pack",
            "compatibility_target": "5.1",
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["id"] == "pack-router-1"

    list_response = await client.get("/api/compendium/packs")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = await client.get("/api/compendium/packs/pack-router-1")
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Router Pack"


@pytest.mark.anyio
async def test_definition_update_then_publish_enforces_immutability(client_and_ws):
    client, ws_handler = client_and_ws

    await client.post(
        "/api/compendium/packs",
        json={"id": "pack-router-2", "title": "Router Pack 2"},
    )

    created = await client.post(
        "/api/compendium/definitions",
        json=_monster_payload(
            definition_id="def-router-1",
            pack_id="pack-router-2",
            slug="router-monster",
        ),
    )
    assert created.status_code == 200

    updated = await client.put(
        "/api/compendium/definitions/def-router-1",
        json={
            "expected_content_version": 1,
            "updates": {"name": "Router Monster Updated"},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["content_version"] == 2

    published = await client.post(
        "/api/compendium/definitions/def-router-1/publish",
        json={"campaign_id": "campaign-1"},
    )
    assert published.status_code == 200
    assert published.json()["lifecycle_state"] == "published"

    denied_update = await client.put(
        "/api/compendium/definitions/def-router-1",
        json={
            "expected_content_version": 3,
            "updates": {"name": "Illegal Update"},
        },
    )
    assert denied_update.status_code == 409
    assert denied_update.json(
    )["detail"]["error"] == "INVALID_LIFECYCLE_TRANSITION"

    lifecycle_event_types = [event.event_type for event in ws_handler.events]
    assert "definition_published" in lifecycle_event_types


@pytest.mark.anyio
async def test_supersede_endpoint_emits_lifecycle_event(client_and_ws):
    client, ws_handler = client_and_ws

    await client.post(
        "/api/compendium/packs",
        json={"id": "pack-router-3", "title": "Router Pack 3"},
    )

    await client.post(
        "/api/compendium/definitions",
        json=_monster_payload(
            definition_id="def-old",
            pack_id="pack-router-3",
            slug="monster-old",
        ),
    )
    await client.post(
        "/api/compendium/definitions",
        json=_monster_payload(
            definition_id="def-new",
            pack_id="pack-router-3",
            slug="monster-new",
        ),
    )

    await client.post(
        "/api/compendium/definitions/def-old/publish",
        json={"campaign_id": "campaign-2"},
    )
    await client.post(
        "/api/compendium/definitions/def-new/publish",
        json={"campaign_id": "campaign-2"},
    )

    superseded = await client.post(
        "/api/compendium/definitions/def-old/supersede",
        json={
            "new_definition_id": "def-new",
            "campaign_id": "campaign-2",
        },
    )
    assert superseded.status_code == 200
    assert superseded.json()["lifecycle_state"] == "superseded"

    supersede_events = [
        e for e in ws_handler.events if e.event_type == "definition_superseded"]
    assert len(supersede_events) == 1
    assert supersede_events[0].replacement_target_id == "def-new"


@pytest.mark.anyio
async def test_error_contract_maps_not_found_and_validation_failures(client_and_ws):
    client, _ = client_and_ws

    not_found_response = await client.post(
        "/api/compendium/definitions/missing/publish",
        json={"campaign_id": "campaign-3"},
    )
    assert not_found_response.status_code == 404
    assert not_found_response.json(
    )["detail"]["error"] == "DEFINITION_NOT_FOUND"

    await client.post(
        "/api/compendium/packs",
        json={"id": "pack-router-4", "title": "Router Pack 4"},
    )
    await client.post(
        "/api/compendium/definitions",
        json=_monster_payload(
            definition_id="def-validation",
            pack_id="pack-router-4",
            slug="monster-validation",
        ),
    )

    validation_response = await client.put(
        "/api/compendium/definitions/def-validation",
        json={
            "expected_content_version": 1,
            "updates": {"armor_class": "invalid-int"},
        },
    )
    assert validation_response.status_code == 400
    detail = validation_response.json()["detail"]
    assert detail["error"] == "VALIDATION_FAILED"
    assert "message" in detail
    assert "summary" in detail["message"]
    assert detail["message"]["field_errors"]["armor_class"][0]["type"] == "int_parsing"
