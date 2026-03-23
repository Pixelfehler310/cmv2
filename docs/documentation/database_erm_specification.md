# Database ERM Specification

Status: Drafted from codebase state on 2026-03-23  
Scope source: SQLAlchemy models and effective write paths in backend services/repositories

## 1. Purpose and Boundaries

This document is the authoritative ERM for persisted backend data in CMV2.

In scope:

- All SQLAlchemy-backed entities declared from Base.
- Relationship cardinalities (hard FK and soft logical links).
- Persistence ownership boundaries (who writes each aggregate).
- Drift notes where code-level behavior diverges from explicit schema constraints.

Out of scope:

- Frontend view-model types.
- In-memory encounter snapshots that are not written to SQL tables.

## 2. Canonical ER Diagram (Mermaid)

```mermaid
erDiagram
  users ||--o{ user_social_auths : has

  campaigns ||--o{ campaign_members : has
  campaigns ||--o{ characters : has
  users ||--o{ campaign_members : joins

  species ||--o{ characters : species_of
  classes ||--o{ characters : class_of
  backgrounds ||--o{ characters : background_of

  dnd5e_encounter_sessions ||--o{ dnd5e_combatant_states : contains
  dnd5e_encounter_sessions ||--o{ dnd5e_turn_budget_records : tracks
  dnd5e_encounter_sessions ||--o{ dnd5e_action_logs : logs
  dnd5e_combatant_states ||--o{ dnd5e_turn_budget_records : has
  dnd5e_encounter_sessions o|--o{ dnd5e_effect_instances : scopes

  users {
    string id PK
    string username UNIQUE
    string hashed_password nullable
    boolean is_active default_true
    boolean is_superuser default_false
    datetime created_at
    datetime updated_at
  }

  user_social_auths {
    string id PK
    string user_id FK
    string provider
    string provider_user_id
    string email nullable
    json extra_data default_object
    datetime created_at
    datetime updated_at
  }

  campaigns {
    string id PK
    string name
    string description nullable
    string dm_id nullable
    string current_scene nullable
    string active_encounter_id nullable
    int context_version default_0
    string active_turn nullable
    datetime created_at
    datetime updated_at
  }

  campaign_members {
    string id PK
    string campaign_id FK
    string user_id FK
    string role default_PLAYER
    string active_character_id nullable
    datetime created_at
    datetime updated_at
  }

  characters {
    string id PK
    string name
    string player_name nullable
    string campaign_id FK nullable
    string species_id FK nullable
    string class_id FK nullable
    string background_id FK nullable
    int level default_1
    int xp default_0
    json inventory default_array
    json effects default_array
    datetime created_at
    datetime updated_at
  }

  species {
    string id PK
    string name
    string description
    int speed default_30
    string size default_Medium
    json ability_bonuses default_object
    json traits default_array
    json languages default_array
    json effects default_array
    datetime created_at
    datetime updated_at
  }

  classes {
    string id PK
    string name
    string description
    string hit_die
    json proficiencies default_object
    json saving_throws default_array
    json progression default_array
    json effects default_array
    datetime created_at
    datetime updated_at
  }

  backgrounds {
    string id PK
    string name
    string description
    json skill_proficiencies default_array
    json tool_proficiencies default_array
    json equipment default_array
    json feature default_object
    json effects default_array
    datetime created_at
    datetime updated_at
  }

  dnd5e_scene_catalog {
    string id PK
    string campaign_id soft_ref
    string scene_id
    string name
    datetime created_at
    datetime updated_at
  }

  dnd5e_encounter_catalog {
    string id PK
    string campaign_id soft_ref
    string scene_id soft_ref
    string encounter_id
    string name
    string source default_fixture
    json state_json default_object
    datetime created_at
    datetime updated_at
  }

  dnd5e_encounter_sessions {
    string id PK
    string campaign_id unique_soft_ref
    string scene_id nullable_soft_ref
    string encounter_id
    string phase default_pre_combat
    int round_number default_0
    int active_index default_0
    json combat_state_json default_object
    datetime created_at
    datetime updated_at
  }

  dnd5e_combatant_states {
    string id PK
    string encounter_session_id FK
    string actor_id
    int initiative_order default_0
    string owner_user_id nullable_soft_ref
    int current_hp default_0
    int max_hp default_0
    int pos_x default_0
    int pos_y default_0
    json actor_snapshot default_object
    datetime created_at
    datetime updated_at
  }

  dnd5e_turn_budget_records {
    string id PK
    string encounter_session_id FK
    string combatant_id FK
    int round_number default_1
    boolean action_available default_true
    boolean bonus_action_available default_true
    boolean reaction_available default_true
    int max_movement default_30
    int movement_used default_0
    datetime created_at
    datetime updated_at
  }

  dnd5e_action_logs {
    string id PK
    string encounter_session_id FK
    string request_id nullable
    string actor_id
    string action_type
    string action_state
    string denial_reason nullable
    json authorization_checks default_object
    json payload default_object
    datetime created_at
    datetime updated_at
  }

  dnd5e_action_definitions {
    string id PK
    string system indexed_default_dnd5e
    string action_id
    string name
    string family default_utility
    string action_type_cost default_action
    string targeting_mode default_single_target
    int range nullable
    json save_context nullable
    json attack_context nullable
    json resource_costs default_array
    json effect_intents default_array
    json tags default_array
    string source_ref default_custom
    string content_version default_1
    boolean enabled default_true
    string pack_id nullable
    string pack_version nullable
    datetime created_at
    datetime updated_at
  }

  dnd5e_ability_bindings {
    string id PK
    string system indexed_default_dnd5e
    string binding_id
    string action_id soft_ref
    string actor_template_id nullable
    string actor_id nullable
    json unlock_conditions default_array
    json override_payload nullable
    string pack_id nullable
    string pack_version nullable
    datetime created_at
    datetime updated_at
  }

  dnd5e_effect_definitions {
    string id PK
    string system indexed_default_dnd5e
    string effect_id
    string name
    string family default_utility
    json duration default_object
    json stacking default_object
    json tags default_array
    json modifiers default_array
    json grants_conditions default_array
    json periodic default_array
    json removal_triggers default_array
    json metadata default_object
    string content_version default_1
    boolean enabled default_true
    string pack_id nullable
    string pack_version nullable
    datetime created_at
    datetime updated_at
  }

  dnd5e_effect_instances {
    string id PK
    string instance_id UNIQUE
    string effect_id indexed_soft_ref
    string source_actor_id nullable_soft_ref
    string target_actor_id soft_ref
    int applied_at_round
    int remaining_duration nullable
    string concentration_owner_actor_id nullable_soft_ref
    int stack_count default_1
    json snapshot_payload default_object
    json provenance default_object
    string encounter_session_id FK_nullable_set_null
    datetime created_at
    datetime updated_at
  }
```

