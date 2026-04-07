from __future__ import annotations
__production_status__ = "gold"

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ..domain.definition_models import DefinitionRecord
from ..domain.errors import (
    ContentPackNotFoundError,
    DefinitionNotFoundError,
    DuplicateContentPackIdError,
    DuplicateDefinitionIdError,
    DuplicateDefinitionSlugError,
    ImmutableDefinitionError,
    InvalidReplacementTargetError,
    VersionMismatchError,
)
from ..domain.index_models import build_index_document
from ..domain.link_models import LinkedEntryReference, RelationKind, ResolveMode
from ..domain.pack_models import ContentPackRecord
from ..domain.primitives import DefinitionFamily, LifecycleState
from ..infrastructure.unit_of_work import CompendiumUnitOfWork
from ..policies.lifecycle_transition_policy import LifecycleTransitionPolicy
from ..policies.linked_entry_integrity_policy import LinkedEntryIntegrityPolicy


@dataclass(slots=True)
class ContentMutationEvent:
    event_type: str
    definition_id: str
    family: str
    lifecycle_state: str
    content_version: int
    pack_id: str | None = None
    replacement_target_id: str | None = None
    request_id: str | None = None
    campaign_id: str | None = None
    catalog_revision: int | None = None
    affected_definition_ids: list[str] | None = None


EventPublisher = Callable[[ContentMutationEvent], Awaitable[None] | None]
UowFactory = Callable[[], CompendiumUnitOfWork]


