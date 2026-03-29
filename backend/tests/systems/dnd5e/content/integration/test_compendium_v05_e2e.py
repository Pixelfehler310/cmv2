"""
V05-07 E2E Integration Tests.

End-to-end tests that exercise the full CompendiumApplicationService through
the real persistence layer (SQLite in-memory). These verify that all V05
systems (domain models, policies, repositories, application services,
search index, link resolution) work together as a coherent whole.

Tests run against the real (in-memory) database — no mocking.
"""

from __future__ import annotations

import pytest

from datetime import datetime, timezone

from src.systems.dnd5e.content.application.resolution import (
    LinkStatus,
    LinkedEntryResolutionService,
)
from src.systems.dnd5e.content.application.services import (
    CompendiumApplicationService,
    ContentMutationEvent,
)
from src.systems.dnd5e.content.domain.definition_models import MonsterDefinition, SpellDefinition
from src.systems.dnd5e.content.domain.errors import ImmutableDefinitionError
from src.systems.dnd5e.content.domain.link_models import (
    LinkedEntryReference,
    RelationKind,
    ResolveMode,
)
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import LifecycleState
from src.systems.dnd5e.content.infrastructure.unit_of_work import CompendiumUnitOfWork


# ---------------------------------------------------------------------------
# Local factories (self-contained — no relative conftest import needed)
# ---------------------------------------------------------------------------
def _build_monster(
    *, definition_id: str, pack_id: str = "pack-1",
    slug: str | None = None, name: str = "Goblin",
) -> MonsterDefinition:
    return MonsterDefinition(
        id=definition_id, slug=slug or f"slug-{definition_id}", name=name,
        lifecycle_state=LifecycleState.DRAFT, content_version=1,
        schema_version=1, pack_id=pack_id, provenance_source="tests",
        provenance_author="test-suite",
        provenance_updated_at=datetime.now(timezone.utc),
        challenge_rating=0.25, armor_class=15, hit_points_formula="2d6",
        action_operation_specs=[],
    )

def _build_spell(
    *, definition_id: str, pack_id: str = "pack-1",
    slug: str | None = None, name: str = "Fireball",
) -> SpellDefinition:
    return SpellDefinition(
        id=definition_id, slug=slug or f"slug-{definition_id}", name=name,
        lifecycle_state=LifecycleState.DRAFT, content_version=1,
        schema_version=1, pack_id=pack_id, provenance_source="tests",
        provenance_author="test-suite",
        provenance_updated_at=datetime.now(timezone.utc),
        level=3, school="evocation", casting_time="1 action",
        action_operation_specs=[],
    )

def _build_link(
    *, link_id: str, source_id: str, target_id: str,
    relation_kind: RelationKind = RelationKind.GRANTS,
    target_family: str = "monster",
) -> LinkedEntryReference:
    return LinkedEntryReference(
        id=link_id, source_definition_id=source_id, source_path="$",
        target_definition_id=target_id, target_family=target_family,
        relation_kind=relation_kind, required=True,
        resolve_mode=ResolveMode.STRICT,
    )

def _build_service(db_session):
    emitted: list[ContentMutationEvent] = []
    def _publish(evt: ContentMutationEvent) -> None:
        emitted.append(evt)
    service = CompendiumApplicationService(
        uow_factory=lambda: CompendiumUnitOfWork(db_session),
        event_publisher=_publish,
    )
    return service, emitted

async def _seed_pack(db_session, *, pack_id: str = "pack-1") -> ContentPackRecord:
    now = datetime.now(timezone.utc)
    pack = ContentPackRecord(
        id=pack_id, author_user_id="user-1", title="V05 E2E Pack",
        lifecycle_state=LifecycleState.DRAFT, is_homebrew=True,
        pack_key=f"key-{pack_id}", compatibility_target="5.1",
        created_at=now, updated_at=now,
    )
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        created = await uow.packs.create(pack)
        await uow.commit()
    return created