## 3. Entity Catalog

Note on shared columns:

- Every table uses mixins for id, created_at, updated_at.
- id is a string UUID primary key generated in application code.
- created_at and updated_at use server defaults; updated_at changes on update.

### 3.1 Identity Domain

#### users

- PK:
  - id
- Columns:
  - username: string, unique, indexed, non-null
  - hashed_password: string, nullable
  - is_active: boolean, default true
  - is_superuser: boolean, default false
- Relationships:
  - 1 to many with user_social_auths via user_social_auths.user_id

#### user_social_auths

- PK:
  - id
- FK:
  - user_id -> users.id (non-null)
- Columns:
  - provider: string, non-null
  - provider_user_id: string, non-null
  - email: string, nullable
  - extra_data: JSON object, default {}
- Relationships:
  - many to 1 with users
- Constraint notes:
  - No DB-level unique constraint on provider + provider_user_id despite lookup behavior requiring uniqueness.

### 3.2 Campaign Domain

#### campaigns

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, nullable
  - dm_id: string, nullable (legacy/soft reference to users.id)
  - current_scene: string, nullable (soft reference to dnd5e_scene_catalog.scene_id within campaign)
  - active_encounter_id: string, nullable (soft reference to dnd5e_encounter_catalog.encounter_id within campaign)
  - context_version: int, default 0
  - active_turn: string, nullable
- Relationships:
  - 1 to many with campaign_members
  - 1 to many with characters

#### campaign_members

- PK:
  - id
