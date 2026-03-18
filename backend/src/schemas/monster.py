import re
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .base import GameEntity
from .effect import Effect


_MONSTER_ACTION_ID_RE = re.compile(
    r"^monster\.[a-z0-9_]+\.[a-z0-9_]+(?:\.[a-z0-9_]+)*$")


class MonsterActionRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(min_length=1)
    display_name: Optional[str] = None

    @field_validator("action_id")
    @classmethod
    def validate_action_id(cls, value: str) -> str:
        action_id = value.strip()
        if not action_id:
            raise ValueError("action_id must be a non-empty string")
        if not _MONSTER_ACTION_ID_RE.match(action_id):
            raise ValueError(
                "action_id must be a canonical monster action reference (example: monster.goblin.scimitar)"
            )
        return action_id


class MonsterBase(GameEntity):
    size: str
    type: str
    alignment: str

    armor_class: int
    hit_points: int
    hit_dice: str
    speed: Dict[str, int]

    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

    proficiencies: List[Dict[str, Any]] = Field(default_factory=list)
    senses: Dict[str, Any] = Field(default_factory=dict)
    languages: str
    challenge_rating: float
    xp: int

    special_abilities: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[MonsterActionRef] = Field(default_factory=list)
    legendary_actions: List[Dict[str, Any]] = Field(default_factory=list)
    inventory: List[Dict[str, Any]] = Field(default_factory=list)
    effects: List[Effect] = Field(default_factory=list)

    @field_validator("actions")
    @classmethod
    def validate_unique_action_refs(cls, actions: List[MonsterActionRef]) -> List[MonsterActionRef]:
        action_ids = [action.action_id for action in actions]
        if len(set(action_ids)) != len(action_ids):
            raise ValueError(
                "actions must not contain duplicate action_id values")
        return actions


class MonsterCreate(MonsterBase):
    pass


class MonsterResponse(MonsterBase):
    id: str
