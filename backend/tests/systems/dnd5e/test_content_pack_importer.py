import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.database import Base
from src.systems.dnd5e.lib.content_models import (
    AbilityBindingRecord,
    ActionDefinitionRecord,
    EffectDefinitionRecord,
)
from src.systems.dnd5e.services.content_pack_importer import ContentPackImporter


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    def _create_tables(sync_conn):
        Base.metadata.tables[ActionDefinitionRecord.__tablename__].create(
            sync_conn)
        Base.metadata.tables[AbilityBindingRecord.__tablename__].create(
            sync_conn)
        Base.metadata.tables[EffectDefinitionRecord.__tablename__].create(
            sync_conn)

    async with engine.begin() as conn:
        await conn.run_sync(_create_tables)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_import_content_pack_success(db_session):
    importer = ContentPackImporter()
    result = await importer.import_content_pack(
        db_session,
        payload={
            "pack_id": "core",
            "system": "dnd5e",
            "version": "1",
            "actions": [
                {
                    "action_id": "basic_attack",
                    "name": "Basic Attack",
                    "effect_intents": [{"effect_id": "bleed"}],
                }
            ],
            "abilities": [
                {
                    "binding_id": "goblin_basic_attack",
                    "action_id": "basic_attack",
                    "actor_template_id": "goblin",
                }
            ],
            "effects": [
                {
                    "effect_id": "bleed",
                    "name": "Bleed",
                    "metadata": {"content_version": "1"},
                }
            ],
        },
    )

    assert result["status"] == "success"
    assert result["summary"]["actions"]["inserted"] == 1
    assert result["summary"]["abilities"]["inserted"] == 1
    assert result["summary"]["effects"]["inserted"] == 1


@pytest.mark.asyncio
async def test_import_content_pack_semantic_validation_error(db_session):
    importer = ContentPackImporter()
    result = await importer.import_content_pack(
        db_session,
        payload={
            "pack_id": "broken",
            "system": "dnd5e",
            "version": "1",
            "abilities": [
                {
                    "binding_id": "broken_binding",
                    "action_id": "missing_action",
                    "actor_template_id": "goblin",
                }
            ],
        },
    )

    assert result["status"] == "failed"
    assert result["error"] == "semantic_validation_failed"
    assert any(
        "unknown_action:missing_action" in err for err in result["semantic_errors"])


@pytest.mark.asyncio
async def test_conflict_policy_reject_conflict(db_session):
    importer = ContentPackImporter()
    base = {
        "pack_id": "core",
        "system": "dnd5e",
        "version": "1",
        "actions": [{"action_id": "dup_action", "name": "Original", "content_version": "1"}],
    }

    await importer.import_content_pack(db_session, payload=base)
    result = await importer.import_content_pack(
        db_session,
        payload={
            **base,
            "version": "2",
            "actions": [{"action_id": "dup_action", "name": "Changed", "content_version": "2"}],
        },
        conflict_policy="reject_conflict",
    )

    assert result["summary"]["actions"]["conflicts"] == 1
    stmt = select(ActionDefinitionRecord).where(
        ActionDefinitionRecord.action_id == "dup_action")
    row = (await db_session.execute(stmt)).scalar_one()
    assert row.name == "Original"


@pytest.mark.asyncio
async def test_conflict_policy_overwrite_if_newer(db_session):
    importer = ContentPackImporter()
    await importer.import_content_pack(
        db_session,
        payload={
            "pack_id": "core",
            "system": "dnd5e",
            "version": "1",
            "actions": [{"action_id": "upd_action", "name": "Old", "content_version": "1"}],
        },
    )

    result = await importer.import_content_pack(
        db_session,
        payload={
            "pack_id": "core",
            "system": "dnd5e",
            "version": "2",
            "actions": [{"action_id": "upd_action", "name": "New", "content_version": "2"}],
        },
        conflict_policy="overwrite_if_newer",
    )

    assert result["summary"]["actions"]["updated"] == 1
    stmt = select(ActionDefinitionRecord).where(
        ActionDefinitionRecord.action_id == "upd_action")
    row = (await db_session.execute(stmt)).scalar_one()
    assert row.name == "New"


@pytest.mark.asyncio
async def test_conflict_policy_fork_namespace(db_session):
    importer = ContentPackImporter()
    await importer.import_content_pack(
        db_session,
        payload={
            "pack_id": "core",
            "system": "dnd5e",
            "version": "1",
            "actions": [{"action_id": "fork_action", "name": "Original", "content_version": "1"}],
        },
    )

    result = await importer.import_content_pack(
        db_session,
        payload={
            "pack_id": "modpack",
            "system": "dnd5e",
            "version": "2",
            "actions": [{"action_id": "fork_action", "name": "Modded", "content_version": "2"}],
        },
        conflict_policy="fork_namespace",
        namespace="mod_ns",
    )

    assert result["summary"]["actions"]["forked"] == 1
    count_stmt = select(func.count()).select_from(ActionDefinitionRecord)
    total = (await db_session.execute(count_stmt)).scalar_one()
    assert total == 2

    forked_stmt = select(ActionDefinitionRecord).where(
        ActionDefinitionRecord.action_id.like("mod_ns::fork_action%"))
    forked = (await db_session.execute(forked_stmt)).scalar_one()
    assert forked.name == "Modded"
