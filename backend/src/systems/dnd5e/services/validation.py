"""
Stateless domain validation and parsing helpers for the D&D 5e combat system.

Extracted from ws_handler.py to enforce SRP — these are pure functions
with no WebSocket, session, or persistence dependencies.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from ..schemas.enums import (
    Ability,
    ActionType,
    ConditionType,
    DamageType,
    DurationType,
)
from ..schemas.common import AbilityScores, SaveRequirement
from ..schemas.definitions import ActionDefinition
from ..schemas.encounter import EncounterState
from ..schemas.instances import ActorInstance


# ---------------------------------------------------------------------------
# Action family constants
# ---------------------------------------------------------------------------

ACTION_FAMILY_ATTACK = "attack"
ACTION_FAMILY_SAVE = "save"
ACTION_FAMILY_HEALING = "healing"
ACTION_FAMILY_UTILITY = "utility"


# ---------------------------------------------------------------------------
# Safe coercion utilities
# ---------------------------------------------------------------------------

def safe_int(value: Any, default: int | None = None) -> int | None:
    """Safely coerce a value to int, returning default on failure."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_int_list(value: Any) -> list[int] | None:
    """Safely coerce a list of values to ints, returning None on any failure."""
    if not isinstance(value, list):
        return None
    parsed: list[int] = []
    for entry in value:
        try:
            parsed.append(int(entry))
        except (TypeError, ValueError):
            return None
    return parsed


# ---------------------------------------------------------------------------
# Enum parsing helpers
# ---------------------------------------------------------------------------

def parse_damage_type(raw_value: Any) -> DamageType:
    """Parse a raw value into a DamageType enum, defaulting to BLUDGEONING."""
    if isinstance(raw_value, DamageType):
        return raw_value
    normalized = str(raw_value or "").strip().lower()
    for candidate in DamageType:
        if candidate.value == normalized:
            return candidate
    return DamageType.BLUDGEONING


def parse_ability(raw_value: Any) -> Ability:
    """Parse a raw value into an Ability enum, defaulting to DEX."""
    normalized = str(raw_value or "").strip().lower()
    mapping = {
        "str": Ability.STR,
        "strength": Ability.STR,
        "dex": Ability.DEX,
        "dexterity": Ability.DEX,
        "con": Ability.CON,
        "constitution": Ability.CON,
        "int": Ability.INT,
        "intelligence": Ability.INT,
        "wis": Ability.WIS,
        "wisdom": Ability.WIS,
        "cha": Ability.CHA,
        "charisma": Ability.CHA,
    }
    return mapping.get(normalized, Ability.DEX)


def parse_condition(raw_value: Any) -> ConditionType | None:
    """Parse a raw value into a ConditionType enum, returning None on failure."""
    if isinstance(raw_value, ConditionType):
        return raw_value
    normalized = str(raw_value or "").strip().lower()
    if not normalized:
        return None
    for condition in ConditionType:
        if condition.value.lower() == normalized:
            return condition
    return None


# ---------------------------------------------------------------------------
# Action family resolution
# ---------------------------------------------------------------------------

def resolve_action_family(
    action_name: str,
    action_payload: dict[str, Any],
    targets: list[ActorInstance],
) -> str | None:
    """Determine the action family (attack/save/healing/utility) from payload heuristics."""
    family_value = str(action_payload.get("family", "")).strip().lower()
    if family_value in {ACTION_FAMILY_ATTACK, ACTION_FAMILY_SAVE, ACTION_FAMILY_HEALING, ACTION_FAMILY_UTILITY}:
        return family_value

    resolution_hint = str(action_payload.get("resolution", "")).strip().lower()
    if resolution_hint in {ACTION_FAMILY_ATTACK, ACTION_FAMILY_SAVE, ACTION_FAMILY_HEALING, ACTION_FAMILY_UTILITY}:
        return resolution_hint

    if "save" in action_payload or "save_dc" in action_payload or "save_ability" in action_payload:
        return ACTION_FAMILY_SAVE

    if any(key in action_payload for key in {"condition", "remove_condition", "condition_op"}):
        return ACTION_FAMILY_UTILITY

    lowered_name = action_name.strip().lower()
    if any(token in lowered_name for token in {"heal", "cure", "mend"}):
        return ACTION_FAMILY_HEALING
    if any(token in lowered_name for token in {"save", "breath", "blast", "fireball"}):
        return ACTION_FAMILY_SAVE
    if any(token in lowered_name for token in {"condition", "stun", "poison", "prone", "grapple"}):
        return ACTION_FAMILY_UTILITY
    if targets:
        return ACTION_FAMILY_ATTACK

    return ACTION_FAMILY_UTILITY


# ---------------------------------------------------------------------------
# Action definition builder
# ---------------------------------------------------------------------------

