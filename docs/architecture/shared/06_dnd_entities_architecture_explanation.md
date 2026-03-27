# D&D Entities Target Architecture (V05 & V02/V01 Mapping)

This document provides a comprehensive overview of the core D&D entities, mapping how static game rules (Compendium Definitions) translate into mutable runtime sessions (Encounters and Combat).

See the accompanying `06_dnd_entities_class_diagram.mmd` for the visual structure.

## Architectural Domains

### 1. Compendium Static Domain (V05)
This domain acts as the absolute source of truth for all rules (Spells, Monsters, Classes, Feats). These records are **static**, intended to remain immutable during combat, and collectively form the catalog of the universe.
- **`DefinitionRecord`**: The foundational schema representing any distinct mechanic or rule. Its `family` determines its exact payload shape (e.g., a "spell" payload differs from a "monster" payload).
- **`ContentPackRecord`**: A logical grouping or "book" of definitions (e.g., Player's Handbook, Custom Homebrew Pack). Modules can be activated or deactivated per campaign.
- **`LinkedEntryReference`**: Maintains referential integrity between definitions (e.g., a specific Class level **grants** a Feature, a Feat has a **prerequisite** of a certain level).
- **`ReplacementChain`**: Allows custom or updated rules to gracefully replace older content without corrupting historical references.

### 2. Campaign Runtime Domain (V01)
This domain tracks the macro-level state of a game playthrough. It does not concern itself with momentary actions or numeric HP values; it acts as the context boundary for "where are the players" and "what narrative phase are we in."
- **`CampaignRuntimeAggregate`**: The root instance for a group's playthrough. Tracks the current active scene and acts as the largest persistence boundary.
- **`SceneRuntimeAggregate`**: A specific location, map, or narratological beat. Scenes can contain maps, ambiance, and a specific lifecycle state (e.g., toggling into combat).

### 3. Combat Execution Domain (V02)
This domain manages the highly mutable, turn-by-turn state of actors during an encounter. Everything here is considered an "instance" that relies on a `DefinitionRecord` for its base properties but sustains its own transient lifecycle.
- **`CombatEncounterRuntime`**: The active combat instance running within a Scene. Tracks global event ticks, current round, and initiative order.
- **`CombatActorRuntime`**: Any participant in combat (player character, monster, familiar). It is instantiated via a "Monster" or "Character" `DefinitionRecord`, establishing baseline stats, while maintaining `hp_current`, `concentration`, and other fluctuating markers.
- **`TurnBudgetRuntime`**: Embedded directly within an actor to strictly regulate their semantic Action Economy (Actions, Bonus Actions, Reactions, Movement) for their current turn.
- **`EffectInstanceRuntime`**: An active buff, debuff, or condition. If a player casts "Bless" (a `DefinitionRecord` Spell), it applies an `EffectInstanceRuntime` on the targets to alter subsequent mechanical equations.
- **`ZoneEffectRuntime`**: Represents an active environmental area of effect projected onto the board (e.g., "Web"). It geometrically evaluates who is inside it to trigger ongoing consequence operations.

### 4. Action Processing Domain (V02)
This domain acts as the "verb pipeline" connecting static definitions and runtime actors. It translates a player's intent to use a rule into deterministic, cascading mechanics on the board.
- **`ActionExecutionRequest`**: Represents a player declaring an intent ("I use this Action/Spell"). It always points back to a `DefinitionRecord` as its origin constraint and requests spending a portion of the actor's `TurnBudgetRuntime`.
- **`ActionOperationSpec`**: The granular, mechanical breakdown of the declared action into exact computational steps (e.g., Step 1: Force Dexterity Save, Step 2: Deal 8d6 Fire Damage, Step 3: Instantiate a ZoneEffectRuntime).

## The Entity Lifecycle Workflow

1. A DM creates an Encounter inside a **`SceneRuntimeAggregate`**.
2. Monsters are spawned into the **`CombatEncounterRuntime`** as mutable **`CombatActorRuntime`** instances, extracting their fixed stats from a `monster` **`DefinitionRecord`**.
3. A player's turn begins. Their **`TurnBudgetRuntime`** validates resources and resets.
4. The player declares they are casting *Fireball*. The client dispatches an **`ActionExecutionRequest`**, statically referencing the *Fireball* **`DefinitionRecord`**.
5. The backend validates the request logic, consumes the player's Action budget, and unpacks the *Fireball* payload into a sequential graph of **`ActionOperationSpec`** steps.
6. The compiled operations definitively resolve, directly mutating targeted **`CombatActorRuntime`** HP values or generating secondary artifacts like a **`ZoneEffectRuntime`**.
7. State integrity resolves and updates correspond back to connected clients.
