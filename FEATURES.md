# Backend Features Breakdown

This document provides a granular view of the functional and architectural capabilities of the CMV2 backend.

## 1. Identity & Subscription Domain
*   **User Multi-Tenancy**: Securely isolates user data with OAuth2/JWT-based authentication and role-based access control.
*   **Subscription & Quota Management**: Enforces tiered resource limits for assets, concurrent campaigns, and storage quotas via user subscription records.
*   **Content Entitlements**: Manages granular read/use permissions, bridging a user's library with specific official or shared content packs.

## 2. Asset Management Domain
*   **Rich Media Library**: Provides high-performance metadata tracking and storage pointers for user-uploaded maps, tokens, and audio assets.
*   **Hierarchical Asset Organization**: Enables structured media management through a user-defined folder hierarchy.

## 3. Compendium & Rules Domain
*   **Universal Rule Schema**: Standardizes the data structures for all game rules (Classes, Species, Items, Spells) into a consistent, versioned inheritance model.
*   **Referential Integrity (Linked Entries)**: Formally enforces relationships between game rules, such as a Class granting specific Abilities at certain levels.
*   **Action & Operation Specifications**: Uses strictly typed mechanical definitions for attacks, saves, and healing to decouple execution logic from raw data.
*   **Lore & World-Building Catalog**: Provides a searchable database for narrative elements like Factions, Regions, Places, and Deities that exist independently of specific campaigns.
*   **Content Pack Lifecycle**: Supports the full lifecycle of "Homebrew" content, from private drafts to versioned, published packs.
*   **Search & Discovery (CQRS)**: Implements a denormalized read-path for millisecond-latency lookup of rules and definitions across the entire catalog.

## 4. Campaign & Session Domain
*   **Persistent Campaign Root**: Manages the multi-player session lifecycle, resolving DM and Player roles and tracking long-term playthrough state.
*   **Campaign Content Policy**: Empowers DMs to control which content packs (official or custom) are available to players within a specific session.
*   **Scene & Encounter Preparation**: Allows pre-staging of maps, narrative nodes, and monster placements to streamline live session flow.
*   **Narrative Journaling**: Provides campaign-scoped rich-text tracking for session logs, player handouts, and DM secrets.

## 5. Character Sheet Domain
*   **Persistent Character Sheets**: Acts as the permanent, authoritative anchor for character stats, progression choices, and base metrics.
*   **Progression Engine**: Automatically calculates and applies adjustments from species, background, and class definitions to a character's core stats.
*   **Inventory & Spell Management**: Tracks unique instances of items and prepared spells, maintaining state like equipment status and custom names.

## 6. Tactical Combat Engine
*   **Runtime Lifecycle Orchestration**: Manages deterministic transitions between campaign exploration and active combat scenes.
*   **Command-Based Action Resolution**: Ensures tactical maneuvers, attacks, and spells are executed against valid targets with correct mechanical outcomes.
*   **Turn Economy & Resource Budgets**: Tracks real-time resource availability (Actions, Reactions) and prevents illegal action sequences.
*   **Effect & Condition Automation**: Handles the automated ticking, concentration checks, and expiration of status effects and conditions.

## Architectural Features (Backend Core)
*   **Async PostgreSQL Persistence**: Uses strongly-typed repository patterns with SQLAlchemy and Alembic migrations for robust data consistency.
*   **Async Application Services**: Orchestrates complex business logic and cross-domain invariants in a high-concurrency, non-blocking environment.
*   **Domain Validation & Invariants**: Enforces strict Pydantic-based contracts and business rules at the application boundary to prevent state corruption.
*   **Integrated Test Matrix**: Validates horizontal and vertical integration using automated test suites powered by Postgres Testcontainers.
*   **Multiplexed Event Dispatching**: Synchronizes real-time state across multiple clients using a high-performance WebSocket dispatcher.
*   **CQRS Read-Path Projections**: Maintains high-speed search indexes via asynchronous workers that project database mutations into flat, searchable documents.
