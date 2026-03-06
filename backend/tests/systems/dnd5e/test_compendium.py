"""
Tests for D&D 5e Compendium Loader and Registry.

Validates that the loader correctly parses fixture files and
the registry provides slug-based lookup.
"""

from pathlib import Path

import pytest

from src.systems.dnd5e.data.registry import CompendiumRegistry
from src.systems.dnd5e.data.loader import CompendiumLoader


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def registry() -> CompendiumRegistry:
    return CompendiumRegistry()


@pytest.fixture
def loader(registry: CompendiumRegistry) -> CompendiumLoader:
    return CompendiumLoader(registry)


# ---------------------------------------------------------------------------
# Loader: Single File
# ---------------------------------------------------------------------------

class TestCompendiumLoader:

    def test_loader_parses_monster_file(self, loader: CompendiumLoader, registry: CompendiumRegistry):
        """Single monster file → MonsterDefinition registered in registry."""
        monster = loader.load_monster_file(FIXTURES / "monsters" / "adult-red-dragon.json")

        assert monster.name == "Adult Red Dragon"
        assert monster.slug == "adult-red-dragon"
        assert registry.count("monsters") == 1

    def test_loader_parses_spell_file(self, loader: CompendiumLoader, registry: CompendiumRegistry):
        """Single spell file → SpellDefinition registered in registry."""
        spell = loader.load_spell_file(FIXTURES / "spells" / "fireball.json")

        assert spell.name == "Fireball"
        assert spell.slug == "fireball"
        assert registry.count("spells") == 1

    def test_loader_parses_item_file(self, loader: CompendiumLoader, registry: CompendiumRegistry):
        """Single item file → ItemDefinition registered in registry."""
        item = loader.load_item_file(FIXTURES / "weapons" / "longsword.json")

        assert item.name == "Longsword"
        assert item.slug == "longsword"
        assert registry.count("items") == 1

    def test_loader_loads_monster_directory(self, loader: CompendiumLoader, registry: CompendiumRegistry):
        """Load all monster fixtures from directory."""
        count = loader.load_directory(FIXTURES / "monsters", entity_type="monsters")

        assert count == 2  # adult-red-dragon + goblin
        assert registry.count("monsters") == 2
        assert registry.get_monster("adult-red-dragon") is not None
        assert registry.get_monster("goblin") is not None

    def test_loader_loads_spell_directory(self, loader: CompendiumLoader, registry: CompendiumRegistry):
        """Load all spell fixtures from directory."""
        count = loader.load_directory(FIXTURES / "spells", entity_type="spells")

        assert count == 2  # fireball + cure-wounds
        assert registry.count("spells") == 2

    def test_loader_handles_nonexistent_directory(self, loader: CompendiumLoader):
        """Nonexistent directory returns 0 loaded."""
        count = loader.load_directory("/nonexistent/path", entity_type="monsters")
        assert count == 0


# ---------------------------------------------------------------------------
# Registry: Lookup
# ---------------------------------------------------------------------------

class TestCompendiumRegistry:

    def test_registry_lookup_by_slug(self, loader: CompendiumLoader, registry: CompendiumRegistry):
        """Lookup returns exact definition by slug."""
        loader.load_monster_file(FIXTURES / "monsters" / "adult-red-dragon.json")

        dragon = registry.get_monster("adult-red-dragon")
        assert dragon is not None
        assert dragon.name == "Adult Red Dragon"
        assert dragon.challenge_rating == 17.0

    def test_registry_lookup_missing_returns_none(self, registry: CompendiumRegistry):
        """Lookup for nonexistent slug returns None."""
        assert registry.get_monster("nonexistent-slug") is None
        assert registry.get_spell("nonexistent-slug") is None
        assert registry.get_item("nonexistent-slug") is None

    def test_registry_count_empty(self, registry: CompendiumRegistry):
        """Empty registry has count 0 for all types."""
        assert registry.count("monsters") == 0
        assert registry.count("spells") == 0
        assert registry.count("items") == 0

    def test_registry_count_after_loading(self, loader: CompendiumLoader, registry: CompendiumRegistry):
        """Count reflects loaded entities."""
        loader.load_monster_file(FIXTURES / "monsters" / "adult-red-dragon.json")
        loader.load_monster_file(FIXTURES / "monsters" / "goblin.json")
        loader.load_spell_file(FIXTURES / "spells" / "fireball.json")

        assert registry.count("monsters") == 2
        assert registry.count("spells") == 1
        assert registry.count("items") == 0

    def test_registry_list_all(self, loader: CompendiumLoader, registry: CompendiumRegistry):
        """list_all returns all registered definitions."""
        loader.load_directory(FIXTURES / "monsters", entity_type="monsters")

        all_monsters = registry.list_all("monsters")
        assert len(all_monsters) == 2
        names = {m.name for m in all_monsters}
        assert "Adult Red Dragon" in names
        assert "Goblin" in names

    def test_registry_invalid_entity_type_raises(self, registry: CompendiumRegistry):
        """Invalid entity type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown entity type"):
            registry.count("potions")
