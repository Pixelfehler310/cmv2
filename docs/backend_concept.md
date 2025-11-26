# Backend Concept: The Modular Monolith

## 1. Architecture Principle: CQRS Light

We strictly separate between **Acting** and **Displaying**.

*   **Frontend is "Dumb":** It never calculates values (like HP or bonuses). It only sends **Commands** to the backend.
*   **Backend is "Smart":** It holds the state, executes rule logic, and sends back a finished **View Model** including explanations (calculation path).

## 2. Backend Services (Python)

Although implemented in a Monorepo, the backend is conceptually sliced into microservices.

### A. Data Service ("The Librarian")

*   **Responsibility:** Saving and loading static definitions (Items, Spells, Monster Templates).
*   **Feature: Mod Loader & Aggregator:**
    *   Loads JSON files from the file system (`/mods/...`).
    *   Merges them based on a load order (Core < Community < Homebrew).
    *   Delivers the final result via API.
*   **SRD 5.1 Integration:** Uses structured JSON dumps of the SRD as a Base Content Pack.

### B. Logic Service ("The Game Master")

*   **Responsibility:** Campaign state management. Execution of rules.
*   **Data Model (Adaptation):** Porting structures from `libsrd5` (C#) to Pydantic Models. Extending these models with an `effects` field.
*   **Core Piece: The Effect Engine:**
    *   An event-based system using JSON configurations instead of code.
    *   **Structure:** An effect has **Trigger** (WHEN: `ON_DAMAGE`), **Condition** (IF: `HP < 50%`), and **Operation** (THEN: `ADD +2`).
    *   **No-Code Modding:** Allows users to create complex Feats/Items by combining these JSON building blocks without programming Python.
    *   **Safe Eval:** Usage of `simpleeval` for safe evaluation of formula strings ("{level} / 2").

## 3. Development Workflow

*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **Validation:** Pydantic v2
*   **Testing:** `pytest` for logic unit tests and API integration tests (`TestClient`).
