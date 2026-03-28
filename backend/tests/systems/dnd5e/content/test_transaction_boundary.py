from datetime import datetime, timezone

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import Base
from src.systems.dnd5e.content.domain.definition_models import MonsterDefinition
from src.systems.dnd5e.content.domain.link_models import LinkedEntryReference, RelationKind, ResolveMode
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import LifecycleState
from src.systems.dnd5e.content.infrastructure.orm import (
    CompendiumDefinitionModel,
    ContentPackModel,
    LinkedEntryModel,
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
        Base.metadata.tables[CompendiumDefinitionModel.__tablename__].create(
            sync_conn)
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
        title="V05 Tx Pack",
        lifecycle_state=LifecycleState.DRAFT,
        is_homebrew=True,
        created_at=now,
        updated_at=now,
    )


def _build_monster(definition_id: str, pack_id: str) -> MonsterDefinition:
    return MonsterDefinition(
        id=definition_id,
        slug="goblin",
        name="Goblin",
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


@pytest.mark.asyncio
async def test_uow_rolls_back_definition_insert_when_link_write_crashes(db_session):
    uow = CompendiumUnitOfWork(db_session)

    source_definition_id = "def-source"

    with pytest.raises(IntegrityError):
        async with uow:
            await uow.packs.create(_build_pack("pack-tx"))
            await uow.definitions.upsert(_build_monster(source_definition_id, "pack-tx"))
            await uow.links.create(
                LinkedEntryReference(
                    id="link-1",
                    source_definition_id=source_definition_id,
                    source_path="$.action_operation_specs[0]",
                    target_definition_id="def-missing-target",
                    target_family="ability",
                    relation_kind=RelationKind.GRANTS,
                    required=True,
                    resolve_mode=ResolveMode.STRICT,
                )
            )
            await uow.commit()

    persisted = await uow.definitions.get_by_id(source_definition_id)
    assert persisted is None
