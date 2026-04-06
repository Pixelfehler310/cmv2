# Horizontal Module Overview

This folder now contains two complementary Mermaid diagrams.

1. Feature module map (logical architecture):
   - [ISSUES/architecture/01_contracts/overview/HORIZONTAL_MODULE_OVERVIEW.mmd](ISSUES/architecture/01_contracts/overview/HORIZONTAL_MODULE_OVERVIEW.mmd)
2. Detailed backend namespace map (Python package architecture):
   - [ISSUES/architecture/01_contracts/overview/HORIZONTAL_BACKEND_NAMESPACE_OVERVIEW.mmd](ISSUES/architecture/01_contracts/overview/HORIZONTAL_BACKEND_NAMESPACE_OVERVIEW.mmd)

Use the feature module map when discussing ownership boundaries, contracts, and cross-module dependencies.
Use the namespace map when discussing concrete backend package layout and migration of current code into target modules.

Legend summary:

- Active: green nodes.
- Implemented: blue nodes.
- Planned: yellow nodes.
- Feature Modules (Active and Implemented Core): current implementation and active architecture streams.
- Horizontal Contracts (Layer 1): shared domain contracts consumed by multiple feature modules.
- Infrastructure: shared platform resources (database, projection store, event stream, blob storage, telemetry).
- Planned Extensions (Separate Scope): explicitly separated V03, V04, and V06 namespaces and dependencies.
