# D&D 5e WebSocket Payloads

This document was auto-generated from `systems/dnd5e/event_types.py` via `scripts/generate_ws_docs.py`. Do not edit manually.

## Inbound Events (Client -> Server)

### `action`
Payload for `action` event — attack, spell, ability.

```json
{
  "actor_id": "string",
  "action_name": "string",
  "target_ids": []
}
```

### `add_actor`
Payload for `add_actor` event.

```json
{
  "definition_slug": "string",
  "name": {},
  "position": {}
}
```

### `apply_condition`
Payload for `apply_condition` event.

```json
{
  "actor_id": "string",
  "condition": "string",
  "source_id": {}
}
```

### `apply_damage`
Payload for `apply_damage` event.

```json
{
  "actor_id": "string",
  "amount": 0,
  "damage_type": "string"
}
```

### `apply_healing`
Payload for `apply_healing` event.

```json
{
  "actor_id": "string",
  "amount": 0
}
```

### `chat_message`
Payload for `chat_message` event.

```json
{
  "message": "string"
}
```

### `end_combat`
Payload for `end_combat` event.

```json
{}
```

### `end_turn`
Payload for `end_turn` event.

```json
{
  "actor_id": "string"
}
```

### `move_token`
Payload for `move_token` event.

```json
{
  "actor_id": "string",
  "path": []
}
```

### `remove_actor`
Payload for `remove_actor` event.

```json
{
  "actor_id": "string"
}
```

### `remove_condition`
Payload for `remove_condition` event.

```json
{
  "actor_id": "string",
  "condition": "string"
}
```

### `roll_dice`
Payload for `roll_dice` event.

```json
{
  "expression": "string",
  "purpose": {}
}
```

### `roll_initiative`
Payload for `roll_initiative` event.

```json
{
  "actor_id": "string",
  "value": {}
}
```

### `start_combat`
Payload for `start_combat` event.

```json
{}
```

### `update_hp`
Payload for `update_hp` event.

```json
{
  "actor_id": "string",
  "current_hp": 0,
  "temp_hp": {}
}
```

---

## Outbound Events (Server -> Client)

### `actor_damaged`
Payload for `actor_damaged` event.

```json
{
  "actor_id": "string",
  "amount": 0,
  "new_hp": 0,
  "source": "string"
}
```

### `actor_died`
Payload for `actor_died` event.

```json
{
  "actor_id": "string"
}
```

### `actor_healed`
Payload for `actor_healed` event.

```json
{
  "actor_id": "string",
  "amount": 0,
  "new_hp": 0
}
```

### `combat_ended`
Payload for `combat_ended` event.

```json
{}
```

### `combat_started`
Payload for `combat_started` event.

```json
{
  "initiative_order": []
}
```

### `condition_added`
Payload for `condition_added` event.

```json
{
  "actor_id": "string",
  "condition": "string",
  "source": "string"
}
```

### `condition_removed`
Payload for `condition_removed` event.

```json
{
  "actor_id": "string",
  "condition": "string"
}
```

### `dice_rolled`
Payload for `dice_rolled` event.

```json
{
  "roller_id": "string",
  "expression": "string",
  "result": 0
}
```

### `error`
Payload for `error` response.

```json
{
  "message": "string",
  "code": "string"
}
```

### `pong`
Payload for `pong` response.

```json
{}
```

### `turn_advanced`
Payload for `turn_advanced` event.

```json
{
  "active_actor_id": "string",
  "round": 0
}
```

