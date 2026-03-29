"""
V05-07 API-Level Integration Tests via FastAPI TestClient.

These tests exercise the HTTP transport layer to close the coverage gap
on the router module and verify the full request → response → error contract.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base
from src.systems.dnd5e.content.api.router import router, get_compendium_service
from src.systems.dnd5e.content.api.ws_events import ContentStreamWsHandler
from src.systems.dnd5e.content.application.services import CompendiumApplicationService
from src.systems.dnd5e.content.infrastructure.orm import (
    CompendiumDefinitionModel,
    ContentPackModel,
    LinkedEntryModel,
    SearchIndexModel,
)
from src.systems.dnd5e.content.infrastructure.unit_of_work import CompendiumUnitOfWork


_V05_TABLES = [
    ContentPackModel.__tablename__,
    CompendiumDefinitionModel.__tablename__,
    SearchIndexModel.__tablename__,
    LinkedEntryModel.__tablename__,
]


@pytest.fixture
async def api_client():
    """FastAPI test client backed by an in-memory SQLite engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        for table_name in _V05_TABLES:
            await conn.run_sync(
                lambda sync_conn, tn=table_name: Base.metadata.tables[tn].create(sync_conn)
            )

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    app = FastAPI()
    app.include_router(router)

    # Override the DI to use our in-memory session
    ws_handler = ContentStreamWsHandler()

    def _override_service():
        session = session_factory()
        return CompendiumApplicationService(
            uow_factory=lambda: CompendiumUnitOfWork(session),
            event_publisher=ws_handler.publish_mutation_event,
        )

    app.dependency_overrides[get_compendium_service] = _override_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await engine.dispose()


# =========================================================================
# Pack CRUD through HTTP
# =========================================================================
@pytest.mark.asyncio
async def test_create_and_list_packs(api_client: AsyncClient):
    """POST /packs then GET /packs returns the created pack."""
    resp = await api_client.post(
        "/api/compendium/packs",
        json={
            "id": "http-pack",
            "title": "HTTP Test Pack",
            "author_user_id": "user-1",
            "is_homebrew": True,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "http-pack"
    assert body["lifecycle_state"] == "draft"

    # List
    resp2 = await api_client.get("/api/compendium/packs")
    assert resp2.status_code == 200
    packs = resp2.json()
    assert len(packs) >= 1
    assert any(p["id"] == "http-pack" for p in packs)


@pytest.mark.asyncio
async def test_get_pack_by_id(api_client: AsyncClient):
    """GET /packs/{id} returns 200 for existing, 404 for missing."""
    # Create first
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "get-pack", "title": "Get Test"},
    )

    resp = await api_client.get("/api/compendium/packs/get-pack")
    assert resp.status_code == 200
    assert resp.json()["id"] == "get-pack"

    # 404
    resp_missing = await api_client.get("/api/compendium/packs/nonexistent")
    assert resp_missing.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_pack_returns_409(api_client: AsyncClient):
    """Duplicate pack ID returns 409 PACK_ID_CONFLICT."""
    payload = {"id": "dup-pack", "title": "First"}
    await api_client.post("/api/compendium/packs", json=payload)
    resp = await api_client.post("/api/compendium/packs", json=payload)
    assert resp.status_code == 409
    assert "PACK_ID_CONFLICT" in resp.json()["detail"]["error"]