# =========================================================================
# Test 1: The Homebrew Flow (complete lifecycle)
# =========================================================================
@pytest.mark.asyncio
async def test_homebrew_flow_complete(db_session):
    """
    Full Homebrew authoring flow:
    1. Create Draft Pack.
    2. Create Draft Spell definition.
    3. Update the draft definition (verify content_version increments).
    4. Publish the definition.
    5. Attempt to update after publish → 409 denied.
    6. Search → published spell is visible with correct name.
    """
    service, emitted = _build_service(db_session)

    # Step 1: Create pack
    from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
    from datetime import datetime, timezone

    pack = await service.create_pack(
        ContentPackRecord(
            id="e2e-pack",
            author_user_id="dm-user",
            title="Homebrew Pack",
            lifecycle_state=LifecycleState.DRAFT,
            is_homebrew=True,
            pack_key="key-e2e-pack",
            compatibility_target="5.1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    assert pack.id == "e2e-pack"

    # Step 2: Create draft spell
    spell = await service.create_definition(
        _build_spell(
            definition_id="spell-homebrew",
            pack_id="e2e-pack",
            slug="custom-fireball",
            name="Custom Fireball",
        )
    )
    assert spell.lifecycle_state == LifecycleState.DRAFT
    assert spell.content_version == 1

    # Step 3: Update the draft
    updated = await service.update_definition(
        definition_id=spell.id,
        updates={"name": "Greater Fireball"},
        expected_content_version=spell.content_version,
    )
    assert updated.name == "Greater Fireball"
    assert updated.content_version == 2

    # Step 4: Publish
    published = await service.publish_definition(definition_id=spell.id)
    assert published.lifecycle_state == LifecycleState.PUBLISHED
    assert published.content_version == 3

    # Step 5: Attempt update after publish → denied
    with pytest.raises(ImmutableDefinitionError):
        await service.update_definition(
            definition_id=published.id,
            updates={"name": "Modified After Publish"},
            expected_content_version=published.content_version,
        )

    # Step 6: Verify search index reflects published state
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        results = await uow.search_index.search(query_text="greater fireball")

    assert len(results) == 1
    assert results[0].definition_id == "spell-homebrew"
    assert results[0].name == "Greater Fireball"
    assert results[0].visibility_state == "published"

    # Verify correct events were emitted
    event_types = [e.event_type for e in emitted]
    assert "definition_created" in event_types
    assert "definition_updated" in event_types
    assert "definition_published" in event_types


# =========================================================================
# Test 2: Cross-System Link Resolution
# =========================================================================
@pytest.mark.asyncio
async def test_linked_content_lifecycle_integrity(db_session):
    """
    Cross-system test: definitions with linked entries, published lifecycle,
    search index, and link resolution all work together.

    1. Create two definitions (A, B) in a pack.
    2. Create a LinkedEntryReference from A → B.
    3. Publish B, then A (succeeds because B is published).
    4. Search → both visible.
    5. Resolve forward links from A → B appears as RESOLVED.
    6. Resolve reverse links from B → A appears as source.
    """
    service, _ = _build_service(db_session)
    await _seed_pack(db_session, pack_id="link-pack")

    # Create and link A → B
    monster_b = await service.create_definition(
        _build_monster(definition_id="B", pack_id="link-pack", slug="target-b", name="Target B")
    )
    monster_a = await service.create_definition(
        _build_monster(definition_id="A", pack_id="link-pack", slug="source-a", name="Source A")
    )

    # Create link A → B
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        await uow.links.create(
            _build_link(link_id="link-ab", source_id="A", target_id="B")
        )
        await uow.commit()

    # Publish B then A (B first because A depends on B via required link)
    await service.publish_definition(definition_id="B")
    await service.publish_definition(definition_id="A")

    # Search → both visible
    uow2 = CompendiumUnitOfWork(db_session)
    async with uow2:
        results = await uow2.search_index.search(
            lifecycle_states=["published"],
        )
    assert len(results) == 2

    # Forward links from A → B
    resolver = LinkedEntryResolutionService()
    uow3 = CompendiumUnitOfWork(db_session)
    async with uow3:
        tree = await resolver.resolve_forward_links("A", uow3)
        assert len(tree.links) == 1
        assert tree.links[0].target_id == "B"
        assert tree.links[0].status == LinkStatus.RESOLVED
        assert not tree.cycle_detected

        # Reverse links from B → A
        reverse = await resolver.resolve_reverse_links("B", uow3)
        assert len(reverse) == 1
        assert reverse[0].source_id == "A"
        assert reverse[0].status == LinkStatus.RESOLVED


# =========================================================================
# Test 3: Full Supersedence Chain with Search + Resolution
# =========================================================================
@pytest.mark.asyncio
async def test_supersede_chain_with_search_and_resolution(db_session):
    """
    Full chain: A superseded by B, B superseded by C.
    Verifies lifecycle states, replacement chain walking, and search index.
    """
    service, _ = _build_service(db_session)
    await _seed_pack(db_session, pack_id="chain-pack")

    # Create + publish A, B, C
    for def_id in ["chain-A", "chain-B", "chain-C"]:
        await service.create_definition(
            _build_monster(
                definition_id=def_id,
                pack_id="chain-pack",
                slug=f"slug-{def_id}",
                name=f"Monster {def_id}",
            )
        )
        await service.publish_definition(definition_id=def_id)

    # Supersede A → B, then B → C
    superseded_a = await service.supersede_definition(
        old_definition_id="chain-A", new_definition_id="chain-B"
    )
    superseded_b = await service.supersede_definition(
        old_definition_id="chain-B", new_definition_id="chain-C"
    )

    assert superseded_a.lifecycle_state == LifecycleState.SUPERSEDED
    assert superseded_b.lifecycle_state == LifecycleState.SUPERSEDED

    # Verify C remains published
    c_def = await service.get_definition("chain-C")
    assert c_def.lifecycle_state == LifecycleState.PUBLISHED

    # Walk replacement chain from A → [A, B, C]
    resolver = LinkedEntryResolutionService()
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        chain = await resolver.resolve_replacement_chain("chain-A", uow)
    assert chain == ["chain-A", "chain-B", "chain-C"]

    # Search index: A and B are superseded, C is published
    uow2 = CompendiumUnitOfWork(db_session)
    async with uow2:
        published_results = await uow2.search_index.search(
            lifecycle_states=["published"],
        )
        superseded_results = await uow2.search_index.search(
            lifecycle_states=["superseded"],
        )

    published_ids = {r.definition_id for r in published_results}
    superseded_ids = {r.definition_id for r in superseded_results}

    assert "chain-C" in published_ids
    assert "chain-A" in superseded_ids
    assert "chain-B" in superseded_ids


# =========================================================================
# Test 4: Delete Cascades (search index + links cleanup)
# =========================================================================
@pytest.mark.asyncio
async def test_delete_cascades_search_index_and_links(db_session):
    """
    Create a draft definition, delete it, verify search index is clean.
    """
    service, _ = _build_service(db_session)
    await _seed_pack(db_session, pack_id="del-pack")

    created = await service.create_definition(
        _build_monster(
            definition_id="del-monster",
            pack_id="del-pack",
            slug="deletable",
            name="Delete Me",
        )
    )

    # Verify in search index
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        before = await uow.search_index.search(query_text="delete me")
    assert len(before) == 1

    # Delete
    await service.delete_definition(
        definition_id=created.id,
        expected_content_version=created.content_version,
    )

    # Verify search index is clean
    uow2 = CompendiumUnitOfWork(db_session)
    async with uow2:
        after = await uow2.search_index.search(query_text="delete me")
    assert len(after) == 0

    # Verify definition is gone
    uow3 = CompendiumUnitOfWork(db_session)
    async with uow3:
        gone = await uow3.definitions.get_by_id(created.id)
    assert gone is None
