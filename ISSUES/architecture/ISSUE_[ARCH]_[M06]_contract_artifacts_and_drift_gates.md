# ISSUE [ARCH][M06]: Contract Artifacts and Drift Gates

Status: Planned
Owner: CI + Backend + Frontend Types
Depends on: ISSUE [ARCH][M00]

## Why This Exists

Architecture breaks silently when contracts drift.
This issue formalizes artifact generation and checks as first-class guardrails.

## Scope

In scope:

- Define authoritative artifacts (OpenAPI, generated frontend types, schema snapshots as needed).
- Ensure drift checks run in CI and local contributor workflow.
- Establish policy for versioned/breaking contract changes.

Out of scope:

- Full semantic versioning automation.

## Interface Focus

- Artifact generation interface (scripts and expected outputs).
- Drift check pass/fail contract in CI.
- Change classification contract (compatible vs breaking).

## Acceptance Criteria

1. Contract artifacts are reproducible and documented.
2. Drift checks are reliable and visible in CI.
3. Breaking contract changes require explicit annotation and migration note.
