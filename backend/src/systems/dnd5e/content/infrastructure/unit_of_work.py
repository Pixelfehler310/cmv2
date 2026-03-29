from __future__ import annotations
__production_status__ = "gold"

from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import ContentPackRepository, DefinitionRepository, LinkedEntryRepository
from .search_index_repository import SearchIndexRepository


class CompendiumUnitOfWork:
    """Transaction boundary for multi-record compendium writes."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self.packs = ContentPackRepository(db)
        self.definitions = DefinitionRepository(db)
        self.links = LinkedEntryRepository(db)
        self.search_index = SearchIndexRepository(db)

    async def __aenter__(self) -> "CompendiumUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise

    async def rollback(self) -> None:
        await self._db.rollback()
