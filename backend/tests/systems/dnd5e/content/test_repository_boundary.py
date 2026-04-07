from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = [pytest.mark.v05, pytest.mark.gold]
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import Base
from src.systems.dnd5e.content.domain.definition_models import MonsterDefinition
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import LifecycleState
from src.systems.dnd5e.content.infrastructure.orm import (
    CompendiumDefinitionModel,
    ContentPackModel,
    LinkedEntryModel,
    SearchIndexModel,
)
from src.systems.dnd5e.content.infrastructure.repositories import (
    ContentPackRepository,
    DefinitionRepository,
)


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


def _build_pack(pack_id: str) -> ContentPackRecord:
    now = datetime.now(timezone.utc)
    return ContentPackRecord(
        id=pack_id,
        author_user_id="user-1",
        title="V05 Core Pack",
        lifecycle_state=LifecycleState.DRAFT,
        is_homebrew=True,
        pack_key="v05-core-pack",
        compatibility_target="5.1",
        created_at=now,
        updated_at=now,
    )


def _build_monster(*, definition_id: str, pack_id: str, slug: str, version: int) -> MonsterDefinition:
    return MonsterDefinition(
        id=definition_id,
        slug=slug,
        name="Goblin",
        lifecycle_state=LifecycleState.DRAFT,
        content_version=version,
        schema_version=1,
        pack_id=pack_id,
        provenance_source="tests",
        provenance_author="test-suite",
        provenance_updated_at=datetime.now(timezone.utc),
        challenge_rating=0.25,
        armor_class=15,
        hit_points_formula="2d6",
        action_operation_specs=[],
    )


@pytest.mark.asyncio
async def test_definition_repository_returns_domain_models_not_orm(db_session):
    packs = ContentPackRepository(db_session)
    definitions = DefinitionRepository(db_session)

    pack = await packs.create(_build_pack("pack-1"))
    definition = await definitions.upsert(
        _build_monster(definition_id="def-1", pack_id=pack.id,
                       slug="goblin", version=1)
    )

    assert isinstance(definition, MonsterDefinition)
    assert not isinstance(definition, CompendiumDefinitionModel)

    by_pack = await definitions.get_by_pack_id(pack.id)
    assert len(by_pack) == 1
    assert isinstance(by_pack[0], MonsterDefinition)


@pytest.mark.asyncio
async def test_definition_repository_get_versions_returns_descending_versions(db_session):
    packs = ContentPackRepository(db_session)
    definitions = DefinitionRepository(db_session)

    pack = await packs.create(_build_pack("pack-2"))
    await definitions.upsert(
        _build_monster(definition_id="def-v1", pack_id=pack.id,
                       slug="goblin", version=1)
    )
    await definitions.upsert(
        _build_monster(definition_id="def-v2", pack_id=pack.id,
                       slug="goblin", version=2)
    )

    versions = await definitions.get_versions("def-v1")

    assert [item.content_version for item in versions] == [2, 1]
    assert all(isinstance(item, MonsterDefinition) for item in versions)


def test_api_layer_does_not_import_repositories_directly():
    repo_root = Path(__file__).resolve().parents[4]
    router_path = repo_root / "src" / "systems" / "dnd5e" / "content" / "api" / "router.py"
    router_source = router_path.read_text(encoding="utf-8")

    assert "content.infrastructure.repositories" not in router_source


def test_infrastructure_layer_does_not_import_policy_modules():
    repo_root = Path(__file__).resolve().parents[4]
    infra_path = repo_root / "src" / "systems" / "dnd5e" / "content" / "infrastructure"

    for py_file in infra_path.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "content.policies" not in source
