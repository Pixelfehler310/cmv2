# V02 Deterministic Combat/Action/Effect Concept: Complex Example

Status: Draft for planning and test design
Related diagrams:

- V02_deterministic_combat_action_effects_complex_example_detailed_plan.mmd
- V02_combat_actions_detailed_plan.mmd
- V02_action_processing_and_event_contracts_detailed_plan.mmd

## Why this artifact exists

This document defines one intentionally complicated but fully deterministic reference scenario for the combat/action/effect system.

It serves three purposes:

1. Demonstrate that the operation-graph model handles high-complexity official DnD actions and spells.
2. Convert complex gameplay behavior into deterministic, testable contracts.
3. Provide the canonical acceptance matrix for V02 closure and future regressions.

## Determinism constraints (non-negotiable)

1. Same input command set and same initial state must always produce identical outputs.
2. Output identity includes: result status, reason codes, operation order, target snapshots, roll results, state deltas, and event sequence.
3. No handler is allowed to mutate state outside the authoritative orchestration pipeline.
4. Every mutation must be attributable to one request_id and operation_id.
5. Every command must end in exactly one terminal action status path (resolved, denied, or error).
6. Every successful command must increment state_revision exactly once.
7. Any client revision gap must trigger deterministic resync.

## Official DnD scenario coverage for your requested list

The scenario uses only official DnD class actions/features/spells.

| Requirement                                        | Example used                                                          | Why this satisfies the requirement                                                                                                                         |
| -------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Multiple actions per turn                       | Fighter (Level 11) with Extra Attack + Action Surge + Crossbow Expert | Attack action can contain multiple weapon attacks; Action Surge grants an additional action in same turn; Crossbow Expert allows repeated crossbow attacks |
| 2a. Vines crowd control with damage in caster turn | Wall of Thorns                                                        | Creates thorn barrier and resolves immediate damage in caster execution pipeline                                                                           |
| 2b. Fire circle damage in target turn              | Wall of Fire (ring mode)                                              | Ring persists and applies target-turn/end-turn damage rules                                                                                                |
| 3. Cone from player origin                         | Burning Hands                                                         | Cone template is anchored at caster origin                                                                                                                 |
| 4. Circle AoE with range + size                    | Fireball                                                              | Point within range plus explicit radius shape                                                                                                              |
| 5. Single target attack                            | Heavy Crossbow attack                                                 | Single explicit target attack path                                                                                                                         |
| 6. Summon entity                                   | Animate Dead                                                          | Creates a new runtime entity with deterministic initiative placement                                                                                       |
| 7. Turn into different entity                      | Druid Wild Shape                                                      | Replaces runtime stat block with deterministic reversion contract                                                                                          |
| 8. Multi-effect single spell                       | Dawn                                                                  | Beam-column style impact plus persistent circular area and repeated turn-based damage ticks                                                                |

## Scenario cast and initial state snapshot

Actors:

1. FighterSeren (PC, L11 Fighter).
2. WizardIria (PC, L13 Wizard).
3. DruidThorn (PC, L10 Druid).
4. NecromancerVoss (NPC caster).
5. SummonedZombieZ1 (spawned later by Animate Dead).

Initial deterministic state assumptions:

1. All actor ids are stable UUID-like strings.
2. Initiative order is precomputed and persisted at revision R0.
3. Grid coordinates and terrain occupancy are persisted at revision R0.
4. No hidden RNG side channels exist; roll stream is derived from deterministic seed formula.
5. No pending unresolved commands exist at scenario start.

## Canonical command model for this scenario

Every action is encoded as a deterministic command envelope:

1. request_id, actor_id, action_ref, action_type_cost.
2. operation_specs (non-empty ordered list after graph linearization).
3. seed_snapshot and state_revision_in.
4. optional command_context.

Every operation node includes:

1. operation_id.
2. operation_kind.
3. targeting_mode.
4. execution_phase.
5. depends_on_operation_ids.
6. payload.

## Concrete representation in action objects and JSON

This section is the canonical answer to "how is this represented in objects/jsons".

The model is intentionally split into three layers:

1. Content layer JSON: authored spell/action definitions in compendium-style data.
2. Command layer JSON: runtime execute-action payload from client to backend.
3. Runtime layer records: persisted resolved operation/effect/zone/summon/transform state.

