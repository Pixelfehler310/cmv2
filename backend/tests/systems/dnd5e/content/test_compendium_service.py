from datetime import datetime, timezone

import pytest

pytestmark = [pytest.mark.v05, pytest.mark.gold]
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import Base
from src.systems.dnd5e.content.application.services import (
    CompendiumApplicationService,
    ContentMutationEvent,
)
from src.systems.dnd5e.content.domain.definition_models import MonsterDefinition
from src.systems.dnd5e.content.domain.errors import (
    DefinitionNotFoundError,
    DuplicateDefinitionSlugError,
    IllegalStateDependencyError,
    ImmutableDefinitionError,
    ReplacementCycleError,
    VersionMismatchError,
)
from src.systems.dnd5e.content.domain.link_models import (
    LinkedEntryReference,
    RelationKind,
    ResolveMode,
)
from src.systems.dnd5e.content.domain.invariants import CompendiumErrorCode
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import LifecycleState
from src.systems.dnd5e.content.infrastructure.orm import (
    CompendiumDefinitionModel,
    ContentPackModel,
    LinkedEntryModel,
    SearchIndexModel,
)
from src.systems.dnd5e.content.infrastructure.unit_of_work import CompendiumUnitOfWork
from src.systems.dnd5e.content.policies.lifecycle_transition_policy import ContentLifecycleError


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


async def _seed_pack(db_session, *, pack_id: str = "pack-1") -> ContentPackRecord:
    now = datetime.now(timezone.utc)
    pack = ContentPackRecord(
        id=pack_id,
        author_user_id="user-1",
        title="V05 Service Pack",
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
    *,
    definition_id: str,
    pack_id: str,
    slug: str,
    name: str = "Goblin",
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


def _build_service(db_session, emitted: list[ContentMutationEvent]) -> CompendiumApplicationService:
    def _publish(event_payload: ContentMutationEvent) -> None:
        emitted.append(event_payload)

    return CompendiumApplicationService(
        uow_factory=lambda: CompendiumUnitOfWork(db_session),
        event_publisher=_publish,
    )


@pytest.mark.asyncio
async def test_update_definition_denied_for_published_entity(db_session):
    await _seed_pack(db_session)
    emitted_events: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted_events)

    created = await service.create_definition(
        _build_monster(definition_id="def-pub",
                       pack_id="pack-1", slug="pub-goblin")
    )
    published = await service.publish_definition(definition_id=created.id)

    with pytest.raises(ImmutableDefinitionError) as exc:
        await service.update_definition(
            definition_id=published.id,
            updates={"name": "Goblin Veteran"},
            expected_content_version=published.content_version,
        )

    assert CompendiumErrorCode.INVALID_LIFECYCLE_TRANSITION.value in str(
        exc.value)


@pytest.mark.asyncio
async def test_supersede_definition_sets_replacement_chain_link(db_session):
    await _seed_pack(db_session)
    emitted_events: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted_events)

    old_created = await service.create_definition(
        _build_monster(definition_id="def-old",
                       pack_id="pack-1", slug="goblin-old")
    )
    new_created = await service.create_definition(
        _build_monster(definition_id="def-new",
                       pack_id="pack-1", slug="goblin-new")
    )

    old_published = await service.publish_definition(definition_id=old_created.id)
    await service.publish_definition(definition_id=new_created.id)

    superseded = await service.supersede_definition(
        old_definition_id=old_published.id,
        new_definition_id=new_created.id,
    )

    assert superseded.lifecycle_state == LifecycleState.SUPERSEDED

    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        links = await uow.links.list_by_source_definition_id(old_published.id)

    replacement_links = [
        link for link in links if link.relation_kind.value == "replacement"
    ]
    assert len(replacement_links) == 1
    assert replacement_links[0].target_definition_id == new_created.id


@pytest.mark.asyncio
async def test_publish_definition_emits_event_only_on_success(db_session):
    await _seed_pack(db_session)
    emitted_events: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted_events)

    created = await service.create_definition(
        _build_monster(definition_id="def-event",
                       pack_id="pack-1", slug="event-goblin")
    )

    await service.publish_definition(definition_id=created.id, request_id="req-123")

    published_events = [
        event_payload
        for event_payload in emitted_events
        if event_payload.event_type == "definition_published"
    ]
    assert len(published_events) == 1
    assert published_events[0].definition_id == created.id
    assert published_events[0].request_id == "req-123"

    event_count_before_failure = len(emitted_events)
    with pytest.raises(DefinitionNotFoundError):
        await service.publish_definition(definition_id="missing-definition")
    assert len(emitted_events) == event_count_before_failure


