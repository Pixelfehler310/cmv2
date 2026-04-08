"""
V05-07 API-Level Integration Tests via FastAPI TestClient.

These tests exercise the HTTP transport layer to close the coverage gap
on the router module and verify the full request → response → error contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base, get_db
from src.systems.dnd5e.content.api.router import router
from src.systems.dnd5e.content.domain.errors import GraphCycleError
from src.systems.dnd5e.content.infrastructure.orm import (
    CompendiumDefinitionModel,
    ContentPackModel,
    LinkedEntryModel,
    SearchIndexModel,
)


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

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

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


@pytest.mark.asyncio
async def test_ability_action_specs_round_trip(api_client: AsyncClient):
    """DND5E-03 integration touch: action specs survive create/get transport."""
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "ability-pack", "title": "Ability Pack"},
    )

    now = datetime.now(timezone.utc).isoformat()
    create_resp = await api_client.post(
        "/api/compendium/definitions",
        json={
            "family": "ability",
            "id": "ability-sneak-attack",
            "slug": "sneak-attack",
            "name": "Sneak Attack",
            "lifecycle_state": "draft",
            "content_version": 1,
            "schema_version": 1,
            "pack_id": "ability-pack",
            "provenance_source": "tests",
            "provenance_updated_at": now,
            "ability_type": "feature",
            "action_operation_specs": [
                {
                    "operation_id": "op-attack",
                    "activation_cost": "action",
                    "targeting_spec": {
                        "type": "single",
                        "range_feet": 5,
                        "max_targets": 1,
                    },
                    "payload": {
                        "operation_type": "attack_roll",
                        "attack_type": "melee_weapon",
                        "damage_instances": [
                            {
                                "value": "1d6",
                                "damage_type": "piercing",
                                "add_stat_modifier": True,
                            }
                        ],
                    },
                }
            ],
            "passive_effects": [
                {
                    "modifier_type": "flat",
                    "target_stat": "initiative",
                    "value": 2,
                    "stack_group": "ability-passive",
                }
            ],
        },
    )
    assert create_resp.status_code == 200

    get_resp = await api_client.get("/api/compendium/definitions/ability-sneak-attack")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["family"] == "ability"
    assert body["action_operation_specs"][0]["payload"]["operation_type"] == "attack_roll"
    assert body["passive_effects"][0]["modifier_type"] == "flat"


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


@pytest.mark.asyncio
async def test_search_endpoint_contract_envelope(api_client: AsyncClient):
    """GET /search supports optional CORE-03 contract envelope fields."""
    await api_client.post(
        "/api/compendium/packs",
        json={"id": "search-pack-contract", "title": "Search Pack Contract"},
    )

    now = datetime.now(timezone.utc).isoformat()
    await api_client.post(
        "/api/compendium/definitions",
        json={
            "family": "monster",
            "id": "search-contract-mon",
            "slug": "search-contract-troll",
            "name": "Contract Troll",
            "lifecycle_state": "draft",
            "content_version": 1,
            "schema_version": 1,
            "pack_id": "search-pack-contract",
            "provenance_source": "tests",
            "provenance_updated_at": now,
            "challenge_rating": 5.0,
            "armor_class": 15,
            "hit_points_formula": "8d10+40",
            "action_operation_specs": [],
        },
    )

    resp = await api_client.get(
        "/api/compendium/search?q=troll&include_contract=true",
        headers={"x-request-id": "req-search-contract"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["request_id"] == "req-search-contract"
    assert body["status"] == "resolved"
    assert isinstance(body["catalog_revision"], int)
    assert body["catalog_revision"] >= 0
    assert "search-contract-mon" in body["affected_definition_ids"]
    assert isinstance(body["payload"], list)


@pytest.mark.asyncio
async def test_replacement_chain_contract_envelope_denied(api_client: AsyncClient):
    """Contract mode returns denied envelope fields on replacement-chain errors."""
    with patch(
        "src.systems.dnd5e.content.application.resolution.LinkedEntryResolutionService.resolve_replacement_chain",
        side_effect=GraphCycleError(definition_id="cycle-a", visited_path=["cycle-a", "cycle-b"]),
    ):
        resp = await api_client.get(
            "/api/compendium/definitions/cycle-a/replacement-chain?include_contract=true",
            headers={"x-request-id": "req-cycle-denied"},
        )

    assert resp.status_code == 400
    body = resp.json()["detail"]
    assert body["request_id"] == "req-cycle-denied"
    assert body["status"] == "denied"
    assert body["reason_code"] == "GRAPH_CYCLE_DETECTED"
    assert isinstance(body["catalog_revision"], int)
    assert body["payload"]["message"]


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
