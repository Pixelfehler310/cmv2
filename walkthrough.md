# Walkthrough: Milestone 2.4 - Model Refinement & Data Ingestion

I have refactored the `Character` model to use proper relational data for Species, Class, and Background, and implemented the necessary supporting models and API endpoints.

## Changes

### 1. New Models (`backend/src/models/`)
- **`Species`**: Represents Race (e.g., Elf, Human). Includes traits, speed, size.
- **`ClassModel`**: Represents Class (e.g., Wizard). Includes hit die, proficiencies.
- **`Background`**: Represents Background (e.g., Sage). Includes skills, equipment.
- **`Feature`**: Represents a feature granted by Species/Class.
- **`Feat`**: Represents a selectable Feat.
- **`Faction`**: Represents a Faction.

### 2. Character Refactoring (`backend/src/models/character.py`)
- Replaced string fields (`race`, `class_name`, `background`) with Foreign Keys:
    - `species_id` -> `species.id`
    - `class_id` -> `classes.id`
    - `background_id` -> `backgrounds.id`
- Added relationships to eagerly load these entities.

### 3. API Updates (`backend/src/routers/`)
- **`definitions.py`**: New router for CRUD operations on Species, Classes, and Backgrounds.
- **`characters.py`**: Updated to accept IDs during creation and return nested objects in responses.

### 4. Effect Engine
- Updated `EffectEngine` to transparently delegate attribute access to the `template` if missing on the instance (e.g., `speed.walk` on a `MonsterInstance` resolves to `template.speed.walk`).

## Verification

I updated existing tests and added new ones:
- **`tests/test_definitions.py`**: Verifies creation of Species, Classes, and Backgrounds.
- **`tests/test_logic_routers.py`**: Verifies Character creation with linked entities.
- **`tests/test_effects.py`**: Verified Effect Engine works with new structure and nested attributes.

### Test Results
```
tests\test_advanced_data.py ....                                      [  5%]
tests\test_config.py .                                                [  7%] 
tests\test_definitions.py ...                                         [ 11%]
tests\test_effects.py ....                                            [ 17%] 
tests\test_instances.py .......                                       [ 27%]
tests\test_loader.py ..                                               [ 30%]
tests\test_logic_routers.py ......                                    [ 39%]
tests\test_logic_schemas.py ....                                      [ 45%] 
tests\test_main.py ..                                                 [ 48%]
tests\test_mechanics.py .......................                       [ 82%]
tests\test_routers.py ......                                          [ 91%]
tests\test_schemas.py ......                                          [100%]

============================ 68 passed in 1.14s ============================
```
