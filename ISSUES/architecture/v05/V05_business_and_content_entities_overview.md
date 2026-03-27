# V05 Business & Content Entities Architecture Overview

This document provides a comprehensive breakdown of the `V05_business_and_content_entities_class_diagram.mmd`. While earlier V05 diagrams focused on the CRUD pipeline and search indexing, this document defines the overarching **Domain Models**—illustrating how SaaS identity, persistent state, campaigns, and rule compendiums all interlock.

## 1. User & Identity Domain
The core foundation of the application as a multi-tenant SaaS.

*   **`UserAccount`**: The absolute root identity. Authenticable via standard providers (OAuth/JWT). 
*   **`UserSubscription`**: Manages tier limits (e.g., storage for assets, number of concurrent campaigns).
*   **`ContentEntitlement`**: The bridge between a user's wallet/library and the game's static content. It grants explicit read/use access to specific `ContentPackRecord`s.

## 2. Asset Management Domain
Virtual Tabletop features require extensive handling of rich media.

*   **`AssetRecord`**: Metadata and storage pointers for user uploads (maps, tokens, audio). This links back to the `UserAccount` via quota limits defined in the `UserSubscription`.
*   **`AssetFolder`**: Simple hierarchical structure allowing users to organize their uploaded media organically.

## 3. Content Catalog Domain (V05 Core)
The "Platonic Ideals" of the game's rules. This expands upon the original V05 compendium index by defining the distinct inheritance structure of the `DefinitionRecord`.

*   **`DefinitionRecord` (Abstract)**: The universal base class containing canonical UUIDs, versions, and naming conventions.
*   **Consolidation of Abilities (`AbilityDefinition`)**: In this architecture, both *Feats* and *Class Features* share an identical schema. Both grant secondary stats, introduce passive effects, or unlock `ActionOperationSpec` elements for the V02 execution engine. Therefore, they are merged under one definition type to reduce schema fragmentation.
*   **`ContentPackRecord`**: The boundary container. Note that **Homebrew** is treated simply as a `ContentPackRecord` where `author_user_id` is populated and `lifecycle_state: draft` represents work-in-progress custom rules.

## 4. Campaign Domain
Where players congregate and narrative content is shaped.

*   **`CampaignMember`**: Resolves the "Contextual Identity" pattern. A user might be a typical `UserAccount` globally, but within a `Campaign`, they are assigned a `role` (DM or Player) and an `active_character_id`.
*   **`CampaignContentPolicy`**: A critical security/validation boundary. It dictatates which `ContentPackRecord`s the V05 API allows into the game session. If a DM disables "Tasha's Cauldron", the system prevents players from selecting those `DefinitionRecord`s.
*   **`Scene` & `PlannedEncounter`**: The narrative framing. The DM sets up maps (`AssetRecord`), writes notes (`JournalEntry`), and queues up monsters (`PlannedEncounter`), before eventually pushing the state into V02's `CombatEncounterRuntime`.

## 5. Character Domain (Persistent State)
The aggregation of thousands of rule-nodes into a single identity over time.

*   **`PlayerCharacterSheet`**: The static, out-of-combat anchor for a character. It doesn't track momentary buffs or turn budgets (that belongs to V02), but instead tracks permanent metrics (Base HP, Stats).
*   **The Content Bridge**: Classes like `CharacterProgression` act as massive relational nodes, directly pointing to `SpeciesDefinition`, `BackgroundDefinition`, `ClassDefinition`, and lists of `AbilityDefinition`s.
*   **`ItemInstance`**: When a character pulls a "Longsword" from the compendium (`ItemDefinition`), it becomes an `ItemInstance`. It gains unique metadata (`is_equipped`, `custom_name`) but still delegates base mechanics back to the definition.

## 6. Integration Boundaries with V02 (Action Engine)
The diagram highlights exactly where V05's persistence ends and V02's ephemeral execution begins:

1.  **Map to Board**: A `Scene` is persistent. When combat breaks out, the backend spawns a `CombatEncounterRuntime` (V02) initialized with the Scene's parameters.
2.  **Sheet to Actor**: A `PlayerCharacterSheet` pushes its calculated stats into a lightweight `CombatActorRuntime`. This actor can gain concentration, take damage, and apply conditions without mutating the core `PlayerCharacterSheet` database directly.
3.  **Template to Actor**: When a `PlannedEncounter` injects a goblin (`MonsterDefinition`), it skips the player character lifecycle entirely and instantiates directly into a `CombatActorRuntime`.

## Iteration & Extension
This domain map is designed to be iterated on. If the platform requires complex faction tracking, quest logs, or marketplace monetization, they can seamlessly attach to standard extension points on the `Campaign` or `UserAccount` nodes respectively.
