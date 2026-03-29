"""
V05-06 Test Suite: Link Resolution

Tests the recursive graph resolver for LinkedEntryReference traversal:
- Forward link resolution with tree building
- Reverse link resolution
- Cycle detection (A → B → A)
- Broken link marking (missing targets)
- Replacement chain walking
- Deep graph traversal (depth limits)
"""

from datetime import datetime, timezone

import pytest

pytestmark = [pytest.mark.v05, pytest.mark.gold]
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import Base
from src.systems.dnd5e.content.application.resolution import (
    LinkStatus,
    LinkedEntryResolutionService,
)
from src.systems.dnd5e.content.domain.definition_models import (
    MonsterDefinition,
    SpellDefinition,
)
from src.systems.dnd5e.content.domain.errors import GraphCycleError
from src.systems.dnd5e.content.domain.link_models import (
    LinkedEntryReference,
    RelationKind,
    ResolveMode,
)
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import (
    DefinitionFamily,
    LifecycleState,
)
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
        title="V05-06 Link Resolution Pack",
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
        lifecycle_state=LifecycleState.PUBLISHED,
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
        lifecycle_state=LifecycleState.PUBLISHED,
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


def _build_link(
    *, link_id: str, source_id: str, target_id: str,
    relation_kind: RelationKind = RelationKind.GRANTS,
    target_family: str = "monster",
) -> LinkedEntryReference:
    return LinkedEntryReference(
        id=link_id,
        source_definition_id=source_id,
        source_path="$",
        target_definition_id=target_id,
        target_family=target_family,
        relation_kind=relation_kind,
        required=True,
        resolve_mode=ResolveMode.STRICT,
    )


@pytest.mark.asyncio
async def test_forward_link_resolution_returns_tree(db_session):
    """Creates A → B → C graph, resolves from A, gets full tree."""
    await _seed_pack(db_session)
    uow = CompendiumUnitOfWork(db_session)

    async with uow:
        await uow.definitions.upsert(_build_monster(definition_id="A", pack_id="pack-1", slug="goblin-a", name="Goblin A"))
        await uow.definitions.upsert(_build_monster(definition_id="B", pack_id="pack-1", slug="goblin-b", name="Goblin B"))
        await uow.definitions.upsert(_build_monster(definition_id="C", pack_id="pack-1", slug="goblin-c", name="Goblin C"))
        await uow.links.create(_build_link(link_id="link-ab", source_id="A", target_id="B"))
        await uow.links.create(_build_link(link_id="link-bc", source_id="B", target_id="C"))
        await uow.commit()

    resolver = LinkedEntryResolutionService()
    async with CompendiumUnitOfWork(db_session) as uow2:
        tree = await resolver.resolve_forward_links("A", uow2)

    assert tree.root_definition_id == "A"
    assert len(tree.links) == 2
    assert all(link.status == LinkStatus.RESOLVED for link in tree.links)
    assert not tree.cycle_detected
    assert not tree.broken_links

    # Verify we found both links in the tree
    target_ids = {link.target_id for link in tree.links}
    assert target_ids == {"B", "C"}


@pytest.mark.asyncio
async def test_reverse_link_resolution(db_session):
    """Creates A → B, resolves reverse from B, finds A."""
    await _seed_pack(db_session)
    uow = CompendiumUnitOfWork(db_session)

    async with uow:
        await uow.definitions.upsert(_build_monster(definition_id="A", pack_id="pack-1", slug="goblin-a", name="Goblin A"))
        await uow.definitions.upsert(_build_monster(definition_id="B", pack_id="pack-1", slug="goblin-b", name="Goblin B"))
        await uow.links.create(_build_link(link_id="link-ab", source_id="A", target_id="B"))
        await uow.commit()

    resolver = LinkedEntryResolutionService()
    async with CompendiumUnitOfWork(db_session) as uow2:
        reverse = await resolver.resolve_reverse_links("B", uow2)

    assert len(reverse) == 1
    assert reverse[0].source_id == "A"
    assert reverse[0].target_id == "B"
    assert reverse[0].status == LinkStatus.RESOLVED


