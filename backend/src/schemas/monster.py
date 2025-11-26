from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .base import GameEntity

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
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    legendary_actions: List[Dict[str, Any]] = Field(default_factory=list)
    inventory: List[Dict[str, Any]] = Field(default_factory=list)
    effects: List[Dict[str, Any]] = Field(default_factory=list)

class MonsterCreate(MonsterBase):
    pass

class MonsterResponse(MonsterBase):
    id: str