def build_action_definition(
    family: str,
    actor: ActorInstance,
    action_name: str,
    action_payload: dict[str, Any],
) -> ActionDefinition:
    """Construct an ActionDefinition from raw payload and actor stats."""
    attack_bonus = safe_int(action_payload.get(
        "attack_bonus"), default=actor.proficiency_bonus)
    damage_dice = str(action_payload.get("damage_dice") or "1d8")
    damage_bonus = safe_int(action_payload.get("damage_bonus"), default=0)
    damage_type = parse_damage_type(action_payload.get("damage_type"))

    if family == ACTION_FAMILY_SAVE:
        save_data = action_payload.get("save", {}) if isinstance(
            action_payload.get("save"), dict) else {}
        ability = parse_ability(save_data.get(
            "ability") or action_payload.get("save_ability"))
        save_dc = safe_int(save_data.get("dc") or action_payload.get(
            "save_dc"), default=10 + actor.proficiency_bonus)
        on_success = str(save_data.get("on_success") or action_payload.get(
            "save_on_success") or "half_damage")
        on_fail = str(save_data.get("on_fail") or action_payload.get(
            "save_on_fail") or "full_damage")
        return ActionDefinition(
            name=action_name,
            action_type=ActionType.SAVE_EFFECT,
            damage_dice=damage_dice,
            damage_bonus=damage_bonus,
            damage_type=damage_type,
            save=SaveRequirement(
                ability=ability,
                dc=save_dc,
                on_success=on_success,
                on_fail=on_fail,
            ),
        )

    if family == ACTION_FAMILY_HEALING:
        return ActionDefinition(
            name=action_name,
            action_type=ActionType.HEALING,
            damage_dice=str(action_payload.get("heal_dice") or damage_dice),
            damage_bonus=safe_int(action_payload.get(
                "heal_bonus"), default=damage_bonus),
        )

    if family == ACTION_FAMILY_UTILITY:
        return ActionDefinition(
            name=action_name,
            action_type=ActionType.UTILITY,
        )

    # Default: attack family
    attack_mode = str(action_payload.get("attack_mode") or action_payload.get(
        "attack_type") or "").strip().lower()
    action_type = ActionType.MELEE_WEAPON
    if attack_mode in {"ranged", "ranged_weapon"}:
        action_type = ActionType.RANGED_WEAPON
    elif attack_mode in {"melee_spell", "spell_melee"}:
        action_type = ActionType.MELEE_SPELL
    elif attack_mode in {"ranged_spell", "spell_ranged"}:
        action_type = ActionType.RANGED_SPELL

    return ActionDefinition(
        name=action_name,
        action_type=action_type,
        attack_bonus=attack_bonus,
        damage_dice=damage_dice,
        damage_bonus=damage_bonus,
        damage_type=damage_type,
    )


# ---------------------------------------------------------------------------
# Naming / ID helpers
# ---------------------------------------------------------------------------

def display_name_from_slug(definition_slug: str) -> str:
    """Convert a definition slug to a display name."""
    cleaned = re.sub(r"[_-]+", " ", definition_slug).strip()
    if not cleaned:
        return "Monster"
    return " ".join(part.capitalize() for part in cleaned.split())


def next_actor_id(encounter: EncounterState, definition_slug: str) -> str:
    """Generate the next unique actor ID based on definition slug."""
    slug_base = re.sub(r"[^a-z0-9]+", "_",
                       definition_slug.lower()).strip("_")
    if not slug_base:
        slug_base = "actor"

    existing_ids = {actor.id for actor in encounter.combatants}
    index = 1
    while f"{slug_base}_{index}" in existing_ids:
        index += 1
    return f"{slug_base}_{index}"


# ---------------------------------------------------------------------------
# Preview denial normalization
# ---------------------------------------------------------------------------

def normalize_preview_denial_reason(reason_code: str | None, message: str | None) -> str:
    """Normalize preview denial reason codes for consistent client handling."""
    if reason_code and reason_code != "invalid_target":
        return reason_code

    lowered_message = str(message or "").lower()
    if "out of map bounds" in lowered_message:
        return "invalid_template_origin"
    if "out of action range" in lowered_message:
        return "template_out_of_range"
    return reason_code or "invalid_action"


# ---------------------------------------------------------------------------
# Effect provenance helpers
# ---------------------------------------------------------------------------

def effect_provenance_payload(
    request_id: str | None,
    action_name: str | None,
    source_actor_id: str | None,
) -> dict[str, Any]:
    """Build an effect provenance payload dict."""
    return {
        "command_request_id": request_id,
        "action_id": action_name,
        "source_actor_id": source_actor_id,
    }


def effect_instance_canonical_id(effect: Any) -> str:
    """Get the canonical ID for an effect instance."""
    return effect.effect_id or effect.name or effect.id


def collect_effect_provenance_by_instance(
    events: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Collect effect provenance data keyed by instance ID from domain events."""
    provenance_by_instance: dict[str, dict[str, Any]] = {}
    for event in events:
        event_type = event.get("type", "")
        if event_type not in {"effect_applied", "effect_refreshed", "effect_removed", "effect_tick_resolved"}:
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        instance_id = payload.get("effect_instance_id")
        provenance = payload.get("provenance")
        if isinstance(instance_id, str) and isinstance(provenance, dict):
            provenance_by_instance[instance_id] = provenance
    return provenance_by_instance
