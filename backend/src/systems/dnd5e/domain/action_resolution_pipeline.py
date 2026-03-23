from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActionResolutionRequest:
    actor_id: str
    action_id: str
    action_type_cost: str
    family: str
    targeting_mode: str
    target_ids: list[str]
    payload: dict[str, Any]


@dataclass
class ActionResolutionContext:
    campaign_id: str
    request_id: str | None
    round_number: int
    active_actor_id: str | None


@dataclass
class ActionResolutionDenial:
    reason_code: str
    message: str
    checks: dict[str, Any] | None = None


@dataclass
class ActionResolutionSuccess:
    events: list[dict[str, Any]]
    checks: dict[str, Any] | None = None
