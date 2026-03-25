# ISSUE [ARCH][D04]: Content Schema and Content Pack Lifecycle

Status: Planned
Owner: Content Systems
Depends on: ISSUE [ARCH][D00]

## Why This Exists

D2.9 includes lifecycle-aware content models (draft, published, deprecated, archived).
This stream defines authoritative content contracts and pack versioning behavior.

## Scope

In scope:

- Action/effect/binding content definition contracts.
- Content pack metadata lifecycle transitions.
- Replacement/deprecation policy and migration notes.

Out of scope:

- Runtime combat state mutation behavior.

## Related D2.9 Namespaces

- ContentSchema
- ApplicationLayer (ContentPackApplicationService)
- RepositoryLayer (ContentRepository)
- PersistenceDnd5e (ActionDefinitionRecord, EffectDefinitionRecord)

## Acceptance Criteria

1. Lifecycle status transitions are explicit and validated.
2. Versioning metadata is consistent across contracts and persistence.
3. Contract drift checks cover content schema artifacts.