@pytest.mark.asyncio
async def test_cycle_detection_marks_tree_without_crashing(db_session):
    """Creates A → B → A circular graph, asserts cycle is detected on tree."""
    await _seed_pack(db_session)
    uow = CompendiumUnitOfWork(db_session)

    async with uow:
        await uow.definitions.upsert(_build_monster(definition_id="A", pack_id="pack-1", slug="cycle-a", name="Cycle A"))
        await uow.definitions.upsert(_build_monster(definition_id="B", pack_id="pack-1", slug="cycle-b", name="Cycle B"))
        await uow.links.create(_build_link(link_id="link-ab", source_id="A", target_id="B"))
        await uow.links.create(_build_link(link_id="link-ba", source_id="B", target_id="A"))
        await uow.commit()

    resolver = LinkedEntryResolutionService()
    async with CompendiumUnitOfWork(db_session) as uow2:
        tree = await resolver.resolve_forward_links("A", uow2)

    # Cycle is marked on the tree but does NOT crash
    assert tree.cycle_detected is True


@pytest.mark.asyncio
async def test_broken_link_marked_not_crashed(db_session):
    """Creates A → B, deletes B bypassing FK, resolves from A — broken link marker."""
    await _seed_pack(db_session)
    uow = CompendiumUnitOfWork(db_session)

    async with uow:
        await uow.definitions.upsert(_build_monster(definition_id="A", pack_id="pack-1", slug="broken-a", name="Broken A"))
        await uow.definitions.upsert(_build_monster(definition_id="B", pack_id="pack-1", slug="broken-b", name="Broken B"))
        await uow.links.create(_build_link(link_id="link-ab", source_id="A", target_id="B"))
        await uow.commit()

    # Bypass FK constraints and delete B directly to simulate orphaned link
    # (This can happen in production via bulk imports, migrations, or manual SQL)
    from sqlalchemy import text
    await db_session.execute(text("PRAGMA foreign_keys=OFF"))
    await db_session.execute(text("DELETE FROM dnd5e_compendium_definitions WHERE id = 'B'"))
    await db_session.execute(text("DELETE FROM dnd5e_search_index WHERE definition_id = 'B'"))
    await db_session.commit()
    await db_session.execute(text("PRAGMA foreign_keys=ON"))

    resolver = LinkedEntryResolutionService()
    async with CompendiumUnitOfWork(db_session) as uow3:
        tree = await resolver.resolve_forward_links("A", uow3)

    # The resolver does NOT crash; instead it marks the broken link
    broken = [link for link in tree.links if link.status == LinkStatus.BROKEN]
    assert len(broken) == 1
    assert "B" in tree.broken_links


@pytest.mark.asyncio
async def test_replacement_chain_resolution(db_session):
    """Creates A superseded by B superseded by C, resolves chain from A to terminal C."""
    await _seed_pack(db_session)
    uow = CompendiumUnitOfWork(db_session)

    async with uow:
        await uow.definitions.upsert(_build_monster(definition_id="A", pack_id="pack-1", slug="chain-a", name="Chain A"))
        await uow.definitions.upsert(_build_monster(definition_id="B", pack_id="pack-1", slug="chain-b", name="Chain B"))
        await uow.definitions.upsert(_build_monster(definition_id="C", pack_id="pack-1", slug="chain-c", name="Chain C"))
        await uow.links.create(_build_link(
            link_id="repl-ab", source_id="A", target_id="B",
            relation_kind=RelationKind.REPLACEMENT
        ))
        await uow.links.create(_build_link(
            link_id="repl-bc", source_id="B", target_id="C",
            relation_kind=RelationKind.REPLACEMENT
        ))
        await uow.commit()

    resolver = LinkedEntryResolutionService()
    async with CompendiumUnitOfWork(db_session) as uow2:
        chain = await resolver.resolve_replacement_chain("A", uow2)

    assert chain == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_deep_graph_traversal_respects_depth_limit(db_session):
    """12 levels deep — verifies no stack overflow and respects MAX_TRAVERSAL_DEPTH."""
    await _seed_pack(db_session)
    depth = 12
    uow = CompendiumUnitOfWork(db_session)

    async with uow:
        for i in range(depth):
            await uow.definitions.upsert(
                _build_monster(
                    definition_id=f"deep-{i}",
                    pack_id="pack-1",
                    slug=f"deep-{i}",
                    name=f"Deep {i}",
                )
            )
        for i in range(depth - 1):
            await uow.links.create(
                _build_link(
                    link_id=f"link-deep-{i}",
                    source_id=f"deep-{i}",
                    target_id=f"deep-{i + 1}",
                )
            )
        await uow.commit()

    resolver = LinkedEntryResolutionService()
    async with CompendiumUnitOfWork(db_session) as uow2:
        tree = await resolver.resolve_forward_links("deep-0", uow2, max_depth=5)

    # Should stop at depth limit, not traverse all 12
    assert len(tree.links) < depth - 1
    assert not tree.cycle_detected
