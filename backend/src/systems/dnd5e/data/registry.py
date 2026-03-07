"""
D&D 5e Compendium Registry.

In-memory slug → Definition lookup for monsters, spells, items,
races, classes, and backgrounds.
Populated by the CompendiumLoader at application startup.
"""

from __future__ import annotations

from typing import Optional, List

from ..schemas.definitions import (
    BackgroundDefinition,
    ClassDefinition,
    ItemDefinition,
    MonsterDefinition,
    RaceDefinition,
    SpellDefinition,
)


class CompendiumLookupError(Exception):
    """Raised when a compendium slug cannot be resolved."""


class CompendiumRegistry:
    """Thread-safe in-memory store for compendium definitions."""

    def __init__(self) -> None:
        self._monsters: dict[str, MonsterDefinition] = {}
        self._spells: dict[str, SpellDefinition] = {}
        self._items: dict[str, ItemDefinition] = {}
        self._races: dict[str, RaceDefinition] = {}
        self._classes: dict[str, ClassDefinition] = {}
        self._backgrounds: dict[str, BackgroundDefinition] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_monster(self, definition: MonsterDefinition) -> None:
        self._monsters[definition.slug] = definition

    def register_spell(self, definition: SpellDefinition) -> None:
        self._spells[definition.slug] = definition

    def register_item(self, definition: ItemDefinition) -> None:
        self._items[definition.slug] = definition

    def register_race(self, definition: RaceDefinition) -> None:
        self._races[definition.slug] = definition

    def register_class(self, definition: ClassDefinition) -> None:
        self._classes[definition.slug] = definition

    def register_background(self, definition: BackgroundDefinition) -> None:
        self._backgrounds[definition.slug] = definition

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_monster(self, slug: str) -> Optional[MonsterDefinition]:
        return self._monsters.get(slug)

    def get_spell(self, slug: str) -> Optional[SpellDefinition]:
        return self._spells.get(slug)

    def get_item(self, slug: str) -> Optional[ItemDefinition]:
        return self._items.get(slug)

    def get_race(self, slug: str) -> Optional[RaceDefinition]:
        return self._races.get(slug)

    def get_class(self, slug: str) -> Optional[ClassDefinition]:
        return self._classes.get(slug)

    def get_background(self, slug: str) -> Optional[BackgroundDefinition]:
        return self._backgrounds.get(slug)

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
            "races": self._races,
            "classes": self._classes,
            "backgrounds": self._backgrounds,
        }
        store = stores.get(entity_type)
        if store is None:
            raise ValueError(
                f"Unknown entity type: {entity_type}. "
                f"Valid types: {list(stores.keys())}"
            )
        return store
