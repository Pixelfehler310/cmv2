# What We Are Doing: CMV2 Horizontal Architecture Phase

This document provides a high-level summary of the current strategic focus for the CMV2 engine development.

## Current Phase: Horizontal-First Contracts

We are currently in a **Horizontal Planning** phase. This means we are defining the "Contracts" (the interfaces and data structures) for all core systems before deep-diving into the final implementations.

### Why?

- **Consistency**: To ensure that a "Monster" or "Spell" is understood identically by the Compendium, the Combat Engine, and the UI.
- **Modularity**: To allow different parts of the system to be developed in parallel without constant breakage.
- **Auditability**: To have a clear "Source of Truth" for how the game rules are mapped to code.

## Key Strategic Pillars

1.  **Contract-First**: Every feature starts with a Layer 1 contract in `01_contracts/`.
2.  **Horizontal Governance**: Adhering to the **Deep Conceptualization Gate**—no code before approved diagrams.
3.  **Standardized Diagramming**: Using **Mermaid** for all system maps and embedded logic flows to ensure native rendering and consistency.
4.  **Production Status Quarantine (PSQ)**: Protecting new "Gold" standards from "Bronze" legacy code.

## Active Priorities

- **D&D 5e Base Rule Schema**: Harvesting entities (Monsters, Spells, Items) from legacy prototypes and formalizing their new schemas.
- **Action Mechanics**: Defining how "Result Piping" and "Operation Payloads" work to make the combat engine platform-agnostic.
- **Repository Pattern Transition**: Moving from the storage-focused V05 implementation to service-oriented repository patterns.

---

> [!TIP]
> **Check the [Planning Overview](PLANNING_OVERVIEW.md)** for a visual map of how these components fit together.
