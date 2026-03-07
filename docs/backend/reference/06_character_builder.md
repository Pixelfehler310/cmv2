# 06. Character Builder

## 1. Overview

The Character Builder operates as a distinct standalone module outside the core real-time combat systems. Its primary objective is to ingest a loosely defined `CharacterCreationBlueprint` detailing a player's choices and, utilizing the `CompendiumRegistry`, construct a fully articulated, mechanically sound `ActorInstance` ready for immediate use in an encounter.

## 2. Core Concepts / Mechanics

- **Definition Resolution & Hydration**: The builder reaches into the cross-system `CompendiumRegistry` to pull raw `RaceDefinition`, `ClassDefinition`, and `BackgroundDefinition` data structures tied to the specific string slugs selected by the user.
- **Derived Math & Attributes**: Raw ability scores are passed before racial bonuses. The builder natively merges the race's modifiers, calculates the resulting hit points using PHB averages alongside CON modifiers, sets foundational hit point bounds, and calculates proficiency bonuses dynamically based on character level.
- **Skill & Saving Throw Synthesis**: Synthesizes the explicit saving throw proficiencies natively granted by the selected class, merging them with the background skill proficiencies and whatever floating skill choices the user made, inherently deduplicating overlapping selections.
- **Spellcasting Matrix**: If the target class definition designates a `SpellcastingProgression`, the engine cross-references the casting type (`full`, `half`, `third`) with hardcoded PHB spell slot progression tables. It computes intrinsic spell save DCs and attack bonuses according to the class's casting ability modifier.
- **Feature Translation**: Scans class `LevelFeature` elements up to the character's target level. The raw effects housed inside these features are translated into permanent `EffectInstance` objects and injected into the target `ActorInstance`.

## 3. Key Schemas / Interfaces

- **`CharacterCreationBlueprint`**: The simplified input payload. Exposes foundational details such as `name`, `level`, raw `base_abilities`, and the defining slugs (`race_slug`, `class_slug`, `background_slug`).
- **`SpellcastingState`**: Derived by the builder for magical classes, tracking maximum and available spell slots across spell levels 1–9, plus the `spell_save_dc` and `spell_attack_bonus`.
- **`CharacterBuilder`**: A class instantiated with a `CompendiumRegistry` reference. Exposes the singular `.build(blueprint)` orchestrator method.

## 4. Example Usage

```python
from systems.dnd5e.engine.character_builder import CharacterBuilder
from systems.dnd5e.schemas.creation import CharacterCreationBlueprint
from systems.dnd5e.schemas.common import AbilityScores

# Assuming 'registry' is a loaded CompendiumRegistry instance
builder = CharacterBuilder(registry)

blueprint = CharacterCreationBlueprint(
    name="Thrall",
    race_slug="half-orc",
    class_slug="barbarian",
    background_slug="outlander",
    level=3,
    base_abilities=AbilityScores(
        strength=15,
        dexterity=14,
        constitution=14,
        intelligence=8,
        wisdom=12,
        charisma=10
    ),
    chosen_skills=["athletics", "survival"]
)

# Convert blueprint into a combat-ready ActorInstance
thrall_actor = builder.build(blueprint)
print(f"{thrall_actor.name} created with {thrall_actor.max_hp} HP!")
```

## 5. Dependencies

- `schemas/creation.py` (CharacterCreationBlueprint)
- `schemas/definitions.py` (BackgroundDefinition, ClassDefinition, RaceDefinition)
- `schemas/instances.py` (ActorInstance)
- `data/registry.py` (CompendiumRegistry)
- `engine/stat_calculator.py` (For applying calculating modifiers and proficiency bonuses)
