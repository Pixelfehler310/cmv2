"""
V05 Content Test Infrastructure — Shared Fixtures and Factories.

Provides two DB backends:
- `db_session` (SQLite, fast, every-test default)
- `pg_session` (PostgreSQL via testcontainers, for GIN index / production-parity tests)

Both fixtures create all four V05 tables automatically.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base
from src.systems.dnd5e.content.application.services import (
    CompendiumApplicationService,
    ContentMutationEvent,
)
from src.systems.dnd5e.content.domain.definition_models import (
    MonsterDefinition,
    SpellDefinition,
)
from src.systems.dnd5e.content.domain.link_models import (
    LinkedEntryReference,
    RelationKind,
    ResolveMode,
)
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import LifecycleState
from src.systems.dnd5e.content.infrastructure.orm import (
    CompendiumDefinitionModel,
    ContentPackModel,
    LinkedEntryModel,
    SearchIndexModel,
)
from src.systems.dnd5e.content.infrastructure.unit_of_work import CompendiumUnitOfWork


# ---------------------------------------------------------------------------
# Table list (order matters for FK dependencies)
# ---------------------------------------------------------------------------
_V05_TABLES = [
    ContentPackModel.__tablename__,
    CompendiumDefinitionModel.__tablename__,
    SearchIndexModel.__tablename__,
    LinkedEntryModel.__tablename__,
]


# ---------------------------------------------------------------------------
# SQLite Fixture (fast in-memory, every-test default)
# ---------------------------------------------------------------------------
@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def _create_tables(sync_conn):
        for table_name in _V05_TABLES:
            Base.metadata.tables[table_name].create(sync_conn)

    async with engine.begin() as conn:
        await conn.run_sync(_create_tables)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


# ---------------------------------------------------------------------------
# PostgreSQL Fixture (testcontainers, for GIN / production-parity tests)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def pg_container():
    """Spin up a PostgreSQL 15 container once per test session."""
    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers[postgres] is not installed")

    with PostgresContainer("postgres:15-alpine") as pg:
        yield pg


@pytest.fixture
async def pg_session(pg_container):
    """Per-test PostgreSQL session. Creates tables, yields, rolls back."""
    host = pg_container.get_container_host_ip()
    port = pg_container.get_exposed_port(5432)
    user = pg_container.username
    password = pg_container.password
    dbname = pg_container.dbname

    url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_async_engine(url, echo=False)

    # Create tables from ORM metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    # Tear down — drop all to ensure clean slate per test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Shared Factories
# ---------------------------------------------------------------------------
def build_pack(
    *,
    pack_id: str = "pack-1",
    author_user_id: str = "user-1",
    title: str = "V05 Test Pack",
) -> ContentPackRecord:
    now = datetime.now(timezone.utc)
    return ContentPackRecord(
        id=pack_id,
        author_user_id=author_user_id,
        title=title,
        lifecycle_state=LifecycleState.DRAFT,
        is_homebrew=True,
        pack_key=f"key-{pack_id}",
        compatibility_target="5.1",
        created_at=now,
        updated_at=now,
    )


def build_monster(
    *,
    definition_id: str,
    pack_id: str = "pack-1",
    slug: str | None = None,
    name: str = "Goblin",
    lifecycle_state: LifecycleState = LifecycleState.DRAFT,
) -> MonsterDefinition:
    return MonsterDefinition(
        id=definition_id,
        slug=slug or f"slug-{definition_id}",
        name=name,
        lifecycle_state=lifecycle_state,
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


def build_spell(
    *,
    definition_id: str,
    pack_id: str = "pack-1",
    slug: str | None = None,
    name: str = "Fireball",
    lifecycle_state: LifecycleState = LifecycleState.DRAFT,
) -> SpellDefinition:
    return SpellDefinition(
        id=definition_id,
        slug=slug or f"slug-{definition_id}",
        name=name,
        lifecycle_state=lifecycle_state,
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


def build_link(
    *,
    link_id: str,
    source_id: str,
    target_id: str,
    relation_kind: RelationKind = RelationKind.GRANTS,
    target_family: str = "monster",
    required: bool = True,
) -> LinkedEntryReference:
    return LinkedEntryReference(
        id=link_id,
        source_definition_id=source_id,
        source_path="$",
        target_definition_id=target_id,
        target_family=target_family,
        relation_kind=relation_kind,
        required=required,
        resolve_mode=ResolveMode.STRICT,
    )


def build_compendium_service(
    db_session: AsyncSession,
    emitted: list[ContentMutationEvent] | None = None,
) -> tuple[CompendiumApplicationService, list[ContentMutationEvent]]:
    """Return a service wired to a real UoW and an event capture list."""
    if emitted is None:
        emitted = []

    def _publish(event_payload: ContentMutationEvent) -> None:
        emitted.append(event_payload)

    service = CompendiumApplicationService(
        uow_factory=lambda: CompendiumUnitOfWork(db_session),
        event_publisher=_publish,
    )
    return service, emitted


async def seed_pack(
    db_session: AsyncSession,
    *,
    pack_id: str = "pack-1",
) -> ContentPackRecord:
    """Insert a pack directly via UoW (skips service-level validation)."""
    pack = build_pack(pack_id=pack_id)
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        created = await uow.packs.create(pack)
        await uow.commit()
    return created
