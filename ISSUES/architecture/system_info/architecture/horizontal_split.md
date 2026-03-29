# Architectural Decision: The Horizontal Split (Decomposing V05 & V02)

## Context
The legacy "Vertical Legacy" modules (V02 and V05) were designed as feature-complete silos. while this allowed for rapid prototyping, it created tight coupling between game rules, execution logic, and persistence.

To transition to a production-ready **Horizontal-First** architecture, we are decomposing these silos into discrete domain-driven horizontal layers.

## The Problem with Vertical Silos
- **V05 (Compendium)**: Combined rule definitions (What a monster IS) with CRUD logic (How we SAVE it). This made it hard to use rules in combat without dragging in persistence-heavy logic.
- **V02 (Combat)**: Combined runtime state (HP/Initiative) with the "physics" of the game (Damage resolution). This made the engine non-deterministic and hard to test in isolation.

## The Solution: Horizontal Domain Mapping

We have mapped all concerns from V05 and V02 into four **Layer 1 (Contract)** domains:

### D1: Rule Schema (Extracted from V05)
- **Responsibility**: Define the "What". Canonical data shapes for Monsters, Spells, Items, and Lore.
- **Form**: JSON-Schema or Pydantic models.
- **Benefit**: Compendium and Combat Engine now speak the same "language".

### D2: Action Mechanics (Extracted from V02)
- **Responsibility**: Define the "How". Operation Specs (Attack, Save, Damage) and Result Piping logic.
- **Form**: Generic operation handlers and value resolvers.
- **Benefit**: Actions are now platform-agnostic and deterministic.

### D3: State & Runtime (Extracted from V02)
- **Responsibility**: Define the "Where". Actor runtime attributes, turn budgets, and effect instances.
- **Form**: Minimal state containers.
- **Benefit**: State can be snapshotted, replayed, and synchronized across clients without rules business logic interference.

### D4: Session & Bridge (Extracted from V05)
- **Responsibility**: Define the "Who". Identity, campaign context, and event envelopes.
- **Form**: WebSocket protocol definitions and API contracts.

## Implementation Pattern
- **Layer 1 (Contracts)**: Reside in `ISSUES/architecture/01_contracts/`. These are the source of truth.
- **Layer 2 (Implementations)**: Reside in `backend/src/systems/dnd5e/`. These implement the logic defined in Layer 1.

> [!NOTE]
> This split enables the **T-Shaped Roadmap**: we can solidify D1 and D2 (Horizontal depth) before we finish the full Compendium CRUD (Vertical depth).