### Layer A: content layer JSON (authoring data)

Content definitions should be reusable templates with no per-request runtime ids.

```json
{
  "action_ref": "spell.dawn",
  "display_name": "Dawn",
  "source": "PHB",
  "cost": {
    "action_type": "action",
    "resource_costs": [{ "resource": "spell_slot", "level": 5, "amount": 1 }]
  },
  "concentration": true,
  "duration": { "unit": "minute", "value": 1 },
  "operation_templates": [
    {
      "operation_key": "cast_impact",
      "operation_kind": "damage",
      "execution_phase": "immediate",
      "targeting": {
        "mode": "area",
        "area": {
          "shape": "cylinder",
          "radius_ft": 30,
          "height_ft": 40,
          "origin": "point_within_range",
          "range_ft": 60
        }
      },
      "payload": {
        "save": { "ability": "con", "dc_from": "spellcasting_dc" },
        "damage": { "dice": "4d10", "type": "radiant", "on_save": "half" }
      }
    },
    {
      "operation_key": "persistent_zone",
      "operation_kind": "zone",
      "execution_phase": "deferred",
      "depends_on": ["cast_impact"],
      "targeting": {
        "mode": "derived",
        "derived_from": "cast_impact.area"
      },
      "payload": {
        "zone_type": "dawn_cylinder",
        "tick_trigger": "end_turn",
        "on_tick": {
          "save": { "ability": "con", "dc_from": "spellcasting_dc" },
          "damage": { "dice": "4d10", "type": "radiant", "on_save": "half" }
        }
      }
    }
  ]
}
```

### Layer B: command layer JSON (runtime execution request)

Command payloads must contain concrete runtime operation_specs.

```json
{
  "request_id": "req-r3-w-0021",
  "campaign_id": "cmp-001",
  "scene_id": "scn-forest-ambush",
  "actor_id": "actor-wizard-iria",
  "action_ref": "spell.dawn",
  "action_type_cost": "action",
  "state_revision_in": 182,
  "operation_specs": [
    {
      "operation_id": "op-r3-w-dawn-1-cast-impact",
      "operation_kind": "damage",
      "execution_phase": "immediate",
      "targeting_mode": "area",
      "target_payload": {
        "shape": "cylinder",
        "center": { "x": 12, "y": 8, "z": 0 },
        "radius_ft": 30,
        "height_ft": 40,
        "range_from_actor_ft": 60
      },
      "depends_on_operation_ids": [],
      "operation_payload": {
        "save": { "ability": "con", "dc": 17 },
        "damage": { "dice": "4d10", "type": "radiant", "on_save": "half" }
      }
    },
    {
      "operation_id": "op-r3-w-dawn-2-zone-create",
      "operation_kind": "zone",
      "execution_phase": "deferred",
      "targeting_mode": "derived",
      "target_payload": {
        "derived_from_operation_id": "op-r3-w-dawn-1-cast-impact",
        "derived_field": "target_payload"
      },
      "depends_on_operation_ids": ["op-r3-w-dawn-1-cast-impact"],
      "operation_payload": {
        "zone_type": "dawn_cylinder",
        "tick_trigger": "end_turn",
        "duration_rounds": 10
      }
    },
    {
      "operation_id": "op-r3-w-dawn-3-zone-tick-register",
      "operation_kind": "damage",
      "execution_phase": "tick",
      "targeting_mode": "derived",
      "target_payload": {
        "derived_from_operation_id": "op-r3-w-dawn-2-zone-create",
        "derived_field": "zone_occupants"
      },
      "depends_on_operation_ids": ["op-r3-w-dawn-2-zone-create"],
      "operation_payload": {
        "save": { "ability": "con", "dc": 17 },
        "damage": { "dice": "4d10", "type": "radiant", "on_save": "half" }
      }
    }
  ],
  "command_context": {
    "client_ts": "2026-03-27T14:31:00Z"
  }
}
```

### Layer C: runtime records (persisted authoritative state)

Three record families are required:

1. action_execution_record: command-level status and revision metadata.
2. operation_execution_record: per-operation result and target snapshot references.
3. effect_runtime_record and zone_runtime_record: lifecycle state for deferred/tick behavior.

