from __future__ import annotations

import re
from typing import Any


_ALLOWED_ACTION_REF_KEYS = {"action_id", "display_name"}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_")


def canonical_action_id(monster_name: str, action_token: str) -> str:
    monster_slug = slugify(monster_name) or "unknown_monster"
    action_slug = slugify(action_token) or "basic_attack"
    if action_slug in {"basicattack", "basic_attack"}:
        action_slug = "basic_attack"
    return f"monster.{monster_slug}.{action_slug}"


def normalize_monster_actions(monster_name: str, actions: Any) -> list[dict[str, str]]:
    if not isinstance(actions, list):
        return []

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()

    for entry in actions:
        if not isinstance(entry, dict):
            continue

        raw_action_id = str(entry.get("action_id") or "").strip()
        raw_display_name = str(entry.get("display_name") or "").strip()
        legacy_name = str(entry.get("name") or entry.get(
            "action_name") or "").strip()

        if raw_action_id.startswith("monster."):
            action_id = raw_action_id
        elif raw_action_id:
            action_id = canonical_action_id(monster_name, raw_action_id)
            if not raw_display_name:
                raw_display_name = raw_action_id
        elif legacy_name:
            action_id = canonical_action_id(monster_name, legacy_name)
            if not raw_display_name:
                raw_display_name = legacy_name
        else:
            continue

        if action_id in seen:
            continue

        action_ref: dict[str, str] = {"action_id": action_id}
        if raw_display_name:
            action_ref["display_name"] = raw_display_name

        normalized.append(action_ref)
        seen.add(action_id)

    return normalized


def is_strict_action_ref_list(actions: Any) -> bool:
    if not isinstance(actions, list):
        return False

    seen: set[str] = set()
    for entry in actions:
        if not isinstance(entry, dict):
            return False
        if set(entry.keys()) - _ALLOWED_ACTION_REF_KEYS:
            return False

        action_id = entry.get("action_id")
        if not isinstance(action_id, str) or not action_id.strip():
            return False
        normalized_action_id = action_id.strip()
        if normalized_action_id in seen:
            return False
        seen.add(normalized_action_id)

        display_name = entry.get("display_name")
        if display_name is not None and not isinstance(display_name, str):
            return False

    return True
