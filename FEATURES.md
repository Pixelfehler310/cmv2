# Backend Feature Specification

This document summarizes the core functional domains and technical capabilities of the CMV2 backend.

## 1. Content Management System (CMS)
The foundation of the engine, providing a comprehensive CRUD (Create, Read, Update, Delete) pipeline for all game-rule definitions.
*   **Polymorphic Rule Definitions**: Native support for **Monsters**, **Spells**, **Items**, **Classes**, **Species**, **Backgrounds**, **Feats**, **Conditions**, and **Effects**.
*   **Mechanical Definitions**: Discrete persistence models for `ActionSpecs` and `OperationSpecs` to decouple logic from raw data.
*   **Recursive Linkage**: Maintains authoritative links between definitions (e.g., a Class referencing its specific Abilities).

## 2. Content Organization & Lifecycles
Framework for managing how content is grouped and versioned before it enters a campaign.
*   **Homebrew Content Packs**: User-authored rule collections with explicit ownership.
*   **Content Pack Lifecycle**: Support for Draft and Published states, ensuring stable rule-graphs for active campaigns.
*   **Version-Controlled Packs**: Enables reliable distribution and updates across multiple campaign instances.

## 3. Campaign Management
Orchestration for long-running narrative and mechanical sessions.
*   **Multi-Player Campaign Root**: Hierarchical state management for campaigns, members, and roles (DM/Player).
*   **Campaign Content Policies**: Fine-grained "Content Whitelisting," allowing DMs to control which rule packs are active in their world.
*   **Scene & Encounter Pre-Staging**: Preparing tactical environments and monster deployments ahead of live play.
*   **Narrative Journaling**: Persistent, rich-text tracking for session logs and player handouts.

## 4. Content Portability (Import/Export)
Bi-directional data movement for rule-sets and campaign state.
*   **Standardized Exchange Formats**: Native support for **JSON** and structured **ZIP** archives organized by definition type.
*   **SRD Data Pipeline**: Sophisticated mapping tools to ingest and normalize external rule-sets (like the D&D 5e SRD) into the engine's authoritative format.

## 5. Wiki, Link Resolution, & Search (CQRS)
The high-performance read-path for in-session rule discovery.
*   **Denormalized Search Index**: Millisecond-latency full-text search independent of the main transactional database.
*   **Recursive Graph Resolution**: Dynamically traversing complex link trees (e.g., "Find all abilities granted by the Level 3 Fighter class").
*   **Referential Integrity Checks**: Automatically detects and marks broken rule-links for easy correction.

## 6. Tactical Combat & Action Engine
The most complex logic layer, governing real-time game mechanics.
*   **Unified Turn Economy**: Automated tracking of Action, Bonus Action, Reaction, and Free Action budgets per turn.
*   **Action Execution Pipeline**: A sophisticated **Result Piping Engine** for resolving complex, multi-stage rules like life drain or conditional ability scaling.
*   **Hybrid Play Orchestration**: Supports `pending_choice` and `pending_roll` interrupts for seamless blending of automated and manual tactical play.

## 7. Spatial Map System
Visual and interactive environment management.
*   **Map Management**: Layered assets with metadata for tactical positioning and line-of-sight preparation.
*   **Interactive Scenes**: Links maps with campaign narrative context to create immersive roleplaying stages.

## 8. Comprehensive Character System
Authoritative source for character identity and state.
*   **Automated Character Sheets**: Real-time attribute calculation and derived state management (e.g., Base HP, Stats).
*   **Entity Bridging**: Direct integration with the Compendium for effortless rule referencing during combat and progression.
*   - **Inventory & Spellbook State**: Tracks prepared spells and item instances with stateful metadata (EQUIPPED, CHARGES).

## 9. User & Identity Domain
SaaS-grade identity and tenancy management.
*   **Multi-Tenant Isolation**: Secure, strictly separated user environments integrated with OAuth2/JWT authentication providers.
*   **Global User Profiles**: Persistent global settings and identity resolution across diverse campaigns.

## 10. Real-time Event Synchronization (WebSockets)
Low-latency communication layer for multi-player state consensus.
*   **Multiplexed Dispatcher**: Synchronizes Combat Events, Chat Logs, Map Position Updates, and System Notifications in real-time.
*   **Deterministic Event Contracts**: Standardized backend-to-frontend event payloads for reliable client-side state projection.