```json
{
  "action_execution_record": {
    "request_id": "req-r3-w-0021",
    "actor_id": "actor-wizard-iria",
    "action_ref": "spell.dawn",
    "status": "resolved",
    "resolved_operation_ids": ["op-r3-w-dawn-1-cast-impact", "op-r3-w-dawn-2-zone-create", "op-r3-w-dawn-3-zone-tick-register"],
    "state_revision_in": 182,
    "state_revision_out": 183,
    "state_checksum_out": "sha256:c0f6..."
  }
}
```

### Canonical JSON shape per targeting mode

The target_payload shape is mode-specific and must be validated strictly.

```json
{
  "explicit": {
    "target_actor_ids": ["actor-goblin-1"]
  },
  "area_cone_from_self": {
    "shape": "cone",
    "origin": "self",
    "length_ft": 15,
    "direction": { "dx": 1, "dy": 0 }
  },
  "area_circle_point_in_range": {
    "shape": "sphere",
    "center": { "x": 18, "y": 5, "z": 0 },
    "radius_ft": 20,
    "range_from_actor_ft": 150
  },
  "self": {
    "self_actor_id": "actor-druid-thorn"
  },
  "derived": {
    "derived_from_operation_id": "op-r3-w-dawn-2-zone-create",
    "derived_field": "zone_occupants"
  },
  "none": {}
}
```

### Worked JSON examples for the requested core scenarios

#### Example 1: Fighter multi-action turn as 3 player WebSocket packets

Packet 1: first Attack action (Extra Attack = 2 attacks)

```json
{
  "request_id": "req-r1-f-0001",
  "actor_id": "actor-fighter-seren",
  "action_ref": "action.weapon_attack.heavy_crossbow",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-r1-f-p1-attack-1",
      "operation_kind": "attack",
      "execution_phase": "immediate",
      "targeting_mode": "explicit",
      "target_payload": { "target_actor_ids": ["actor-ogre-1"] },
      "depends_on_operation_ids": [],
      "operation_payload": { "weapon_ref": "weapon.heavy_crossbow" }
    },
    {
      "operation_id": "op-r1-f-p1-attack-2",
      "operation_kind": "attack",
      "execution_phase": "immediate",
      "targeting_mode": "explicit",
      "target_payload": { "target_actor_ids": ["actor-ogre-1"] },
      "depends_on_operation_ids": ["op-r1-f-p1-attack-1"],
      "operation_payload": { "weapon_ref": "weapon.heavy_crossbow" }
    }
  ]
}
```

Packet 2: Action Surge activation (refreshes additional action budget)

```json
{
  "request_id": "req-r1-f-0002",
  "actor_id": "actor-fighter-seren",
  "action_ref": "feature.fighter.action_surge",
  "action_type_cost": "free",
  "operation_specs": [
    {
      "operation_id": "op-r1-f-p2-action-surge",
      "operation_kind": "resource",
      "execution_phase": "immediate",
      "targeting_mode": "none",
      "target_payload": {},
      "depends_on_operation_ids": [],
      "operation_payload": {
        "consume": "action_surge_charge",
        "grant": "one_additional_action_this_turn"
      }
    }
  ]
}
```

Packet 3: second Attack action (Extra Attack = 2 attacks)

```json
{
  "request_id": "req-r1-f-0003",
  "actor_id": "actor-fighter-seren",
  "action_ref": "action.weapon_attack.heavy_crossbow",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-r1-f-p3-attack-1",
      "operation_kind": "attack",
      "execution_phase": "immediate",
      "targeting_mode": "explicit",
      "target_payload": { "target_actor_ids": ["actor-ogre-1"] },
      "depends_on_operation_ids": [],
      "operation_payload": { "weapon_ref": "weapon.heavy_crossbow" }
    },
    {
      "operation_id": "op-r1-f-p3-attack-2",
      "operation_kind": "attack",
      "execution_phase": "immediate",
      "targeting_mode": "explicit",
      "target_payload": { "target_actor_ids": ["actor-ogre-1"] },
      "depends_on_operation_ids": ["op-r1-f-p3-attack-1"],
      "operation_payload": { "weapon_ref": "weapon.heavy_crossbow" }
    }
  ]
}
```

#### Example 2: Wall of Thorns (caster-turn crowd control damage)

