# 02 - Compendium and Loader

## Overview

The `data` component isolates all read-only, statically defined game mechanics and encyclopedic data from the mutable combat runtime. It relies on the `CompendiumLoader` to parse Open5e-formatted JSON files into strongly-typed `pydantic` Definition models, which are then stored in-memory by the `CompendiumRegistry` at application startup.

## Core Concepts / Mechanics

### CompendiumLoader

- **Function**: Reads flat JSON data directly from the filesystem (often sourced from the Open5e SRD) and transforms it into structured objects.
- **Normalization**: Handles the necessary translation of loosely structured, occasionally inconsistent foreign JSON into strict, nested models (for instance, converting string-based challenge ratings into floats, or assembling `AbilityScores` and `SpeedBlock` sub-models).
- **Execution**: Invoked once during system bootstrapping. It walks the directory structures matching entity types (`monsters`, `spells`, `items`) and delegates to specific parsers (`_parse_monster`, `_parse_spell`, etc.).

### CompendiumRegistry

- **Function**: A thread-safe, in-memory lookup table that holds all hydrated Definition models.
- **Lookup mechanism**: Definitions are indexed and retrieved using a unique string identifier called a `slug` (e.g., `"adult-red-dragon"` or `"fireball"`).
- **Role**: Validates that any requested base definitions exist before they are instantiated into live `Instance` objects by systems like the Action Resolver or Character Builder.

## Key Schemas / Interfaces

### CompendiumLoader (`loader.py`)

Handles reading and parsing JSON definitions into structured engine models.

```python
class CompendiumLoader:
    def load_monster_file(self, path: str | Path) -> MonsterDefinition: ...
    def load_spell_file(self, path: str | Path) -> SpellDefinition: ...
    def load_item_file(self, path: str | Path) -> ItemDefinition: ...
    def load_directory(self, base_path: str | Path, entity_type: str = "monsters") -> int: ...
```

### CompendiumRegistry (`registry.py`)

Stores and retrieves engine schemas using a unique identifier.

```python
class CompendiumRegistry:
    def register_monster(self, definition: MonsterDefinition) -> None: ...
    def get_monster(self, slug: str) -> Optional[MonsterDefinition]: ...

    # Introspection
    def count(self, entity_type: str) -> int: ...
    def list_all(self, entity_type: str) -> list: ...
```

## Example Usage

```python
from systems.dnd5e.data.registry import CompendiumRegistry
from systems.dnd5e.data.loader import CompendiumLoader
from pathlib import Path

# 1. Initialize empty registry
registry = CompendiumRegistry()

# 2. Instruct loader to populate the registry from disk
loader = CompendiumLoader(registry)
loader.load_directory(Path("tests/fixtures/monsters"), "monsters")

# 3. Retrieve a read-only definition for use in the engine
goblin_def = registry.get_monster("goblin")
if goblin_def:
    print(f"Loaded {goblin_def.name} with AC {goblin_def.armor_class}")
```

## Dependencies

- **Requires**: `schemas.common`, `schemas.definitions`
- **Required By**: `engine.character_builder`, `routers` (for serving compendium lookups to the frontend), and any component hydrating an `ActorInstance` from a definition.