@pytest.mark.asyncio
async def test_update_definition_requires_expected_content_version(db_session):
    await _seed_pack(db_session)
    emitted_events: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted_events)

    created = await service.create_definition(
        _build_monster(definition_id="def-version",
                       pack_id="pack-1", slug="version-goblin")
    )

    with pytest.raises(VersionMismatchError):
        await service.update_definition(
            definition_id=created.id,
            updates={"name": "Goblin Corrected"},
            expected_content_version=created.content_version + 1,
        )

    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        persisted = await uow.definitions.get_by_id(created.id)
    assert persisted is not None
    assert persisted.content_version == created.content_version
    assert persisted.name == created.name


@pytest.mark.asyncio
async def test_delete_definition_hard_delete_draft_only(db_session):
    await _seed_pack(db_session)
    emitted_events: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted_events)

    published_candidate = await service.create_definition(
        _build_monster(definition_id="def-no-delete",
                       pack_id="pack-1", slug="no-delete")
    )
    await service.publish_definition(definition_id=published_candidate.id)

    with pytest.raises(ImmutableDefinitionError):
        await service.delete_definition(
            definition_id=published_candidate.id,
            expected_content_version=2,
        )

    deletable = await service.create_definition(
        _build_monster(definition_id="def-delete",
                       pack_id="pack-1", slug="delete-me")
    )

    await service.delete_definition(
        definition_id=deletable.id,
        expected_content_version=deletable.content_version,
    )

    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        persisted = await uow.definitions.get_by_id(deletable.id)
    assert persisted is None


@pytest.mark.asyncio
async def test_create_definition_denies_duplicate_slug_in_pack_family(db_session):
    await _seed_pack(db_session)
    emitted_events: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted_events)

    await service.create_definition(
        _build_monster(definition_id="def-dup-1",
                       pack_id="pack-1", slug="dup-slug")
    )

    with pytest.raises(DuplicateDefinitionSlugError) as exc:
        await service.create_definition(
            _build_monster(definition_id="def-dup-2",
                           pack_id="pack-1", slug="dup-slug")
        )

    assert CompendiumErrorCode.DUPLICATE_SLUG.value in str(exc.value)


@pytest.mark.asyncio
async def test_supersede_definition_denies_replacement_cycles(db_session):
    await _seed_pack(db_session)
    emitted_events: list[ContentMutationEvent] = []
    service = _build_service(db_session, emitted_events)

    a = await service.create_definition(
        _build_monster(definition_id="def-a", pack_id="pack-1", slug="chain-a")
    )
    b = await service.create_definition(
        _build_monster(definition_id="def-b", pack_id="pack-1", slug="chain-b")
    )
    c = await service.create_definition(
        _build_monster(definition_id="def-c", pack_id="pack-1", slug="chain-c")
    )

    await service.publish_definition(definition_id=a.id)
    await service.publish_definition(definition_id=b.id)
    await service.publish_definition(definition_id=c.id)

    await service.supersede_definition(old_definition_id=a.id, new_definition_id=b.id)
    await service.supersede_definition(old_definition_id=b.id, new_definition_id=c.id)

    with pytest.raises(ReplacementCycleError) as exc:
        await service.supersede_definition(old_definition_id=c.id, new_definition_id=a.id)

    assert CompendiumErrorCode.CYCLE_DETECTED.value in str(exc.value)


@pytest.mark.asyncio
async def test_publish_fails_with_draft_dependency(db_session):
    await _seed_pack(db_session)
    service = _build_service(db_session, [])

    # Create Source (Spell) and Target (Condition)
    source = await service.create_definition(
        _build_monster(definition_id="source-1",
                       pack_id="pack-1", slug="source")
    )
    target = await service.create_definition(
        _build_monster(definition_id="target-1",
                       pack_id="pack-1", slug="target")
    )

    # Manually create a link from source to target
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        await uow.links.create(
            LinkedEntryReference(
                id="link-1",
                source_definition_id=source.id,
                source_path="$.action_operation_specs[0].payload.applied_condition_id",
                target_definition_id=target.id,
                target_family="condition",
                relation_kind=RelationKind.RELATED,
                required=True,
                resolve_mode=ResolveMode.STRICT,
            )
        )
        await uow.commit()

    # Attempt to publish source while target is DRAFT
    with pytest.raises(IllegalStateDependencyError) as exc:
        await service.publish_definition(definition_id=source.id)

    assert "cannot depend on DRAFT target" in str(exc.value)


@pytest.mark.asyncio
async def test_supersede_fails_with_draft_target(db_session):
    await _seed_pack(db_session)
    service = _build_service(db_session, [])

    old_def = await service.create_definition(
        _build_monster(definition_id="old-1", pack_id="pack-1", slug="old")
    )
    new_def = await service.create_definition(
        _build_monster(definition_id="new-1", pack_id="pack-1", slug="new")
    )

    await service.publish_definition(definition_id=old_def.id)
    # new_def remains in DRAFT

    with pytest.raises(ContentLifecycleError) as exc:
        await service.supersede_definition(
            old_definition_id=old_def.id,
            new_definition_id=new_def.id,
        )

    assert "replacement target cannot be in draft state" in str(exc.value)