```json
{
  "request_id": "req-r2-d-0101",
  "actor_id": "actor-druid-thorn",
  "action_ref": "spell.wall_of_thorns",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-wot-1",
      "operation_kind": "zone",
      "execution_phase": "deferred",
      "targeting_mode": "area",
      "target_payload": {
        "shape": "line",
        "segments": [
          { "x": 4, "y": 7 },
          { "x": 14, "y": 7 }
        ]
      },
      "depends_on_operation_ids": [],
      "operation_payload": { "zone_type": "wall_of_thorns", "tick_trigger": "on_enter" }
    },
    {
      "operation_id": "op-wot-2",
      "operation_kind": "damage",
      "execution_phase": "immediate",
      "targeting_mode": "derived",
      "target_payload": { "derived_from_operation_id": "op-wot-1", "derived_field": "initial_occupants" },
      "depends_on_operation_ids": ["op-wot-1"],
      "operation_payload": { "save": { "ability": "dex", "dc": 17 }, "damage": { "dice": "7d8", "type": "piercing", "on_save": "half" } }
    }
  ]
}
```

#### Example 3: Wall of Fire ring (target-turn damage)

```json
{
  "request_id": "req-r2-w-0112",
  "actor_id": "actor-wizard-iria",
  "action_ref": "spell.wall_of_fire",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-wof-1",
      "operation_kind": "zone",
      "execution_phase": "deferred",
      "targeting_mode": "area",
      "target_payload": { "shape": "ring", "center": { "x": 10, "y": 10 }, "radius_ft": 20 },
      "depends_on_operation_ids": [],
      "operation_payload": { "zone_type": "wall_of_fire_ring", "tick_trigger": "end_turn", "damage": { "dice": "5d8", "type": "fire" } }
    }
  ]
}
```

#### Example 4: Burning Hands cone from caster origin

```json
{
  "request_id": "req-r1-w-0008",
  "actor_id": "actor-wizard-iria",
  "action_ref": "spell.burning_hands",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-bh-1",
      "operation_kind": "damage",
      "execution_phase": "immediate",
      "targeting_mode": "area",
      "target_payload": { "shape": "cone", "origin": "self", "length_ft": 15, "direction": { "dx": 1, "dy": 0 } },
      "depends_on_operation_ids": [],
      "operation_payload": { "save": { "ability": "dex", "dc": 17 }, "damage": { "dice": "3d6", "type": "fire", "on_save": "half" } }
    }
  ]
}
```

#### Example 5: Fireball circle AoE (range + size)

```json
{
  "request_id": "req-r2-f-0201",
  "actor_id": "actor-fighter-seren",
  "action_ref": "spell.fireball_via_scroll",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-fb-1",
      "operation_kind": "damage",
      "execution_phase": "immediate",
      "targeting_mode": "area",
      "target_payload": { "shape": "sphere", "center": { "x": 18, "y": 5, "z": 0 }, "radius_ft": 20, "range_from_actor_ft": 150 },
      "depends_on_operation_ids": [],
      "operation_payload": { "save": { "ability": "dex", "dc": 15 }, "damage": { "dice": "8d6", "type": "fire", "on_save": "half" } }
    }
  ]
}
```

#### Example 6: Animate Dead summon

```json
{
  "request_id": "req-r1-n-0017",
  "actor_id": "actor-necromancer-voss",
  "action_ref": "spell.animate_dead",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-ad-1",
      "operation_kind": "summon",
      "execution_phase": "deferred",
      "targeting_mode": "explicit",
      "target_payload": { "target_corpse_ids": ["corpse-3"] },
      "depends_on_operation_ids": [],
      "operation_payload": { "summon_template_ref": "undead.zombie", "initiative_policy": "insert_after_summoner" }
    }
  ]
}
```

#### Example 7: Wild Shape transform

```json
{
  "request_id": "req-r3-d-0022",
  "actor_id": "actor-druid-thorn",
  "action_ref": "feature.wild_shape",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-ws-1",
      "operation_kind": "transform",
      "execution_phase": "deferred",
      "targeting_mode": "self",
      "target_payload": { "self_actor_id": "actor-druid-thorn" },
      "depends_on_operation_ids": [],
      "operation_payload": { "target_form_ref": "beast.dire_wolf", "persist_reversion_snapshot": true }
    }
  ]
}
```

