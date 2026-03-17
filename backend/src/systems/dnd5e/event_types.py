"""
D&D 5e WebSocket Event Types.

All inbound and outbound payload schemas for the D&D 5e game system.
Per architecture doc 09 § 4.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Inbound Payloads (Client → Server)
# ---------------------------------------------------------------------------

class ActionPayload(BaseModel):
    """Payload for `action` event — attack, spell, ability."""
    actor_id: str
    action_name: str
    action_type: str = "action"
    target_ids: List[str] = Field(default_factory=list)


class RequestActionPayload(BaseModel):
    """Payload for `request_action` event from player clients."""
    actor_id: str
    action_type: str = "action"
    action_name: str = ""
    payload: dict = Field(default_factory=dict)
    acting_as_user_id: Optional[str] = None


class MoveTokenPayload(BaseModel):
    """Payload for `move_token` event."""
    actor_id: str
    path: List[dict] = Field(default_factory=list)  # [{x, y}, ...]
    acting_as_user_id: Optional[str] = None


class RequestMovePreviewPayload(BaseModel):
    """Payload for `request_move_preview` event."""
    actor_id: str
    acting_as_user_id: Optional[str] = None


class RequestExecutableActionsPayload(BaseModel):
    """Payload for `request_executable_actions` event."""
    actor_id: str
    acting_as_user_id: Optional[str] = None


class RequestAttackPreviewPayload(BaseModel):
    """Payload for `request_attack_preview` event."""
    actor_id: str
    action_id: str
    template_origin: Optional[dict] = None
    template_direction: Optional[dict] = None
    acting_as_user_id: Optional[str] = None


class RollDicePayload(BaseModel):
    """Payload for `roll_dice` event."""
    expression: str
    purpose: Optional[str] = None


class EndTurnPayload(BaseModel):
    """Payload for `end_turn` event."""
    actor_id: str


class StartCombatPayload(BaseModel):
    """Payload for `start_combat` event."""
    pass


class EndCombatPayload(BaseModel):
    """Payload for `end_combat` event."""
    pass


class ApplyDamagePayload(BaseModel):
    """Payload for `apply_damage` event."""
    actor_id: str
    amount: int
    damage_type: str


class ApplyHealingPayload(BaseModel):
    """Payload for `apply_healing` event."""
    actor_id: str
    amount: int


class ApplyConditionPayload(BaseModel):
    """Payload for `apply_condition` event."""
    actor_id: str
    condition: str
    source_id: Optional[str] = None


class RemoveConditionPayload(BaseModel):
    """Payload for `remove_condition` event."""
    actor_id: str
    condition: str


class AddActorPayload(BaseModel):
    """Payload for `add_actor` event."""
    definition_slug: str
    name: Optional[str] = None
    position: Optional[dict] = None
    owner_user_id: Optional[str] = None


class RemoveActorPayload(BaseModel):
    """Payload for `remove_actor` event."""
    actor_id: str


class ChatMessagePayload(BaseModel):
    """Payload for `chat_message` event."""
    message: str


# ---------------------------------------------------------------------------
# Outbound Payloads (Server → Client)
# ---------------------------------------------------------------------------

class ErrorPayload(BaseModel):
    """Payload for `error` response."""
    message: str
    code: str


class TurnAdvancedPayload(BaseModel):
    """Payload for `turn_advanced` event."""
    active_actor_id: str
    round: int


class MovementPreviewPayload(BaseModel):
    """Payload for `movement_preview` event."""
    actor_id: str
    origin: dict
    movement_remaining: int
    reachable: List[dict] = Field(default_factory=list)


class AttackPreviewPayload(BaseModel):
    """Payload for `attack_preview` event."""
    actor_id: str
    action_id: str
    origin: dict
    eligible_target_ids: List[str] = Field(default_factory=list)
    eligible_cells: List[dict] = Field(default_factory=list)
    template_projection: Optional[dict] = None


class ActionAuthorizedPayload(BaseModel):
    """Payload for `action_authorized` event."""
    actor_id: str
    action_type: str
    action_name: str = ""


class ActionDeniedPayload(BaseModel):
    """Payload for `action_denied` event."""
    actor_id: str
    action_type: str
    reason_code: str
    message: str


class ActorDamagedPayload(BaseModel):
    """Payload for `actor_damaged` event."""
    actor_id: str
    amount: int
    new_hp: int
    source: str = ""


class ActorHealedPayload(BaseModel):
    """Payload for `actor_healed` event."""
    actor_id: str
    amount: int
    new_hp: int


class ActorDiedPayload(BaseModel):
    """Payload for `actor_died` event."""
    actor_id: str


class ConditionAddedPayload(BaseModel):
    """Payload for `condition_added` event."""
    actor_id: str
    condition: str
    source: str = ""


class ConditionRemovedPayload(BaseModel):
    """Payload for `condition_removed` event."""
    actor_id: str
    condition: str


class CombatStartedPayload(BaseModel):
    """Payload for `combat_started` event."""
    initiative_order: List[dict] = Field(default_factory=list)


class CombatEndedPayload(BaseModel):
    """Payload for `combat_ended` event."""
    pass


class DiceRolledPayload(BaseModel):
    """Payload for `dice_rolled` event."""
    roller_id: str
    expression: str
    result: int


class PongPayload(BaseModel):
    """Payload for `pong` response."""
    pass