- FK:
  - campaign_id -> campaigns.id (non-null)
  - user_id -> users.id (non-null)
- Columns:
  - role: string, default PLAYER
  - active_character_id: string, nullable (soft reference to characters.id)
- Relationships:
  - many to 1 campaigns
  - many to 1 users
- Constraint notes:
  - No DB-level unique constraint on campaign_id + user_id.

#### characters

- PK:
  - id
- FK:
  - campaign_id -> campaigns.id (nullable)
  - species_id -> species.id (nullable)
  - class_id -> classes.id (nullable)
  - background_id -> backgrounds.id (nullable)
- Columns (identity and progression):
  - name: string, indexed, non-null
  - player_name: string, nullable
  - level: int, default 1
  - xp: int, default 0
  - alignment: string, nullable
- Columns (abilities):
  - strength, dexterity, constitution, intelligence, wisdom, charisma: int, default 10
- Columns (vitals):
  - max_hp: int, non-null
  - current_hp: int, non-null
  - temp_hp: int, default 0
  - hit_dice: string, non-null
  - armor_class: int, default 10
  - speed: int, default 30
  - initiative: int, default 0
- Columns (state payloads):
  - inventory: JSON array, default []
  - spells: JSON array, default []
  - spell_slots: JSON object, default {}
  - actions: JSON array, default []
  - effects: JSON array, default []
- Relationships:
  - many to 1 campaigns/species/classes/backgrounds

#### factions

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, non-null
  - goals: string, nullable
  - beliefs: string, nullable
- Relationship notes:
  - No explicit FK relationships.

### 3.3 SRD/Definition Content Domain

#### items

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, non-null
  - type: string, non-null
  - rarity: string, non-null
  - weight: integer column, default 0
  - price: int, default 0
  - properties: JSON object, default {}
  - effects: JSON array, default []

#### spells

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, non-null
  - level: int, non-null
  - school: string, non-null
  - casting_time: string, non-null
  - range: string, non-null
  - components: JSON object, non-null
  - duration: string, non-null
  - effects: JSON array, default []

#### monsters

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, nullable
  - size, type, alignment: string, non-null
  - armor_class, hit_points: int, non-null
  - hit_dice: string, non-null
  - speed: JSON object, non-null
  - strength, dexterity, constitution, intelligence, wisdom, charisma: int, non-null
  - proficiencies: JSON array, default []
  - senses: JSON object, default {}
  - languages: string, non-null
  - challenge_rating: integer column, non-null
  - xp: int, non-null
  - special_abilities, actions, legendary_actions, inventory, effects: JSON array, default []

#### species

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, non-null
  - speed: int, default 30
  - size: string, default Medium
  - ability_bonuses: JSON object, default {}
  - traits: JSON array, default []
  - languages: JSON array, default []
  - effects: JSON array, default []

#### classes

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, non-null
  - hit_die: string, non-null
  - proficiencies: JSON object, default {}
  - saving_throws: JSON array, default []
  - progression: JSON array, default []
  - effects: JSON array, default []

#### backgrounds

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, non-null
  - skill_proficiencies, tool_proficiencies, equipment, effects: JSON array, default []
  - feature: JSON object, default {}

#### feats

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, non-null
  - prerequisites: string, nullable
  - effects: JSON array, default []

#### features

- PK:
  - id
- Columns:
  - name: string, indexed, non-null
  - description: string, non-null
  - source: string, non-null
  - level_required: int, default 1
  - effects: JSON array, default []

### 3.4 DnD5e Context Catalog Domain

#### dnd5e_scene_catalog

- PK:
  - id
- Columns:
  - campaign_id: string, indexed, non-null (soft relation to campaigns.id)
  - scene_id: string, non-null
  - name: string, non-null
- Constraints:
  - unique(campaign_id, scene_id)

#### dnd5e_encounter_catalog

- PK:
  - id
- Columns:
  - campaign_id: string, indexed, non-null (soft relation to campaigns.id)
  - scene_id: string, indexed, non-null (soft relation to dnd5e_scene_catalog.scene_id within campaign)
  - encounter_id: string, non-null
  - name: string, non-null
  - source: string, default fixture
  - state_json: JSON object, default {}