#### Example 8: Single target crossbow attack

```json
{
  "request_id": "req-r3-f-0100",
  "actor_id": "actor-fighter-seren",
  "action_ref": "action.weapon_attack.heavy_crossbow",
  "action_type_cost": "action",
  "operation_specs": [
    {
      "operation_id": "op-cb-1",
      "operation_kind": "attack",
      "execution_phase": "immediate",
      "targeting_mode": "explicit",
      "target_payload": { "target_actor_ids": ["actor-ghoul-2"] },
      "depends_on_operation_ids": [],
      "operation_payload": { "weapon_ref": "weapon.heavy_crossbow", "attack_mod": 9, "damage": "1d10+5" }
    }
  ]
}
```

## One complicated deterministic walkthrough

### Round 1

#### R1.1 FighterSeren: multi-action turn (Requirement 1 + 5)

Action package:

1. Attack action using Heavy Crossbow with Extra Attack sequence.
2. Action Surge for second action.
3. Second action also Attack (crossbow sequence).
4. Crossbow Expert is assumed to satisfy loading-rule legality for repeated crossbow shots.

Deterministic operation model:

1. req-r1-f-0001: op-r1-f-p1-attack-1, op-r1-f-p1-attack-2
2. req-r1-f-0002: op-r1-f-p2-action-surge
3. req-r1-f-0003: op-r1-f-p3-attack-1, op-r1-f-p3-attack-2

Deterministic checks:

1. Packet order from player is authoritative for command sequencing: 0001 -> 0002 -> 0003.
2. Each packet has deterministic internal operation order by operation_id/dependency.
3. Budget transitions are exact: packet1 consumes action, packet2 consumes action surge feature and grants one action, packet3 consumes granted action.
4. Miss/hit/crit outcomes must replay exactly from seed stream.

#### R1.2 WizardIria: Burning Hands (Requirement 3)

Operation model:

1. op_r1_w_bh_1_validate_origin
2. op_r1_w_bh_2_resolve_cone_targets
3. op_r1_w_bh_3_roll_saves_and_damage
4. op_r1_w_bh_4_apply_damage

Deterministic checks:

1. Cone geometry resolution uses deterministic template projection.
2. Target list ordering is stable by actor_id.
3. Save and damage rolls are deterministic and replayable.

#### R1.3 NecromancerVoss: Animate Dead (Requirement 6)

Operation model:

1. op_r1_n_ad_1_validate_corpse_or_bones_target
2. op_r1_n_ad_2_spawn_entity_runtime
3. op_r1_n_ad_3_insert_initiative_slot
4. op_r1_n_ad_4_emit_summon_event

Deterministic checks:

1. Summoned entity id format and assignment path are deterministic.
2. Initiative insertion rule is fixed and replay-safe.
3. Summon event payload includes stable initiative_slot.

### Round 2

#### R2.1 DruidThorn: Wall of Thorns (Requirement 2a)

Operation model:

1. op_r2_d_wot_1_resolve_wall_geometry
2. op_r2_d_wot_2_create_zone_wall_of_thorns
3. op_r2_d_wot_3_resolve_immediate_saves
4. op_r2_d_wot_4_apply_immediate_damage
5. op_r2_d_wot_5_register_movement_hazard_rules

Deterministic checks:

1. Wall geometry hash must be identical under replay.
2. Immediate damage occurs in caster request pipeline only once.
3. Zone id and zone lifecycle events are deterministic.

#### R2.2 WizardIria: Wall of Fire ring (Requirement 2b)

Operation model:

1. op_r2_w_wof_1_resolve_ring_center_and_radius
2. op_r2_w_wof_2_create_ring_zone
3. op_r2_w_wof_3_mark_hot_side
4. op_r2_w_wof_4_register_target_turn_end_tick

Deterministic checks:

1. Ring zone topology must be deterministic.
2. Tick resolution order follows initiative then actor_id tie break.
3. End-turn damage event sequence must be stable.

#### R2.3 FighterSeren: Fireball (Requirement 4)

Operation model:

1. op_r2_f_fb_1_validate_point_within_range
2. op_r2_f_fb_2_resolve_sphere_targets
3. op_r2_f_fb_3_roll_dex_saves_and_damage
4. op_r2_f_fb_4_apply_aoe_damage