class CompendiumApplicationService:
    """Authoritative orchestration service for content definition mutations."""

    _catalog_revision: int = 0

    def __init__(
        self,
        *,
        uow_factory: UowFactory,
        event_publisher: EventPublisher | None = None,
    ):
        self._uow_factory = uow_factory
        self._event_publisher = event_publisher
        self._link_policy = LinkedEntryIntegrityPolicy()

    async def create_pack(self, pack: ContentPackRecord) -> ContentPackRecord:
        async with self._uow_factory() as uow:
            existing = await uow.packs.get_by_id(pack.id)
            if existing is not None:
                raise DuplicateContentPackIdError(pack.id)

            created = await uow.packs.create(pack)
            await uow.commit()
        return created

    async def list_packs(
        self,
        *,
        lifecycle_state: LifecycleState | None = None,
    ) -> list[ContentPackRecord]:
        async with self._uow_factory() as uow:
            return await uow.packs.list(lifecycle_state=lifecycle_state)

    async def get_pack(self, pack_id: str) -> ContentPackRecord | None:
        async with self._uow_factory() as uow:
            return await uow.packs.get_by_id(pack_id)

    async def get_definition(self, definition_id: str) -> DefinitionRecord:
        async with self._uow_factory() as uow:
            definition = await uow.definitions.get_by_id(definition_id)
            if definition is None:
                raise DefinitionNotFoundError(definition_id)
            return definition

    async def list_definitions(
        self,
        *,
        pack_id: str,
        family: DefinitionFamily | None = None,
    ) -> list[DefinitionRecord]:
        async with self._uow_factory() as uow:
            return await uow.definitions.get_by_pack_id(pack_id, family=family)

    async def create_definition(
        self,
        definition: DefinitionRecord,
        *,
        request_id: str | None = None,
        campaign_id: str | None = None,
    ) -> DefinitionRecord:
        async with self._uow_factory() as uow:
            await self._ensure_pack_exists(uow, definition.pack_id)

            if await uow.definitions.get_by_id(definition.id) is not None:
                raise DuplicateDefinitionIdError(definition.id)

            slug_matches = await uow.definitions.get_by_pack_family_slug(
                pack_id=definition.pack_id,
                family=definition.family,
                slug=definition.slug,
            )
            if slug_matches:
                raise DuplicateDefinitionSlugError(
                    pack_id=definition.pack_id,
                    family=definition.family.value,
                    slug=definition.slug,
                )

            saved = await uow.definitions.upsert(definition)
            await self._update_search_index(uow, saved)
            await uow.commit()

        await self._emit(
            ContentMutationEvent(
                event_type="definition_created",
                definition_id=saved.id,
                family=saved.family.value,
                lifecycle_state=saved.lifecycle_state.value,
                content_version=saved.content_version,
                pack_id=saved.pack_id,
                request_id=request_id,
                campaign_id=campaign_id,
                catalog_revision=self._next_catalog_revision(),
                affected_definition_ids=[saved.id],
            )
        )
        return saved

    async def update_definition(
        self,
        *,
        definition_id: str,
        updates: Mapping[str, Any],
        expected_content_version: int,
        request_id: str | None = None,
        campaign_id: str | None = None,
    ) -> DefinitionRecord:
        async with self._uow_factory() as uow:
            existing = await uow.definitions.get_by_id(definition_id)
            if existing is None:
                raise DefinitionNotFoundError(definition_id)

            try:
                LifecycleTransitionPolicy.validate_delete_permission(
                    state=existing.lifecycle_state
                )
            except ValueError:
                raise ImmutableDefinitionError(
                    lifecycle_state=existing.lifecycle_state.value
                ) from None

            if expected_content_version != existing.content_version:
                raise VersionMismatchError(
                    expected=expected_content_version,
                    actual=existing.content_version,
                )

            self._deny_immutable_field_changes(
                existing=existing, updates=updates)

            candidate_data = existing.model_dump(mode="python")
            candidate_data.update(dict(updates))
            candidate_data["content_version"] = existing.content_version + 1
            candidate_data["provenance_updated_at"] = datetime.now(
                timezone.utc)

            validated = type(existing).model_validate(candidate_data)

            if validated.slug != existing.slug:
                slug_matches = await uow.definitions.get_by_pack_family_slug(
                    pack_id=validated.pack_id,
                    family=validated.family,
                    slug=validated.slug,
                )
                if any(match.id != existing.id for match in slug_matches):
                    raise DuplicateDefinitionSlugError(
                        pack_id=validated.pack_id,
                        family=validated.family.value,
                        slug=validated.slug,
                    )

            saved = await uow.definitions.upsert(validated)
            await self._update_search_index(uow, saved)
            await uow.commit()

        await self._emit(
            ContentMutationEvent(
                event_type="definition_updated",
                definition_id=saved.id,
                family=saved.family.value,
                lifecycle_state=saved.lifecycle_state.value,
                content_version=saved.content_version,
                pack_id=saved.pack_id,
                request_id=request_id,
                campaign_id=campaign_id,
                catalog_revision=self._next_catalog_revision(),
                affected_definition_ids=[saved.id],
            )
        )
        return saved

    async def delete_definition(
        self,
        *,
        definition_id: str,
        expected_content_version: int,
        request_id: str | None = None,
        campaign_id: str | None = None,
    ) -> None:
        async with self._uow_factory() as uow:
            existing = await uow.definitions.get_by_id(definition_id)
            if existing is None:
                raise DefinitionNotFoundError(definition_id)

            if existing.lifecycle_state != LifecycleState.DRAFT:
                raise ImmutableDefinitionError(
                    lifecycle_state=existing.lifecycle_state.value
                )

            if expected_content_version != existing.content_version:
                raise VersionMismatchError(
                    expected=expected_content_version,
                    actual=existing.content_version,
                )

            reverse_refs = await uow.links.list_by_target_definition_id(definition_id)
            self._link_policy.validate_delete_dependencies(
                target_definition_id=definition_id,
                incoming_links=reverse_refs,
            )

            await uow.links.delete_by_source_definition_id(definition_id)
            await self._delete_search_index(uow, definition_id)
            await uow.definitions.delete(definition_id)
            await uow.commit()

        await self._emit(
            ContentMutationEvent(
                event_type="definition_deleted",
                definition_id=existing.id,
                family=existing.family.value,
                lifecycle_state=existing.lifecycle_state.value,
                content_version=existing.content_version,
                pack_id=existing.pack_id,
                request_id=request_id,
                campaign_id=campaign_id,
                catalog_revision=self._next_catalog_revision(),
                affected_definition_ids=[existing.id],
            )
        )

    async def publish_definition(
        self,
        *,
        definition_id: str,
        request_id: str | None = None,
        campaign_id: str | None = None,
    ) -> DefinitionRecord:
        async with self._uow_factory() as uow:
            existing = await uow.definitions.get_by_id(definition_id)
            if existing is None:
                raise DefinitionNotFoundError(definition_id)

            LifecycleTransitionPolicy.deny_on_invalid_transition(
                existing.lifecycle_state,
                LifecycleState.PUBLISHED,
            )

            links = await uow.links.list_by_source_definition_id(existing.id)
            self._link_policy.validate_resolve_modes(links=links)
            await self._link_policy.validate_required_targets_exist(
                links=links,
                target_lookup=uow.definitions.get_by_id,
            )

            await self._link_policy.validate_published_targets_only(
                links=links,
                target_lookup=uow.definitions.get_by_id,
            )

            updated_data = existing.model_dump(mode="python")
            updated_data["lifecycle_state"] = LifecycleState.PUBLISHED
            updated_data["content_version"] = existing.content_version + 1
            updated_data["provenance_updated_at"] = datetime.now(timezone.utc)
            published = type(existing).model_validate(updated_data)

            saved = await uow.definitions.upsert(published)
            await self._update_search_index(uow, saved)
            await uow.commit()

        await self._emit(
            ContentMutationEvent(
                event_type="definition_published",
                definition_id=saved.id,
                family=saved.family.value,
                lifecycle_state=saved.lifecycle_state.value,
                content_version=saved.content_version,
                pack_id=saved.pack_id,
                request_id=request_id,
                campaign_id=campaign_id,
                catalog_revision=self._next_catalog_revision(),
                affected_definition_ids=[saved.id],
            )
        )
        return saved

    async def supersede_definition(
        self,
        *,
        old_definition_id: str,
        new_definition_id: str,
        request_id: str | None = None,
        campaign_id: str | None = None,
    ) -> DefinitionRecord:
        if old_definition_id == new_definition_id:
            raise InvalidReplacementTargetError(
                "A definition cannot supersede itself."
            )

        async with self._uow_factory() as uow:
            old_definition = await uow.definitions.get_by_id(old_definition_id)
            if old_definition is None:
                raise DefinitionNotFoundError(old_definition_id)

            new_definition = await uow.definitions.get_by_id(new_definition_id)
            if new_definition is None:
                raise DefinitionNotFoundError(new_definition_id)

            LifecycleTransitionPolicy.validate_supersedence(
                source_state=old_definition.lifecycle_state,
                replacement_state=new_definition.lifecycle_state,
            )

            self._link_policy.validate_target_family(
                source_family=old_definition.family,
                target_family=new_definition.family,
                relation_kind=RelationKind.REPLACEMENT,
            )

            await self._link_policy.validate_replacement_cycle_safety(
                source_definition_id=old_definition.id,
                replacement_target_id=new_definition.id,
                replacement_target_lookup=uow.links.get_replacement_target,
            )

            old_links = await uow.links.list_by_source_definition_id(old_definition.id)
            for old_link in old_links:
                if old_link.relation_kind == RelationKind.REPLACEMENT:
                    await uow.links.delete(old_link.id)

            replacement_link = LinkedEntryReference(
                id=f"link-replacement-{uuid4().hex}",
                source_definition_id=old_definition.id,
                source_path="$.replacement_target_id",
                target_definition_id=new_definition.id,
                target_family=new_definition.family.value,
                relation_kind=RelationKind.REPLACEMENT,
                required=True,
                resolve_mode=ResolveMode.STRICT,
            )
            await uow.links.create(replacement_link)

            superseded_data = old_definition.model_dump(mode="python")
            superseded_data["lifecycle_state"] = LifecycleState.SUPERSEDED
            superseded_data["content_version"] = old_definition.content_version + 1
            superseded_data["provenance_updated_at"] = datetime.now(
                timezone.utc)
            superseded = type(old_definition).model_validate(superseded_data)

            saved = await uow.definitions.upsert(superseded)
            await self._update_search_index(uow, saved)
            await uow.commit()

        await self._emit(
            ContentMutationEvent(
                event_type="definition_superseded",
                definition_id=saved.id,
                family=saved.family.value,
                lifecycle_state=saved.lifecycle_state.value,
                content_version=saved.content_version,
                pack_id=saved.pack_id,
                replacement_target_id=new_definition_id,
                request_id=request_id,
                campaign_id=campaign_id,
                catalog_revision=self._next_catalog_revision(),
                affected_definition_ids=[saved.id, new_definition_id],
            )
        )
        return saved

    @classmethod
    def _next_catalog_revision(cls) -> int:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        cls._catalog_revision = max(now_ms, cls._catalog_revision + 1)
        return cls._catalog_revision

    @staticmethod
    def _deny_immutable_field_changes(
        *,
        existing: DefinitionRecord,
        updates: Mapping[str, Any],
    ) -> None:
        if "id" in updates and updates["id"] != existing.id:
            raise InvalidReplacementTargetError(
                "Definition id cannot be changed.")
        if "family" in updates and updates["family"] != existing.family:
            raise InvalidReplacementTargetError(
                "Definition family cannot be changed.")
        if "pack_id" in updates and updates["pack_id"] != existing.pack_id:
            raise InvalidReplacementTargetError(
                "Definition pack_id cannot be changed.")

    async def _emit(self, event: ContentMutationEvent) -> None:
        if self._event_publisher is None:
            return

        maybe_awaitable = self._event_publisher(event)
        if maybe_awaitable is not None:
            await maybe_awaitable

    @staticmethod
    async def _ensure_pack_exists(
        uow: CompendiumUnitOfWork,
        pack_id: str,
    ) -> None:
        pack = await uow.packs.get_by_id(pack_id)
        if pack is None:
            raise ContentPackNotFoundError(pack_id)

    @staticmethod
    async def _update_search_index(
        uow: CompendiumUnitOfWork,
        definition: DefinitionRecord,
    ) -> None:
        doc = build_index_document(definition)
        await uow.search_index.upsert_document(doc)

    @staticmethod
    async def _delete_search_index(
        uow: CompendiumUnitOfWork,
        definition_id: str,
    ) -> None:
        await uow.search_index.delete_document(definition_id)
