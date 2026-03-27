# ISSUE [VERT][V05-01]: Baseline and Drift Audit

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V00]

## Why This Exists

V05 requires a verified baseline before contract freeze and ownership lock.
This issue captures current compendium behavior, linked-entry behavior, and contract drift risk so downstream V05 work starts from measured facts.

## Scope

In scope:

- Identify all definition-family CRUD paths currently reachable through REST and application services.
- Capture current payload shapes for list, detail, create, update, delete, and optional lifecycle transitions.
- Capture current linked-entry behavior (forward links, reverse references, missing references, cycle handling).
- Record baseline search/filter/sort behavior across large definition sets.
- Record baseline verification commands and expected outputs.

Out of scope:

- Changing behavior or schema.
- Introducing new APIs.

## Deliverables

1. Current-state path map for definition family flows:
   - transport handlers
   - application services
   - policy checks
   - repository writes
2. Baseline endpoint and contract matrix for scoped families:
   - spells
   - items
   - monsters
   - species
   - classes
   - feats
   - backgrounds
   - features
3. Linked-entry drift report covering:
   - unresolved references
   - ambiguous reference keys
   - replacement-link inconsistencies
   - cycle-risk paths
4. Baseline notes integrated into V05 planning docs.

## Acceptance Criteria

1. Every scoped CRUD path has one documented start and end point.
2. Baseline matrix includes request payload, response payload, reason-code behavior, and lifecycle-field behavior.
3. Linked-entry drift findings are explicit and severity-tagged.
4. Baseline commands run successfully in containerized workflow.
5. Findings are sufficient to support V05-02 and V05-03 without re-discovery.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/data -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -k compendium -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- Hidden fallback loaders can mask unresolved reference defects.
- If drift is material, V05-02 must include explicit break decisions.
