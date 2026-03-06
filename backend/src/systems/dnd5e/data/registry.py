"""
D&D 5e Compendium Registry.

In-memory slug → Definition lookup for monsters, spells, and items.
Populated by the CompendiumLoader at application startup.
"""

from __future__ import annotations

from typing import Optional, List

from ..schemas.definitions import (
    ItemDefinition,
    MonsterDefinition,
    SpellDefinition,
)


class CompendiumRegistry:
    """Thread-safe in-memory store for compendium definitions."""

    def __init__(self) -> None:
        self._monsters: dict[str, MonsterDefinition] = {}
        self._spells: dict[str, SpellDefinition] = {}
        self._items: dict[str, ItemDefinition] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_monster(self, definition: MonsterDefinition) -> None:
        self._monsters[definition.slug] = definition

    def register_spell(self, definition: SpellDefinition) -> None:
        self._spells[definition.slug] = definition

    def register_item(self, definition: ItemDefinition) -> None:
        self._items[definition.slug] = definition

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_monster(self, slug: str) -> Optional[MonsterDefinition]:
        return self._monsters.get(slug)

    def get_spell(self, slug: str) -> Optional[SpellDefinition]:
        return self._spells.get(slug)

    def get_item(self, slug: str) -> Optional[ItemDefinition]:
        return self._items.get(slug)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def count(self, entity_type: str) -> int:
        """Return the number of registered definitions of the given type."""
        store = self._get_store(entity_type)
        return len(store)

    def list_all(self, entity_type: str) -> list:
        """Return all registered definitions of the given type."""
        store = self._get_store(entity_type)
        return list(store.values())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_store(self, entity_type: str) -> dict:
        stores = {
            "monsters": self._monsters,
            "spells": self._spells,
            "items": self._items,
        }
        store = stores.get(entity_type)
        if store is None:
            raise ValueError(
                f"Unknown entity type: {entity_type}. "
                f"Valid types: {list(stores.keys())}"
            )
        return store