Deterministic checks:

1. Point-in-range check returns same result for same coordinates.
2. Sphere target resolution uses deterministic occupancy snapshot.
3. Damage and save outcomes are deterministic.

### Round 3

#### R3.1 DruidThorn: Wild Shape (Requirement 7)

Operation model:

1. op_r3_d_ws_1_validate_form_access
2. op_r3_d_ws_2_snapshot_pre_transform_state
3. op_r3_d_ws_3_apply_form_stat_block
4. op_r3_d_ws_4_emit_transform_started

Deterministic checks:

1. Form resolution uses canonical stat-block reference.
2. HP/state carry-over and reversion snapshot are deterministic.
3. Transform event carries stable source and target form refs.

#### R3.2 WizardIria: Dawn (Requirement 8)

Operation model:

1. op_r3_w_dawn_1_validate_target_point
2. op_r3_w_dawn_2_create_beam_column_footprint
3. op_r3_w_dawn_3_apply_cast_phase_damage
4. op_r3_w_dawn_4_create_persistent_cylinder_zone
5. op_r3_w_dawn_5_register_end_turn_ticks

Deterministic checks:

1. Beam/cylinder geometry hash is stable.
2. Cast-time damage applies exactly once per valid target in snapshot.
3. Persistent zone ticks on configured trigger with deterministic order.
4. Removal/expiry events are deterministic and idempotent.

#### R3.3 FighterSeren: single crossbow shot (Requirement 5 re-validated)

Operation model:

1. op_r3_f_cb_1_validate_target
2. op_r3_f_cb_2_attack_roll
3. op_r3_f_cb_3_damage_roll_apply

Deterministic checks:

1. Single-target path remains stable even under many active zones/effects.
2. No unrelated zone/effect ordering drift occurs.

## Adaptation guide: how to encode this into the V02 architecture

### Step 1: Translate rules text into operation graph primitives

For each action/spell/feature, identify:

1. Immediate operations.
2. Deferred operations.
3. Tick-triggered operations.
4. Side-effect operations (summon, transform, concentration change).

### Step 2: Lock deterministic identifiers and graph shape

1. Generate operation_id deterministically from request_id + semantic suffix.
2. Reject dependency cycles.
3. Linearize graph deterministically before execution.

### Step 3: Resolve targets with immutable snapshots

1. Resolve per-operation targets.
2. Persist snapshot by request_id + operation_id.
3. Use snapshot references for all downstream resolution.

### Step 4: Execute with stable ordering and stable RNG

1. Execute operations in linearized graph order.
2. Resolve tie breaks with stable actor_id ordering.
3. Use deterministic seed policy for all roll operations.

### Step 5: Emit canonical events and revision metadata

1. action lifecycle events.
2. operation lifecycle events.
3. effect/zone/summon/transform lifecycle events.
4. terminal result event with state_revision and checksum.

### Step 6: Replay validation

1. Re-run identical command list against identical initial snapshot.
2. Diff full event stream and state deltas.
3. Fail on any mismatch.

## Expanded complexity backlog (beyond your 8 required cases)

These scenarios should also become explicit tests because they commonly break determinism.

1. Reaction races: Shield vs Counterspell timing windows.
2. Opportunity attack trigger while moving through threatened cells.
3. Forced movement through hazardous zones (push/pull/teleport distinction).
4. Concentration replacement chain with linked zone cleanup.
5. Concentration break from damage in same tick as expiry.
6. Simultaneous multiple start-of-turn effects on one actor.
7. Simultaneous end-of-turn effects from different sources.
8. Initiative tie breaks with summons and transformed entities.
9. Dead/unconscious actor skip semantics.
10. Revive during same round and initiative reinsertion policy.
11. Summon expiry and summoner death interaction.
12. Wild Shape revert when beast HP reaches zero.
13. Temporary hit points layering interactions.
14. Advantage/disadvantage consolidation rules under multiple modifiers.
15. Critical hit doubling and rider effect order.
16. Save-for-half damage plus rider condition application order.
17. Multi-target immunity/resistance/vulnerability split in same AoE.
18. Line-of-effect blocking changes after movement in same request.
19. Zone overlap ordering and additive/non-additive policies.
20. Enter-zone vs start-turn-zone trigger distinction.
21. Spell upcast scaling consistency under replay.
22. Readied action triggering in opponent turn.
23. Hidden information redaction parity without semantic drift.
24. WS vs REST parity for same command payload.
25. Idempotency on duplicate request_id submissions.
26. Partial failure behavior in multi-operation action graphs.
27. Command denial with zero side effects guarantee.
28. Snapshot resync after client revision gap.
29. Checkpoint restore replay parity after server restart.
30. Drift detection under high event throughput.

