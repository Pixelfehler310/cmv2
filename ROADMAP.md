# Backend Development Roadmap

## Project Strategy
Our backend development follows a **Vertical Modularization** strategy, creating deep functional slices that isolate architectural domains into testable, high-integrity modules.

---

## Phase 1: Foundation & Runtime Lifecycle (V01)
*   **Status:** In Progress (Audit & Contract Freeze)
*   **Key Milestones:**
    *   [x] Campaign/Scene Persistence Hierarchy
    *   [x] State Ownership Handoff Protocols
    *   [ ] Scene Transition WS Dispatcher (In-Prep)
    *   [ ] Vertical Quality Gate (V01-06)

## Phase 2: Core Combat & Action Engine (V02)
*   **Status:** Planned
*   **Key Milestones:**
    *   [ ] Command-Based Action Resolution Spec
    *   [ ] Real-time Turn Budget Integration
    *   [ ] Automation for Effect/Condition Lifecycles
    *   [ ] Deterministic Tactical Verification Suite

## Phase 3: World Context & Narrative (V03)
*   **Status:** Planned
*   **Key Milestones:**
    *   [ ] Faction/Regional Identity Models
    *   [ ] NPC State & Relationship Invariants
    *   [ ] Campaign Journaling & Narrative Storage
    *   [ ] World Context Application Services

## Phase 4: Content Infrastructure & Schema (V04)
*   **Status:** Planned
*   **Key Milestones:**
    *   [ ] Definitional Pydantic Contract Stabilization
    *   [ ] Version-Controlled Content Pack Distribution
    *   [ ] Action/Operation Blueprint Protocols
    *   [ ] Content Schema Drift Monitoring

## Phase 5: Digital Compendium & Data Services (V05)
*   **Status:** Active Implementation (Current Focus)
*   **Key Milestones:**
    *   [x] Multi-Family Definition CRUD Orchestration
    *   [x] Linked Entry Recursive Resolution Engine
    *   [ ] High-Concurrency Search Index Projections
    *   [ ] Asset Management Domain Unification
    *   [ ] Compendium E2E Test Matrix (V05-07)

## Phase 6: UI Sync & Event Contracts (V06)
*   **Status:** Active Planning (Prep Phase)
*   **Key Milestones:**
    *   [ ] Deterministic Event Payload Stabilization
    *   [ ] Frontend Projection/Read-Model Store Definitions
    *   [ ] Multiplexed WebSocket Message Framing
    *   [ ] End-to-End State Consensus Verification

---

## Core Infrastructure Roadmap (Cross-Phase)

### Persistence & Data
- [x] Async SQLAlchemy + SQLModel Integration
- [x] Alembic Database Migration Pipeline
- [ ] Multi-Tenant Data Isolation (Identity-Link)

### API & Real-time
- [x] Unified REST/WebSocket Routing
- [x] Multiplexed Action Dispatching
- [ ] Cross-Domain Event-Bus (In-Service)

### Quality & Performance
- [x] Postgres Testcontainer Integration
- [ ] 85%+ Coverage Gate for Domain Systems
- [ ] Millisecond-Latency Search Path
