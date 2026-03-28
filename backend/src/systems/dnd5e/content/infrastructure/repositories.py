from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.definition_models import (
    AbilityDefinition,
    BackgroundDefinition,
    ClassDefinition,
    ConditionDefinition,
    DefinitionRecord,
    ItemDefinition,
    LoreDefinition,
    MonsterDefinition,
    SpeciesDefinition,
    SpellDefinition,
)
from ..domain.link_models import LinkedEntryReference
from ..domain.pack_models import ContentPackRecord
from ..domain.primitives import DefinitionFamily, LifecycleState
from .orm import CompendiumDefinitionModel, ContentPackModel, LinkedEntryModel

_DEFINITION_BASE_FIELDS = {
    "id",
    "family",
    "slug",
    "name",
    "lifecycle_state",
    "content_version",
    "schema_version",
    "pack_id",
    "provenance_source",
    "provenance_author",
    "provenance_updated_at",
}

_DEFINITION_MODEL_BY_FAMILY = {
    DefinitionFamily.LORE: LoreDefinition,
    DefinitionFamily.SPECIES: SpeciesDefinition,
    DefinitionFamily.BACKGROUND: BackgroundDefinition,
    DefinitionFamily.CLASS: ClassDefinition,
    DefinitionFamily.CONDITION: ConditionDefinition,
    DefinitionFamily.ABILITY: AbilityDefinition,
    DefinitionFamily.SPELL: SpellDefinition,
    DefinitionFamily.ITEM: ItemDefinition,
    DefinitionFamily.MONSTER: MonsterDefinition,
}


def _pack_domain_from_row(row: ContentPackModel) -> ContentPackRecord:
    return ContentPackRecord.model_validate(
        {
            "id": row.id,
            "author_user_id": row.author_user_id,
            "title": row.title,
            "lifecycle_state": row.lifecycle_state,
            "is_homebrew": row.is_homebrew,
            "pack_key": row.pack_key,
            "compatibility_target": row.compatibility_target,
            "published_version": row.published_version,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    )


def _definition_payload_from_domain(definition: DefinitionRecord) -> dict[str, Any]:
    serialized = definition.model_dump(mode="json")
    return {key: value for key, value in serialized.items() if key not in _DEFINITION_BASE_FIELDS}


def _definition_domain_from_row(row: CompendiumDefinitionModel) -> DefinitionRecord:
    family = DefinitionFamily(row.family)
    model_cls = _DEFINITION_MODEL_BY_FAMILY[family]
    payload = row.payload or {}
    raw = {
        "id": row.id,
        "family": row.family,
        "slug": row.slug,
        "name": row.name,
        "lifecycle_state": row.lifecycle_state,
        "content_version": row.content_version,
        "schema_version": row.schema_version,
        "pack_id": row.pack_id,
        "provenance_source": row.provenance_source,
        "provenance_author": row.provenance_author,
        "provenance_updated_at": row.provenance_updated_at,
        **payload,
    }
    return model_cls.model_validate(raw)


def _linked_entry_domain_from_row(row: LinkedEntryModel) -> LinkedEntryReference:
    return LinkedEntryReference.model_validate(
        {
            "id": row.id,
            "source_definition_id": row.source_definition_id,
            "source_path": row.source_path,
            "target_definition_id": row.target_definition_id,
            "target_family": row.target_family,
            "relation_kind": row.relation_kind,
            "required": row.required,
            "resolve_mode": row.resolve_mode,
        }
    )


class ContentPackRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, pack: ContentPackRecord) -> ContentPackRecord:
        row = ContentPackModel(
            id=pack.id,
            author_user_id=pack.author_user_id,
            title=pack.title,
            lifecycle_state=pack.lifecycle_state.value if isinstance(pack.lifecycle_state, LifecycleState) else str(pack.lifecycle_state),
            is_homebrew=pack.is_homebrew,
            pack_key=pack.pack_key,
            compatibility_target=pack.compatibility_target,
            published_version=pack.published_version,
        )
        self._db.add(row)
        await self._db.flush()
        await self._db.refresh(row)
        return _pack_domain_from_row(row)

    async def get_by_id(self, pack_id: str) -> ContentPackRecord | None:
        row = await self._db.get(ContentPackModel, pack_id)
        if row is None:
            return None
        return _pack_domain_from_row(row)

    async def list(self, *, lifecycle_state: LifecycleState | None = None) -> list[ContentPackRecord]:
        stmt = select(ContentPackModel).order_by(ContentPackModel.created_at.desc())
        if lifecycle_state is not None:
            stmt = stmt.where(ContentPackModel.lifecycle_state == lifecycle_state.value)

        result = await self._db.execute(stmt)
        return [_pack_domain_from_row(row) for row in result.scalars().all()]


class DefinitionRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def upsert(self, definition: DefinitionRecord) -> DefinitionRecord:
        payload = _definition_payload_from_domain(definition)
        row = await self._db.get(CompendiumDefinitionModel, definition.id)

        if row is None:
            row = CompendiumDefinitionModel(
                id=definition.id,
                family=definition.family.value,
                slug=definition.slug,
                name=definition.name,
                lifecycle_state=definition.lifecycle_state.value,
                content_version=definition.content_version,
                schema_version=definition.schema_version,
                pack_id=definition.pack_id,
                provenance_source=definition.provenance_source,
                provenance_author=definition.provenance_author,
                provenance_updated_at=definition.provenance_updated_at,
                payload=payload,
            )
            self._db.add(row)
        else:
            row.family = definition.family.value
            row.slug = definition.slug
            row.name = definition.name
            row.lifecycle_state = definition.lifecycle_state.value
            row.content_version = definition.content_version
            row.schema_version = definition.schema_version
            row.pack_id = definition.pack_id
            row.provenance_source = definition.provenance_source
            row.provenance_author = definition.provenance_author
            row.provenance_updated_at = definition.provenance_updated_at
            row.payload = payload

        await self._db.flush()
        await self._db.refresh(row)
        return _definition_domain_from_row(row)

    async def get_by_id(self, definition_id: str) -> DefinitionRecord | None:
        row = await self._db.get(CompendiumDefinitionModel, definition_id)
        if row is None:
            return None
        return _definition_domain_from_row(row)

    async def get_by_pack_id(
        self,
        pack_id: str,
        *,
        family: DefinitionFamily | None = None,
    ) -> list[DefinitionRecord]:
        stmt = select(CompendiumDefinitionModel).where(CompendiumDefinitionModel.pack_id == pack_id)
        if family is not None:
            stmt = stmt.where(CompendiumDefinitionModel.family == family.value)
        stmt = stmt.order_by(CompendiumDefinitionModel.updated_at.desc())

        result = await self._db.execute(stmt)
        return [_definition_domain_from_row(row) for row in result.scalars().all()]

    async def get_versions(self, definition_id: str) -> list[DefinitionRecord]:
        base = await self._db.get(CompendiumDefinitionModel, definition_id)
        if base is None:
            return []

        stmt = (
            select(CompendiumDefinitionModel)
            .where(
                CompendiumDefinitionModel.pack_id == base.pack_id,
                CompendiumDefinitionModel.family == base.family,
                CompendiumDefinitionModel.slug == base.slug,
            )
            .order_by(
                CompendiumDefinitionModel.content_version.desc(),
                CompendiumDefinitionModel.updated_at.desc(),
            )
        )

        result = await self._db.execute(stmt)
        return [_definition_domain_from_row(row) for row in result.scalars().all()]


class LinkedEntryRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, entry: LinkedEntryReference) -> LinkedEntryReference:
        row = LinkedEntryModel(
            id=entry.id,
            source_definition_id=entry.source_definition_id,
            source_path=entry.source_path,
            target_definition_id=entry.target_definition_id,
            target_family=entry.target_family,
            relation_kind=entry.relation_kind.value,
            required=entry.required,
            resolve_mode=entry.resolve_mode.value,
        )
        self._db.add(row)
        await self._db.flush()
        await self._db.refresh(row)
        return _linked_entry_domain_from_row(row)

    async def list_by_source_definition_id(self, source_definition_id: str) -> list[LinkedEntryReference]:
        stmt = (
            select(LinkedEntryModel)
            .where(LinkedEntryModel.source_definition_id == source_definition_id)
            .order_by(LinkedEntryModel.created_at.desc())
        )
        result = await self._db.execute(stmt)
        return [_linked_entry_domain_from_row(row) for row in result.scalars().all()]