## Deterministic test criteria matrix

### Group A: Required scenario tests (expanded from your 8 requirements)

| Test ID     | Scenario                         | Expected deterministic assertions                                      |
| ----------- | -------------------------------- | ---------------------------------------------------------------------- |
| V02-DET-001 | Fighter multi-action turn        | Exact attack operation ordering and budget spend parity across replays |
| V02-DET-002 | Wall of Thorns caster-turn vines | Immediate damage + zone creation emitted once with stable zone_id      |
| V02-DET-003 | Wall of Fire target-turn circle  | End-turn tick ordering stable for all affected actors                  |
| V02-DET-004 | Burning Hands cone               | Cone targets and save order stable for same geometry                   |
| V02-DET-005 | Fireball range+size AoE          | Point/radius resolution and damage events identical across replays     |
| V02-DET-006 | Heavy Crossbow single target     | Hit/miss and damage deterministic with fixed seed and state            |
| V02-DET-007 | Animate Dead summon              | Summon id and initiative insertion deterministic                       |
| V02-DET-008 | Wild Shape transform             | Form swap and reversion snapshot deterministic                         |
| V02-DET-009 | Dawn multi-effect spell          | Cast impact + persistent area + tick sequence deterministic            |

### Group B: Determinism invariants

| Test ID     | Invariant                     | Expected deterministic assertions                     |
| ----------- | ----------------------------- | ----------------------------------------------------- |
| V02-DET-010 | Operation graph linearization | Same request yields same operation order list         |
| V02-DET-011 | Target snapshot immutability  | Snapshot hash unchanged for same input state          |
| V02-DET-012 | Event ordering contract       | Canonical ordering never violated                     |
| V02-DET-013 | RNG replay parity             | Roll stream exactly equal on replay                   |
| V02-DET-014 | Revision monotonicity         | Exactly one revision increment per successful command |
| V02-DET-015 | Denial side-effect isolation  | Denied command mutates nothing                        |

### Group C: Extended complexity tests

| Test ID     | Scenario                   | Expected deterministic assertions                            |
| ----------- | -------------------------- | ------------------------------------------------------------ |
| V02-DET-016 | Counterspell reaction race | Same winner/loser resolution for same event timing           |
| V02-DET-017 | Forced movement into zone  | Trigger semantics consistent with movement type              |
| V02-DET-018 | Concentration replacement  | Remove-old-before-start-new ordering stable                  |
| V02-DET-019 | Simultaneous tick effects  | Initiative and actor tie-break stable                        |
| V02-DET-020 | Summon + transform overlap | Entity ownership and initiative remain deterministic         |
| V02-DET-021 | WS/REST parity             | Same semantics and reason codes across transports            |
| V02-DET-022 | Duplicate request_id       | Second submission is idempotent and non-mutating             |
| V02-DET-023 | Resync after revision gap  | Client receives deterministic state_sync and resumes cleanly |
| V02-DET-024 | Restart replay parity      | Checkpoint restore reproduces same outcomes                  |

## Completion criteria for this concept package

This concept is considered implemented only when:

1. Every test in Groups A, B, and C exists and is executable.
2. Replay parity passes on repeated seeded runs with zero flakiness.
3. WS and REST outputs remain semantically identical.
4. Event contracts remain backward-stable for V02 scope.

## Verification command draft

1. docker compose --profile test run --rm backend-test pytest tests -k "request_action and operation" -q
2. docker compose --profile test run --rm backend-test pytest tests -k "effect and zone and concentration" -q
3. docker compose --profile test run --rm backend-test pytest tests -k "deterministic and replay" -q
4. docker compose --profile test run --rm backend-test pytest tests -k "summon or transform" -q
5. docker compose --profile test run --rm backend-test pytest tests -k "ws and rest and parity" -q
6. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
