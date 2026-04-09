from __future__ import annotations
__production_status__ = "gold"

from datetime import datetime, timezone
import re
import unicodedata

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.index_models import IndexDocument
from .orm import SearchIndexModel


class SearchIndexRepository:
    """
    Denormalized search index repository — the CQRS read-path store.

    Queries hit this flat table instead of the relational definitions table.
    For MVP, uses SQL LIKE on search_blob. Upgradeable to GIN/tsvector or
    Elasticsearch behind this same interface.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def upsert_document(self, doc: IndexDocument) -> None:
        """Insert or update an index document for a definition."""
        row = await self._get_by_definition_id(doc.definition_id)

        if row is None:
            row = SearchIndexModel(
                id=doc.document_id,
                definition_id=doc.definition_id,
                family=doc.family,
                pack_id=doc.pack_id,
                name=doc.name,
                name_normalized=doc.name_normalized,
                search_blob=doc.search_blob,
                visibility_state=doc.visibility_state,
            )
            self._db.add(row)
        else:
            row.family = doc.family
            row.pack_id = doc.pack_id
            row.name = doc.name
            row.name_normalized = doc.name_normalized
            row.search_blob = doc.search_blob
            row.visibility_state = doc.visibility_state

        await self._db.flush()

    async def delete_document(self, definition_id: str) -> None:
        """Remove the index document for a definition."""
        row = await self._get_by_definition_id(definition_id)
        if row is not None:
            await self._db.delete(row)
            await self._db.flush()

    async def search(
        self,
        *,
        query_text: str | None = None,
        family: str | None = None,
        lifecycle_states: list[str] | None = None,
        pack_id: str | None = None,
        payload_filters: dict[str, str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[IndexDocument]:
        """
        Search the denormalized index.

        This is the primary read-path query — it NEVER touches the
        dnd5e_compendium_definitions table.
        """
        stmt = select(SearchIndexModel)

        if query_text:
            term = f"%{query_text.lower()}%"
            stmt = stmt.where(
                or_(
                    SearchIndexModel.name_normalized.ilike(term),
                    SearchIndexModel.search_blob.ilike(term),
                )
            )

        if family:
            stmt = stmt.where(SearchIndexModel.family == family)

        if lifecycle_states:
            stmt = stmt.where(
                SearchIndexModel.visibility_state.in_(lifecycle_states)
            )

        if pack_id:
            stmt = stmt.where(SearchIndexModel.pack_id == pack_id)

        if payload_filters:
            for key, value in payload_filters.items():
                token = self._payload_filter_token(key=key, value=value)
                stmt = stmt.where(
                    SearchIndexModel.search_blob.ilike(f"%{token}%"))

        stmt = stmt.order_by(
            SearchIndexModel.name_normalized.asc(),
            SearchIndexModel.id.asc(),  # Stable tie-breaker
        )
        stmt = stmt.limit(limit).offset(offset)

        result = await self._db.execute(stmt)
        return [self._row_to_document(row) for row in result.scalars().all()]

    async def count(
        self,
        *,
        query_text: str | None = None,
        family: str | None = None,
        lifecycle_states: list[str] | None = None,
        pack_id: str | None = None,
        payload_filters: dict[str, str] | None = None,
    ) -> int:
        """Count matching documents (for pagination metadata)."""
        stmt = select(func.count(SearchIndexModel.id))

        if query_text:
            term = f"%{query_text.lower()}%"
            stmt = stmt.where(
                or_(
                    SearchIndexModel.name_normalized.ilike(term),
                    SearchIndexModel.search_blob.ilike(term),
                )
            )

        if family:
            stmt = stmt.where(SearchIndexModel.family == family)

        if lifecycle_states:
            stmt = stmt.where(
                SearchIndexModel.visibility_state.in_(lifecycle_states)
            )

        if pack_id:
            stmt = stmt.where(SearchIndexModel.pack_id == pack_id)

        if payload_filters:
            for key, value in payload_filters.items():
                token = self._payload_filter_token(key=key, value=value)
                stmt = stmt.where(
                    SearchIndexModel.search_blob.ilike(f"%{token}%"))

        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def get_catalog_revision(self, *, pack_id: str | None = None) -> int:
        """Return a monotonic-ish catalog revision derived from index row update time."""
        stmt = select(func.max(SearchIndexModel.updated_at))
        if pack_id:
            stmt = stmt.where(SearchIndexModel.pack_id == pack_id)

        result = await self._db.execute(stmt)
        max_updated_at = result.scalar_one()
        if max_updated_at is None:
            return 0

        if isinstance(max_updated_at, datetime):
            return int(max_updated_at.replace(tzinfo=timezone.utc).timestamp() * 1000)

        return 0

    async def _get_by_definition_id(
        self, definition_id: str,
    ) -> SearchIndexModel | None:
        stmt = select(SearchIndexModel).where(
            SearchIndexModel.definition_id == definition_id
        )
        result = await self._db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def _row_to_document(row: SearchIndexModel) -> IndexDocument:
        return IndexDocument(
            document_id=row.id,
            definition_id=row.definition_id,
            family=row.family,
            pack_id=row.pack_id,
            name=row.name,
            name_normalized=row.name_normalized,
            search_blob=row.search_blob,
            visibility_state=row.visibility_state,
        )

    @staticmethod
    def _payload_filter_token(*, key: str, value: str) -> str:
        normalized_key = SearchIndexRepository._normalize_fragment(key)
        normalized_value = SearchIndexRepository._normalize_fragment(value)
        return f"{normalized_key}:{normalized_value}"

    @staticmethod
    def _normalize_fragment(value: str) -> str:
        nfkd = unicodedata.normalize("NFKD", value)
        ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_only.lower().strip())
