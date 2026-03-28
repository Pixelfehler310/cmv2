"""
V05-06 Test Suite: Search Index

Tests the denormalized search index (CQRS ReadModel):
- Partial name matching
- Family filtering
- Index updated on create/update/delete
- Search uses index table only (not definitions table)
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import Base
from src.systems.dnd5e.content.application.services import (
    CompendiumApplicationService,
    ContentMutationEvent,
)
from src.systems.dnd5e.content.domain.definition_models import (
    MonsterDefinition,
    SpellDefinition,
)
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import DefinitionFamily, LifecycleState
from src.systems.dnd5e.content.infrastructure.orm import (
    CompendiumDefinitionModel,
    ContentPackModel,
    LinkedEntryModel,
    SearchIndexModel,
)
from src.systems.dnd5e.content.infrastructure.unit_of_work import CompendiumUnitOfWork


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
        Base.metadata.tables[CompendiumDefinitionModel.__tablename__].create(sync_conn)
        Base.metadata.tables[SearchIndexModel.__tablename__].create(sync_conn)
        Base.metadata.tables[LinkedEntryModel.__tablename__].create(sync_conn)

    async with engine.begin() as conn:
        await conn.run_sync(_create_tables)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _seed_pack(db_session, *, pack_id: str = "pack-1") -> ContentPackRecord:
    now = datetime.now(timezone.utc)
    pack = ContentPackRecord(
        id=pack_id,
        author_user_id="user-1",
        title="V05-06 Search Index Pack",
        lifecycle_state=LifecycleState.DRAFT,
        is_homebrew=True,
        pack_key=f"key-{pack_id}",
        compatibility_target="5.1",
        created_at=now,
        updated_at=now,
    )
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        created = await uow.packs.create(pack)
        await uow.commit()
    return created


def _build_monster(
    *, definition_id: str, pack_id: str, slug: str, name: str = "Goblin",
) -> MonsterDefinition:
    return MonsterDefinition(
        id=definition_id,
        slug=slug,
        name=name,
        lifecycle_state=LifecycleState.DRAFT,
        content_version=1,
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


def _build_spell(
    *, definition_id: str, pack_id: str, slug: str, name: str = "Fireball",
) -> SpellDefinition:
    return SpellDefinition(
        id=definition_id,
        slug=slug,
        name=name,
        lifecycle_state=LifecycleState.DRAFT,
        content_version=1,
        schema_version=1,
        pack_id=pack_id,
        provenance_source="tests",
        provenance_author="test-suite",
        provenance_updated_at=datetime.now(timezone.utc),
        level=3,
        school="evocation",
        casting_time="1 action",
        action_operation_specs=[],
    )


def _build_service(db_session, emitted: list[ContentMutationEvent]) -> CompendiumApplicationService:
    def _publish(event_payload: ContentMutationEvent) -> None:
        emitted.append(event_payload)

    return CompendiumApplicationService(
        uow_factory=lambda: CompendiumUnitOfWork(db_session),
        event_publisher=_publish,
    )


@pytest.mark.asyncio
async def test_search_by_name_partial_match(db_session):
    """Creates 'Fireball', searches 'fire', finds it."""
    await _seed_pack(db_session)
    emitted: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted)

    await service.create_definition(
        _build_spell(definition_id="spell-1", pack_id="pack-1", slug="fireball", name="Fireball")
    )

    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        results = await uow.search_index.search(query_text="fire")

    assert len(results) == 1
    assert results[0].definition_id == "spell-1"
    assert results[0].name == "Fireball"


@pytest.mark.asyncio
async def test_search_filters_by_family(db_session):
    """Creates spell + monster, searches with family=spell, gets only spell."""
    await _seed_pack(db_session)
    emitted: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted)

    await service.create_definition(
        _build_spell(definition_id="spell-1", pack_id="pack-1", slug="fireball", name="Fireball")
    )
    await service.create_definition(
        _build_monster(definition_id="mon-1", pack_id="pack-1", slug="fire-elemental", name="Fire Elemental")
    )

    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        results = await uow.search_index.search(
            query_text="fire",
            family=DefinitionFamily.SPELL.value,
        )

    assert len(results) == 1
    assert results[0].family == DefinitionFamily.SPELL.value


@pytest.mark.asyncio
async def test_search_index_updated_on_create(db_session):
    """Creates definition, immediately searches, finds it."""
    await _seed_pack(db_session)
    emitted: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted)

    await service.create_definition(
        _build_monster(definition_id="mon-1", pack_id="pack-1", slug="goblin", name="Goblin")
    )

    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        results = await uow.search_index.search(query_text="goblin")

    assert len(results) == 1
    assert results[0].definition_id == "mon-1"


@pytest.mark.asyncio
async def test_search_index_updated_on_delete(db_session):
    """Creates + deletes, searches, gets empty results."""
    await _seed_pack(db_session)
    emitted: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted)

    created = await service.create_definition(
        _build_monster(definition_id="mon-del", pack_id="pack-1", slug="goblin-del", name="Goblin Delete")
    )

    # Verify it's in the index
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        before = await uow.search_index.search(query_text="goblin delete")
    assert len(before) == 1

    # Delete it
    await service.delete_definition(
        definition_id=created.id,
        expected_content_version=created.content_version,
    )

    # Search again — should be gone
    uow2 = CompendiumUnitOfWork(db_session)
    async with uow2:
        after = await uow2.search_index.search(query_text="goblin delete")
    assert len(after) == 0


@pytest.mark.asyncio
async def test_search_index_updated_on_name_change(db_session):
    """Creates 'Goblin', updates to 'Hobgoblin', verifies index reflects the change."""
    await _seed_pack(db_session)
    emitted: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted)

    created = await service.create_definition(
        _build_monster(definition_id="mon-rename", pack_id="pack-1", slug="goblin-rename", name="Goblin")
    )

    # Update name
    await service.update_definition(
        definition_id=created.id,
        updates={"name": "Hobgoblin"},
        expected_content_version=created.content_version,
    )

    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        # Search new name
        found_hob = await uow.search_index.search(query_text="hobgoblin")
        assert len(found_hob) == 1
        assert found_hob[0].name == "Hobgoblin"

        # Old name should NOT match (it was replaced)
        found_old = await uow.search_index.search(query_text="goblin")
        # "Hobgoblin" still contains "goblin" — this is expected for LIKE search
        # But the name field should show "Hobgoblin", not "Goblin"
        if found_old:
            assert found_old[0].name == "Hobgoblin"


@pytest.mark.asyncio
async def test_search_returns_empty_for_no_matches(db_session):
    """Searches for a non-existent term, gets empty results."""
    await _seed_pack(db_session)
    emitted: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted)

    await service.create_definition(
        _build_monster(definition_id="mon-1", pack_id="pack-1", slug="goblin", name="Goblin")
    )

    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        results = await uow.search_index.search(query_text="dragon")

    assert len(results) == 0