- Constraints:
  - unique(campaign_id, scene_id, encounter_id)
- Indexes:
  - (campaign_id, scene_id)

### 3.5 DnD5e Encounter Session and Action Execution Domain

#### dnd5e_encounter_sessions

- PK:
  - id
- Columns:
  - campaign_id: string, indexed, unique, non-null (soft relation to campaigns.id)
  - scene_id: string, nullable (soft relation to scene catalog)
  - encounter_id: string, non-null (soft relation to encounter catalog)
  - phase: string, default pre_combat
  - round_number: int, default 0
  - active_index: int, default 0
  - combat_state_json: JSON object, default {}
- Relationships:
  - 1 to many with dnd5e_combatant_states
  - 1 to many with dnd5e_turn_budget_records
  - 1 to many with dnd5e_action_logs
  - optional 1 to many with dnd5e_effect_instances

#### dnd5e_combatant_states

- PK:
  - id
- FK:
  - encounter_session_id -> dnd5e_encounter_sessions.id (on delete cascade, non-null)
- Columns:
  - actor_id: string, indexed, non-null
  - initiative_order: int, default 0
  - owner_user_id: string, nullable (soft relation to users.id)
  - current_hp: int, default 0
  - max_hp: int, default 0
  - pos_x: int, default 0
  - pos_y: int, default 0
  - actor_snapshot: JSON object, default {}
- Relationships:
  - many to 1 encounter session
  - 1 to many turn budget records

#### dnd5e_turn_budget_records

- PK:
  - id
- FK:
  - encounter_session_id -> dnd5e_encounter_sessions.id (on delete cascade, non-null)
  - combatant_id -> dnd5e_combatant_states.id (on delete cascade, non-null)
- Columns:
  - round_number: int, default 1
  - action_available: boolean, default true
  - bonus_action_available: boolean, default true
  - reaction_available: boolean, default true
  - max_movement: int, default 30
  - movement_used: int, default 0
- Constraints:
  - unique(encounter_session_id, combatant_id, round_number)
- Indexes:
  - (encounter_session_id, round_number)
  - (encounter_session_id, combatant_id)

#### dnd5e_action_logs

- PK:
  - id
- FK:
  - encounter_session_id -> dnd5e_encounter_sessions.id (on delete cascade, non-null)
- Columns:
  - request_id: string, nullable
  - actor_id: string, indexed, non-null
  - action_type: string, non-null
  - action_state: string, non-null
  - denial_reason: string, nullable
  - authorization_checks: JSON object, default {}
  - payload: JSON object, default {}
- Relationships:
  - many to 1 encounter session

#### dnd5e_action_definitions

- PK:
  - id
- Columns:
  - system: string, indexed, default dnd5e
  - action_id: string, non-null
  - name: string, non-null
  - family: string, default utility
  - action_type_cost: string, default action
  - targeting_mode: string, default single_target
  - range: int, nullable
  - save_context: JSON object, nullable
  - attack_context: JSON object, nullable
  - resource_costs: JSON array, default []
  - effect_intents: JSON array, default []
  - tags: JSON array, default []
  - source_ref: string, default custom
  - content_version: string, default 1
  - enabled: boolean, default true
  - pack_id: string, nullable, indexed
  - pack_version: string, nullable
- Constraints:
  - unique(system, action_id)
- Indexes:
  - (system, pack_id)

#### dnd5e_ability_bindings

- PK:
  - id
- Columns:
  - system: string, indexed, default dnd5e
  - binding_id: string, non-null
  - action_id: string, indexed, non-null (soft relation to dnd5e_action_definitions.action_id by system)
  - actor_template_id: string, nullable
  - actor_id: string, nullable
  - unlock_conditions: JSON array, default []
  - override_payload: JSON object, nullable
  - pack_id: string, nullable, indexed
  - pack_version: string, nullable
- Constraints:
  - unique(system, binding_id)
- Indexes:
  - (system, pack_id)

#### dnd5e_effect_definitions

- PK:
  - id