# =========================================================================
# Definition CRUD through HTTP
# =========================================================================
@pytest.mark.asyncio
async def test_definition_create_and_get(api_client: AsyncClient):
    """POST + GET definition via HTTP."""
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "def-pack", "title": "Def Pack"},
    )

    now = datetime.now(timezone.utc).isoformat()
    create_resp = await api_client.post(
        "/api/compendium/definitions",
        json={
            "family": "monster",
            "id": "http-monster",
            "slug": "goblin-http",
            "name": "HTTP Goblin",
            "lifecycle_state": "draft",
            "content_version": 1,
            "schema_version": 1,
            "pack_id": "def-pack",
            "provenance_source": "tests",
            "provenance_author": "test-suite",
            "provenance_updated_at": now,
            "challenge_rating": 0.25,
            "armor_class": 15,
            "hit_points_formula": "2d6",
            "action_operation_specs": [],
        },
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["id"] == "http-monster"

    # GET
    get_resp = await api_client.get("/api/compendium/definitions/http-monster")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "HTTP Goblin"


@pytest.mark.asyncio
async def test_definition_update_and_publish(api_client: AsyncClient):
    """PUT update then POST publish through HTTP."""
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "up-pack", "title": "Update Pack"},
    )

    now = datetime.now(timezone.utc).isoformat()
    await api_client.post(
        "/api/compendium/definitions",
        json={
            "family": "spell",
            "id": "http-spell",
            "slug": "fireball-http",
            "name": "HTTP Fireball",
            "lifecycle_state": "draft",
            "content_version": 1,
            "schema_version": 1,
            "pack_id": "up-pack",
            "provenance_source": "tests",
            "provenance_updated_at": now,
            "level": 3,
            "school": "evocation",
            "casting_time": "1 action",
            "action_operation_specs": [],
        },
    )

    # Update
    update_resp = await api_client.put(
        "/api/compendium/definitions/http-spell",
        json={
            "expected_content_version": 1,
            "updates": {"name": "Greater HTTP Fireball"},
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Greater HTTP Fireball"
    assert update_resp.json()["content_version"] == 2

    # Publish
    pub_resp = await api_client.post(
        "/api/compendium/definitions/http-spell/publish",
        json={},
    )
    assert pub_resp.status_code == 200
    assert pub_resp.json()["lifecycle_state"] == "published"

    # Attempt update after publish → 409
    stale_resp = await api_client.put(
        "/api/compendium/definitions/http-spell",
        json={
            "expected_content_version": 3,
            "updates": {"name": "Should Fail"},
        },
    )
    assert stale_resp.status_code == 409
    assert "INVALID_LIFECYCLE_TRANSITION" in stale_resp.json()["detail"]["error"]


@pytest.mark.asyncio
async def test_definition_delete(api_client: AsyncClient):
    """DELETE definition returns 204 then GET returns 404."""
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "del-pack", "title": "Delete Pack"},
    )

    now = datetime.now(timezone.utc).isoformat()
    await api_client.post(
        "/api/compendium/definitions",
        json={
            "family": "lore",
            "id": "http-lore",
            "slug": "deletable",
            "name": "Deletable Lore",
            "lifecycle_state": "draft",
            "content_version": 1,
            "schema_version": 1,
            "pack_id": "del-pack",
            "provenance_source": "tests",
            "provenance_updated_at": now,
            "lore_type": "faction",
            "rich_text_content": "Test content",
        },
    )

    del_resp = await api_client.delete(
        "/api/compendium/definitions/http-lore?expected_content_version=1"
    )
    assert del_resp.status_code == 204

    # Gone
    gone_resp = await api_client.get("/api/compendium/definitions/http-lore")
    assert gone_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_definitions_by_pack(api_client: AsyncClient):
    """GET /definitions?pack_id= returns filtered list."""
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "list-pack", "title": "List Pack"},
    )

    now = datetime.now(timezone.utc).isoformat()
    await api_client.post(
        "/api/compendium/definitions",
        json={
            "family": "monster",
            "id": "list-monster",
            "slug": "list-goblin",
            "name": "List Goblin",
            "lifecycle_state": "draft",
            "content_version": 1,
            "schema_version": 1,
            "pack_id": "list-pack",
            "provenance_source": "tests",
            "provenance_updated_at": now,
            "challenge_rating": 0.5,
            "armor_class": 12,
            "hit_points_formula": "3d8",
            "action_operation_specs": [],
        },
    )

    resp = await api_client.get("/api/compendium/definitions?pack_id=list-pack")
    assert resp.status_code == 200
    defs = resp.json()
    assert len(defs) >= 1


# =========================================================================
# Search Endpoint through HTTP
# =========================================================================
@pytest.mark.asyncio
async def test_search_endpoint(api_client: AsyncClient):
    """GET /search returns matching index documents."""
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "search-pack", "title": "Search Pack"},
    )

    now = datetime.now(timezone.utc).isoformat()
    await api_client.post(
        "/api/compendium/definitions",
        json={
            "family": "monster",
            "id": "search-mon",
            "slug": "search-troll",
            "name": "Searchable Troll",
            "lifecycle_state": "draft",
            "content_version": 1,
            "schema_version": 1,
            "pack_id": "search-pack",
            "provenance_source": "tests",
            "provenance_updated_at": now,
            "challenge_rating": 5.0,
            "armor_class": 15,
            "hit_points_formula": "8d10+40",
            "action_operation_specs": [],
        },
    )

    resp = await api_client.get("/api/compendium/search?q=troll")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["name"] == "Searchable Troll"


# =========================================================================
# Supersede through HTTP
# =========================================================================
@pytest.mark.asyncio
async def test_supersede_through_http(api_client: AsyncClient):
    """POST /definitions/{id}/supersede returns the superseded entity."""
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "sup-pack", "title": "Supersede Pack"},
    )

    now = datetime.now(timezone.utc).isoformat()
    for def_id, slug in [("sup-old", "old-monster"), ("sup-new", "new-monster")]:
        await api_client.post(
            "/api/compendium/definitions",
            json={
                "family": "monster",
                "id": def_id,
                "slug": slug,
                "name": f"Monster {def_id}",
                "lifecycle_state": "draft",
                "content_version": 1,
                "schema_version": 1,
                "pack_id": "sup-pack",
                "provenance_source": "tests",
                "provenance_updated_at": now,
                "challenge_rating": 1.0,
                "armor_class": 13,
                "hit_points_formula": "4d8",
                "action_operation_specs": [],
            },
        )
        await api_client.post(f"/api/compendium/definitions/{def_id}/publish", json={})

    resp = await api_client.post(
        "/api/compendium/definitions/sup-old/supersede",
        json={"new_definition_id": "sup-new"},
    )
    assert resp.status_code == 200
    assert resp.json()["lifecycle_state"] == "superseded"
