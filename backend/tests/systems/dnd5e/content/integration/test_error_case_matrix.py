"""
V05-07 Error Case Matrix Tests.

Systematic verification that all domain errors produce the correct
CompendiumErrorCode reason codes, and that Pydantic contract violations
surface field-level validation errors.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pydantic
import pytest

from src.systems.dnd5e.content.application.services import (
    CompendiumApplicationService,
    ContentMutationEvent,
)
from src.systems.dnd5e.content.domain.definition_models import MonsterDefinition
from src.systems.dnd5e.content.domain.errors import (
    DuplicateDefinitionSlugError,
    IllegalStateDependencyError,
    ReplacementCycleError,
    VersionMismatchError,
)
from src.systems.dnd5e.content.domain.invariants import CompendiumErrorCode
from src.systems.dnd5e.content.domain.link_models import (
    LinkedEntryReference,
    RelationKind,
    ResolveMode,
)
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.primitives import LifecycleState
from src.systems.dnd5e.content.infrastructure.unit_of_work import CompendiumUnitOfWork
from src.systems.dnd5e.content.policies.lifecycle_transition_policy import (
    ContentLifecycleError,
    LifecycleTransitionPolicy,
)


# ---------------------------------------------------------------------------
# Local factories
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

def _build_link(
    *, link_id: str, source_id: str, target_id: str,
    relation_kind: RelationKind = RelationKind.GRANTS,
    target_family: str = "monster", required: bool = True,
) -> LinkedEntryReference:
    return LinkedEntryReference(
        id=link_id, source_definition_id=source_id, source_path="$",
        target_definition_id=target_id, target_family=target_family,
        relation_kind=relation_kind, required=required,
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
        id=pack_id, author_user_id="user-1", title="Error Test Pack",
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
# Test 5: Pydantic Validation Failures
# =========================================================================
@pytest.mark.asyncio
async def test_pydantic_validation_missing_required_fields(db_session):
    """
    MonsterDefinition with missing challenge_rating, armor_class, etc.
    should raise a Pydantic ValidationError with field-level detail.
    """
    with pytest.raises(pydantic.ValidationError) as exc:
        MonsterDefinition(
            id="bad-mon",
            slug="bad-monster",
            name="Incomplete Monster",
            lifecycle_state=LifecycleState.DRAFT,
            content_version=1,
            schema_version=1,
            pack_id="pack-1",
            provenance_source="tests",
            provenance_updated_at="2026-01-01T00:00:00Z",
            # Missing: challenge_rating, armor_class, hit_points_formula
            action_operation_specs=[],
        )

    errors = exc.value.errors()
    missing_fields = {e["loc"][-1] for e in errors if e["type"] == "missing"}
    assert "challenge_rating" in missing_fields
    assert "armor_class" in missing_fields
    assert "hit_points_formula" in missing_fields


def test_pydantic_validation_invalid_content_version():
    """Content version < 1 should fail with VALIDATION_FAILED code."""
    with pytest.raises(pydantic.ValidationError) as exc:
        MonsterDefinition(
            id="bad-ver",
            slug="ver-test",
            name="Bad Version",
            lifecycle_state=LifecycleState.DRAFT,
            content_version=0,
            schema_version=1,
            pack_id="pack-1",
            provenance_source="tests",
            provenance_updated_at="2026-01-01T00:00:00Z",
            challenge_rating=1.0,
            armor_class=10,
            hit_points_formula="1d8",
            action_operation_specs=[],
        )
    assert CompendiumErrorCode.VALIDATION_FAILED.value in str(exc.value)


# =========================================================================
# Test 6: Lifecycle Transition Denial Matrix
# =========================================================================
class TestLifecycleTransitionMatrix:
    """
    Matrix test: verify all illegal lifecycle transitions produce
    ContentLifecycleError with the correct code.

    Valid transitions (per LifecycleTransitionPolicy):
            DRAFT      → {PUBLISHED}
            PUBLISHED  → {ARCHIVED, SUPERSEDED}
            ARCHIVED   → {PUBLISHED}
      SUPERSEDED → {} (terminal)
    """

    @pytest.mark.parametrize(
        "current, target",
        [
            # superseded is terminal — cannot go anywhere
            (LifecycleState.SUPERSEDED, LifecycleState.DRAFT),
            (LifecycleState.SUPERSEDED, LifecycleState.PUBLISHED),
            (LifecycleState.SUPERSEDED, LifecycleState.ARCHIVED),
            # draft cannot go directly to superseded
            (LifecycleState.DRAFT, LifecycleState.SUPERSEDED),
            (LifecycleState.DRAFT, LifecycleState.ARCHIVED),
            (LifecycleState.PUBLISHED, LifecycleState.DRAFT),
            (LifecycleState.ARCHIVED, LifecycleState.DRAFT),
            # archived cannot go to superseded
            (LifecycleState.ARCHIVED, LifecycleState.SUPERSEDED),
        ],
    )
    def test_illegal_transition_denied(self, current, target):
        with pytest.raises(ContentLifecycleError):
            LifecycleTransitionPolicy.deny_on_invalid_transition(current, target)

    @pytest.mark.parametrize(
        "current, target",
        [
            (LifecycleState.DRAFT, LifecycleState.PUBLISHED),
            (LifecycleState.PUBLISHED, LifecycleState.ARCHIVED),
            (LifecycleState.PUBLISHED, LifecycleState.SUPERSEDED),
            (LifecycleState.ARCHIVED, LifecycleState.PUBLISHED),
        ],
    )
    def test_valid_transition_allowed(self, current, target):
        # Should NOT raise
        LifecycleTransitionPolicy.deny_on_invalid_transition(current, target)


# =========================================================================
# Test 7: Link Cycle Detection Produces Correct Error Code
# =========================================================================
@pytest.mark.asyncio
async def test_supersedence_cycle_produces_cycle_detected_code(db_session):
    """
    A → B → C → A supersedence cycle must produce CYCLE_DETECTED.
    """
    service, _ = _build_service(db_session)
    await _seed_pack(db_session, pack_id="cycle-pack")

    for def_id in ["cyc-A", "cyc-B", "cyc-C"]:
        await service.create_definition(
            _build_monster(
                definition_id=def_id,
                pack_id="cycle-pack",
                slug=f"slug-{def_id}",
            )
        )
        await service.publish_definition(definition_id=def_id)

    await service.supersede_definition(old_definition_id="cyc-A", new_definition_id="cyc-B")
    await service.supersede_definition(old_definition_id="cyc-B", new_definition_id="cyc-C")

    with pytest.raises(ReplacementCycleError) as exc:
        await service.supersede_definition(old_definition_id="cyc-C", new_definition_id="cyc-A")

    assert CompendiumErrorCode.CYCLE_DETECTED.value in str(exc.value)


# =========================================================================
# Test 8: Version Guard Prevents Stale Updates
# =========================================================================
@pytest.mark.asyncio
async def test_version_guard_prevents_stale_updates(db_session):
    """
    Updating with a wrong expected_content_version must produce
    VERSION_MISMATCH error code.
    """
    service, _ = _build_service(db_session)
    await _seed_pack(db_session, pack_id="ver-pack")

    created = await service.create_definition(
        _build_monster(definition_id="ver-mon", pack_id="ver-pack", slug="ver-slug")
    )
    assert created.content_version == 1

    # Correct version works
    updated = await service.update_definition(
        definition_id=created.id,
        updates={"name": "Updated Goblin"},
        expected_content_version=1,
    )
    assert updated.content_version == 2

    # Wrong version (stale) is denied
    with pytest.raises(VersionMismatchError) as exc:
        await service.update_definition(
            definition_id=created.id,
            updates={"name": "Stale Update"},
            expected_content_version=1,  # Stale — should be 2
        )
    assert CompendiumErrorCode.VERSION_MISMATCH.value in str(exc.value)


# =========================================================================
# Test 9: Duplicate Slug Rejection
# =========================================================================
@pytest.mark.asyncio
async def test_duplicate_slug_in_same_pack_family_rejected(db_session):
    """
    Two definitions with the same slug in the same pack+family
    must produce DUPLICATE_SLUG error code.
    """
    service, _ = _build_service(db_session)
    await _seed_pack(db_session, pack_id="slug-pack")

    await service.create_definition(
        _build_monster(definition_id="slug-1", pack_id="slug-pack", slug="duplicate-slug")
    )

    with pytest.raises(DuplicateDefinitionSlugError) as exc:
        await service.create_definition(
            _build_monster(definition_id="slug-2", pack_id="slug-pack", slug="duplicate-slug")
        )
    assert CompendiumErrorCode.DUPLICATE_SLUG.value in str(exc.value)


# =========================================================================
# Test: Publish Denied When Required Link Target is Draft
# =========================================================================
@pytest.mark.asyncio
async def test_publish_denied_when_link_target_is_draft(db_session):
    """
    Publishing a definition that has a required link to a DRAFT target
    must be denied with ILLEGAL_STATE_DEPENDENCY.
    """
    service, _ = _build_service(db_session)
    await _seed_pack(db_session, pack_id="dep-pack")

    source = await service.create_definition(
        _build_monster(definition_id="dep-src", pack_id="dep-pack", slug="source")
    )
    target = await service.create_definition(
        _build_monster(definition_id="dep-tgt", pack_id="dep-pack", slug="target")
    )

    # Create required link source → target
    uow = CompendiumUnitOfWork(db_session)
    async with uow:
        await uow.links.create(
            _build_link(
                link_id="dep-link",
                source_id=source.id,
                target_id=target.id,
                required=True,
            )
        )
        await uow.commit()

    # target is still DRAFT — publish should fail
    with pytest.raises(IllegalStateDependencyError) as exc:
        await service.publish_definition(definition_id=source.id)

    assert "cannot depend on DRAFT target" in str(exc.value)
