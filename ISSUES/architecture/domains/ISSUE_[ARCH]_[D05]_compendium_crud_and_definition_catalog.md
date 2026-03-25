# ISSUE [ARCH][D05]: Compendium CRUD and Definition Catalog

Status: Planned
Owner: Data + Content Systems
Depends on: ISSUE [ARCH][D00]

## Why This Exists

Compendium operations are business-critical and broad (items, monsters, spells, features, feats).
This stream prevents broad CRUD work from leaking into unrelated combat/runtime architecture tasks.

## Scope

In scope:

- CRUD contracts per compendium definition family.
- Repository and endpoint consistency for definition catalogs.
- Validation and lifecycle alignment with content status fields.

Out of scope:

- Encounter runtime transitions.

## Related D2.9 Namespaces

- ApplicationLayer (CompendiumApplicationService)
- RepositoryLayer (CompendiumRepository)
- PersistenceDnd5e (ItemDefinitionRecord, MonsterDefinitionRecord, SpellDefinitionRecord, FeatureDefinitionRecord, FeatDefinitionRecord)

## Acceptance Criteria

1. CRUD behavior is contract-consistent across definition families.
2. Repository boundaries are explicit and test-covered.
3. API surface is complete for defined compendium entities.
