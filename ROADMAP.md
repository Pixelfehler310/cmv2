# Backend Development Roadmap

## Project Strategy
Our backend development follows a **Vertical Modularization** strategy, creating deep functional slices that isolate architectural domains into testable, high-integrity modules.

---

## Phase 1: Foundation & CMS (V01)
*   **Status:** In Progress (Audit & Contract Freeze)
*   **Key Milestones:**
    *   [x] Campaign/Scene Persistence Hierarchy
    *   [x] Universal Definition Base Schema
    *   [ ] CMS Definition CRUD for core types (InProgress)
    *   [ ] Vertical Quality Gate (V01-06)

## Phase 2: Core Combat & Action Engine (V02)
*   **Status:** Planned
*   **Key Milestones:**
    *   [ ] Result Piping & Action Pipeline Spec
    *   [ ] Turn Economy & Resource Budget Integration
    *   [ ] Hybrid Play Logic (PendingChoice/Roll)
    *   [ ] Deterministic Tactical Verification Suite

## Phase 3: World & Context Management (V03)
*   **Status:** Planned
*   **Key Milestones:**
    *   [ ] Faction/Regional Identity Models
    *   [ ] Narrative Journaling & Storage
    *   [ ] Map System & Spatial Layers (Prep)
    *   [ ] World Context Application Services

## Phase 4: Content Portability & Schema (V04)
*   **Status:** Planned
*   **Key Milestones:**
    *   [ ] JSON/ZIP Import & Export Protocols
    *   [ ] Version-Controlled Content Pack Distribution
    *   [ ] Action/Operation Blueprint Protocols
    *   [ ] Content Schema Drift Monitoring

## Phase 5: Digital Compendium & Data Services (V05)
*   **Status:** Active Implementation (Current Focus)
*   **Key Milestones:**
    *   [x] Multi-Family Definition CRUD Orchestration
    *   [x] Linked Entry Recursive Resolution Engine
    *   [ ] CQRS Search Index Projections (Millisecond Read-Path)
    *   [ ] Compendium E2E Test Matrix (V05-07)

## Phase 6: UI Sync & Event Contracts (V06)
*   **Status:** Active Planning (Prep Phase)
*   **Key Milestones:**
    *   [ ] Multiplexed WebSocket Message Framing (Chat/Logs)
    *   [ ] Deterministic Event Payload Stabilization
    *   [ ] Frontend Projection/Read-Model Store Definitions
    *   [ ] End-to-End State Consensus Verification

---

## Core Infrastructure Roadmap (Cross-Phase)

### Persistence & Data
- [x] Async SQLAlchemy + SQLModel Integration
- [x] Alembic Database Migration Pipeline
- [ ] Multi-Tenant SaaS Isolation (Identity-Link)

### API & Real-time
- [x] Unified REST/WebSocket Routing
- [x] Multiplexed Action Dispatching
- [ ] Cross-Domain Event-Bus (In-Service)

### Quality & Performance
- [x] Postgres Testcontainer Integration
- [ ] 85%+ Coverage Gate for Domain Systems
- [ ] Millisecond-Latency Search Path
