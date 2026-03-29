# V05 Architecture Q&A Analysis

This document serves as a backup of the architectural analysis regarding the V05 structural diagrams.

### 1. Are the in-between interfaces clear and correct?
**Generally Yes, but with one critical gap.** 
The interfaces between the "Write Path" (Compendium CRUD) and the "Read Path" (Query & Projection) are extremely robust. The use of `LinkedEntryReference` instead of hardcoded nested objects cleanly splits the domains.
**The Gap:** The boundary between the `ContentCatalogDomain` (V05) and `IntegrationBoundariesV2` (The Combat Engine) needs strict definition. We mapped out that `MonsterDefinition` translates to a `CombatActorRuntime`, but the interface for translating an `ActionOperationSpec` into a V2 executable event is opaque. V05 just stores the payload, but V2 needs to parse it. 

### 2. Are the processes clear?
**Yes.** The flow of data is well-articulated. The lifecycle of a `DefinitionRecord` (Draft -> Published -> Archived) and how it passes through the `V05ProjectionGate` for linked-entry resolution provides a clear pipeline. 
**Watch Out:** The process for "Homebrew branching" (e.g., a player cloning a Longsword to make a custom weapon) is clear in the DB layer, but we must be careful with how ID generation is handled so we don't accidentally duplicate `LinkedEntryReference`s that point to global, non-homebrew rules.

### 3. Do we really have all the objects and classes that we need?
We have about **95%** of the core classes mapped out. However, reviewing the rules of D&D, there are a few missing puzzle pieces that normally force "hacky" JSON payloads if not defined early:
- **`ConditionDefinition`:** (e.g., Blinded, Poisoned). Right now, conditions aren't explicitly cataloged alongside spells or items. They need to belong to the Compendium so `ActionOperationSpec`s can formally link to them.
- **`ModifierSpec` Contracts:** How do we represent passive effects (e.g., "+1 to AC")? The `AbilityDefinition.passive_effects` is currently an ambiguous list. We need a strict schema for modifiers.

### 4. Do we need a specification document for features to enhance clarity and test writing?
**Absolutely YES.** 
The architecture diagrams dictate *how* the data moves, but not *what* the data is. Without a dedicated "Feature & Mechanics Specification Document", `ActionOperationSpec`, `passive_effects`, and `payload` will become dumping grounds for unstructured JSON. 
We need a document that defines the exact schema of a "Melee Attack", a "Saving Throw Spell", and a "Healing Action". If we do not write this specification, testing the V2 engine will be impossible because the mock data will become inconsistent.

### 5. Should we implement all 3 in one big PR / Issue, or split it even further?
**Split it.** 
Attempting to implement Identity, Compendium CRUD, Campaign State, and Linked Resolution in a single PR will create a massive, unreviewable monolith. We should heavily lean into the "Vertical Slice" issues you've already templated (`V05-01` through `V05-07`).
1. **Slice 1 (V05-02 & 03):** Implement *just* the pure Pydantic Domain Models and validation. (No databases, no API routes).
2. **Slice 2 (V05-04):** Implement the CRUD repositories and FastAPI routes for the Compendium.
3. **Slice 3 (V05-06):** Implement the Linked Entry Resolution and Projection logic.
4. **Slice 4:** Move onto Campaign & Character persistence domains.

### 6. Do we still have major structural flaws in the current process?
**The "Linked Resolution Cycle" is a major risk.**
The `V05_content_management_query_and_projection_detailed_plan.mmd` mentions "Cycle Denial". If a `Class` grants an `Ability`, and someone accidentally configures that `Ability` to act as a prerequisite for the `Class`, it creates an infinite loop. While the architecture acknowledges this, recursive SQL relationships (or MongoDB graph lookups) are computationally expensive and prone to crashing the server if the safeguards fail. We will need rigorous unit tests on the `LinkedEntry` integrity checks before *any* data is saved to the DB.

### 7. How does this apply to our current structure? Adapt or Replace?
**Completely Replace the Data Layer.**
Do not try to adapt the old `backend/src/schemas` and `backend/src/data` layers. The `v05_migration_notes.md` explicitly calls out heavy schema drift and "severe structural coupling" in the old code. 

If we try to morph the old schemas into V05, we will drag legacy tech-debt (hardcoded arrays, mixed UI-state concepts) into the pristine new architecture. 

**The recommended approach (The Strangler Pattern):**
1. Leave the current V1/V2 endpoints and `schemas/` folder entirely alone so the project still successfully builds and runs today.
2. Build V05 in the new `backend/src/modules/` directory side-by-side (Domain-Driven Design).
3. Build the new FastAPI endpoints under an `/api/v5/` prefix.
4. Once the `/api/v5/` compendium works and the frontend is updated to read from it, delete the old `schemas/` and legacy endpoints. 
