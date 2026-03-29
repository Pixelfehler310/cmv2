# ISSUE: Generic CI/CD Docs Freshness Warning Workflow

Status: Planned  
Owner: DevEx / CI

## Goal

Add a generic CI/CD warning workflow that flags stale architecture/specification docs without blocking merges.

## Problem Statement

Documentation quality is acceptable for MVP when refreshed periodically, but there is currently no automated reminder in CI when docs become stale.

This creates risk that DB/event/architecture docs lag behind implementation over time.

## Scope

In scope:

- Add a CI step that checks document age for selected canonical docs.
- Emit warnings (not failures) when docs exceed a configured age threshold.
- Keep implementation generic so additional docs can be added easily.

Out of scope:

- Automatic documentation generation.
- Hard merge blocking on docs staleness.
- Schema hash drift enforcement (future enhancement).

## Initial Target Documents

- docs/documentation/database_erm_specification.md
- docs/documentation/event_specification.md

## Proposed Implementation

1. Add a script:

- backend/scripts/check_docs_freshness.py

2. Script behavior:

- Read configured file list.
- Parse a metadata line, for example:
  - Last reviewed: YYYY-MM-DD
- Compare with current UTC date.
- If document age > threshold (for example 30 days), print warning message.
- Emit GitHub Actions annotation warnings for visibility in PR checks.

3. CI integration:

- Add a workflow step in existing backend/general CI pipeline.
- Run checker in warning mode (non-blocking).

4. Configuration:

- Threshold via CLI arg or env var (default 30 days).
- Document list from script constant or simple config file.

## Acceptance Criteria

1. CI run shows explicit warning when a target doc is older than threshold.
2. CI run passes (non-blocking) even when warnings are present.
3. Warning includes file path, age in days, threshold, and refresh guidance.
4. Adding a new tracked doc requires minimal config change.

## Future Enhancements

1. Optional strict mode for protected branches.
2. Optional schema/model-hash drift check to complement age warning.
3. Optional auto-comment on PR when warnings are present.

## Verification

1. Set one target doc date to an old date and run checker locally.
2. Confirm warning output includes file and age details.
3. Run in CI and verify GitHub annotation is visible.
4. Restore valid date and confirm warning disappears.