- Columns:
  - system: string, indexed, default dnd5e
  - effect_id: string, non-null
  - name: string, non-null
  - family: string, default utility
  - duration: JSON object, default {}
  - stacking: JSON object, default {}
  - tags: JSON array, default []
  - modifiers: JSON array, default []
  - grants_conditions: JSON array, default []
  - periodic: JSON array, default []
  - removal_triggers: JSON array, default []
  - metadata: JSON object, default {}
  - content_version: string, default 1
  - enabled: boolean, default true
  - pack_id: string, nullable, indexed
  - pack_version: string, nullable
- Constraints:
  - unique(system, effect_id)
- Indexes:
  - (system, pack_id)

#### dnd5e_effect_instances

- PK:
  - id
- FK:
  - encounter_session_id -> dnd5e_encounter_sessions.id (nullable, on delete set null)
- Columns:
  - instance_id: string, unique, indexed, non-null
  - effect_id: string, indexed, non-null (soft relation to dnd5e_effect_definitions.effect_id)
  - source_actor_id: string, nullable
  - target_actor_id: string, indexed, non-null
  - applied_at_round: int, non-null
  - remaining_duration: int, nullable
  - concentration_owner_actor_id: string, nullable
  - stack_count: int, default 1
  - snapshot_payload: JSON object, default {}
  - provenance: JSON object, default {}
- Relationship notes:
  - Effect instance rows can outlive encounter session deletion because FK uses set null.

## 4. Relationship and Cardinality Summary

Hard FK-enforced:

- users 1 -> many user_social_auths
- campaigns 1 -> many campaign_members
- users 1 -> many campaign_members
- campaigns 1 -> many characters
- species/classes/backgrounds 1 -> many characters
- dnd5e_encounter_sessions 1 -> many dnd5e_combatant_states
- dnd5e_encounter_sessions 1 -> many dnd5e_turn_budget_records
- dnd5e_combatant_states 1 -> many dnd5e_turn_budget_records
- dnd5e_encounter_sessions 1 -> many dnd5e_action_logs
- dnd5e_encounter_sessions 0..1 -> many dnd5e_effect_instances

Soft (application-enforced) relationships:

- campaigns.current_scene -> dnd5e_scene_catalog.scene_id (scoped by campaign)
- campaigns.active_encounter_id -> dnd5e_encounter_catalog.encounter_id (scoped by campaign + scene)
- dnd5e_scene_catalog.campaign_id -> campaigns.id
- dnd5e_encounter_catalog.(campaign_id, scene_id) -> scene catalog/campaign context
- dnd5e_encounter_sessions.campaign_id -> campaigns.id
- dnd5e_ability_bindings.action_id -> dnd5e_action_definitions.action_id (plus system)
- dnd5e_effect_instances.effect_id -> dnd5e_effect_definitions.effect_id (plus implied system)
- dnd5e_combatant_states.owner_user_id -> users.id

## 5. Persistence Ownership Boundaries

### 5.1 Identity

- Writer surfaces:
  - auth register/login/social callback flows.
- Primary files:
  - backend/src/identity/lib/users.py
  - backend/src/identity/router.py
- Owned aggregates:
  - users
  - user_social_auths

### 5.2 Campaign and Character

- Writer surfaces:
  - campaigns and characters routers.
- Primary files:
  - backend/src/campaigns/routers/campaigns.py
  - backend/src/campaigns/routers/characters.py
- Owned aggregates:
  - campaigns
  - campaign_members
  - characters

### 5.3 Context Selection and Catalog

- Writer surfaces:
  - context selection through encounter session repository.
  - automatic context catalog initialization in combat service.
- Primary files:
  - backend/src/systems/dnd5e/repositories/encounter_session_repository.py
  - backend/src/systems/dnd5e/services/combat_service.py
- Owned aggregates:
  - campaigns.current_scene
  - campaigns.active_encounter_id
  - campaigns.context_version
  - dnd5e_scene_catalog
  - dnd5e_encounter_catalog

### 5.4 Encounter Session Runtime Persistence

- Writer surfaces:
  - action execution repository via combat service orchestration.
- Primary files:
  - backend/src/systems/dnd5e/repositories/action_execution_repository.py
  - backend/src/systems/dnd5e/services/combat_service.py
- Owned aggregates:
  - dnd5e_encounter_sessions
  - dnd5e_combatant_states
  - dnd5e_turn_budget_records
  - dnd5e_action_logs
  - dnd5e_effect_instances

### 5.5 Content Packs and Definition Seeding

- Writer surfaces:
  - DataLoader fixture imports.
  - ContentPackImporter upsert/merge workflows.
  - Definitions router create endpoints.
- Primary files:
  - backend/src/data/lib/loader.py
  - backend/src/systems/dnd5e/services/content_pack_importer.py
  - backend/src/data/routers/definitions.py
- Owned aggregates:
  - items, spells, monsters, species, classes, backgrounds, feats, features
  - dnd5e_action_definitions
  - dnd5e_ability_bindings
  - dnd5e_effect_definitions

## 6. Known Drift and Risks

1. Soft-relations without FK constraints in DnD5e catalog/session tables.

- campaign_id, scene_id, encounter_id fields are string-based and mostly application validated.
- Risk: orphaned or mismatched rows possible if writes bypass service layer.

2. Backfill/migration gap.

- Startup backfill only adds campaigns.active_encounter_id, campaigns.context_version, and encounter_sessions.scene_id.
- Risk: no general migration framework yet; future schema changes can drift across environments.

3. usersocial uniqueness is implicit, not explicit.

- Auth callback logic expects one provider/provider_user_id mapping.
- Missing unique constraint allows duplicates under race/manual inserts.

4. Campaign membership uniqueness is implicit, not explicit.

- Join logic assumes one row per user per campaign.
- Missing unique constraint on (campaign_id, user_id) permits duplicates.

5. Numeric typing mismatches in SRD models.

- items.weight and monsters.challenge_rating are mapped as Integer while comments/usage suggest fractional values.
- Risk: precision loss or inconsistent semantics.

6. Faction model registration gap.

- factions model exists but is not imported by startup/router path used by metadata.create_all.
- Risk: table may not be created in environments relying solely on current import graph.

7. JSON default mutability pattern.

- Some columns use default {} directly (for example user_social_auths.extra_data).
- SQLAlchemy handles Python defaults at object construction, but mutable-literal style is higher-risk than callable defaults.

## 7. Verification Checklist

Schema and behavior verification commands:

1. Campaign domain tests:

- docker compose --profile test run --rm backend-test pytest tests/campaigns -q

2. DnD5e domain tests:

- docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -q

3. Backend runtime logs:

- docker compose logs backend --tail=200

4. Optional schema introspection (recommended):

- Verify unique constraints exist as expected (especially dnd5e catalog and budget tables).
- Verify FK ondelete behavior for:
  - dnd5e_combatant_states.encounter_session_id (cascade)
  - dnd5e_turn_budget_records.\* (cascade)
  - dnd5e_action_logs.encounter_session_id (cascade)
  - dnd5e_effect_instances.encounter_session_id (set null)

5. Optional drift checks (recommended):

- Confirm whether factions table is present in fresh DB bootstrap.
- Validate that duplicate campaign_members and duplicate user_social_auths cannot be produced under concurrent calls.

## 8. Source Index

Primary model and wiring sources used:

- backend/src/database.py
- backend/src/main.py
- backend/src/campaigns/lib/campaign.py
- backend/src/campaigns/lib/character.py
- backend/src/campaigns/lib/faction.py
- backend/src/identity/models.py
- backend/src/data/lib/item.py
- backend/src/data/lib/spell.py
- backend/src/data/lib/monster.py
- backend/src/data/lib/species.py
- backend/src/data/lib/class_model.py
- backend/src/data/lib/background.py
- backend/src/data/lib/feat.py
- backend/src/data/lib/feature.py
- backend/src/systems/dnd5e/lib/context_models.py
- backend/src/systems/dnd5e/lib/combat_models.py
- backend/src/systems/dnd5e/lib/content_models.py
- backend/src/systems/dnd5e/repositories/context_repository.py
- backend/src/systems/dnd5e/repositories/encounter_session_repository.py
- backend/src/systems/dnd5e/repositories/action_execution_repository.py
- backend/src/systems/dnd5e/repositories/action_catalog_repository.py
- backend/src/systems/dnd5e/services/combat_service.py
- backend/src/systems/dnd5e/services/content_pack_importer.py
- backend/src/data/lib/loader.py
