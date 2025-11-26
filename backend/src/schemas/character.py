from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from .base import GameEntity

class CharacterBase(BaseModel):
    name: str
    player_name: Optional[str] = None
    campaign_id: Optional[str] = None
    
    race: str
    class_name: str
    level: int = 1
    xp: int = 0
    alignment: Optional[str] = None
    background: Optional[str] = None
    
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    max_hp: int
    current_hp: int
    temp_hp: int = 0
    hit_dice: str
    armor_class: int = 10
    speed: int = 30
    initiative: int = 0
    
    inventory: List[Dict[str, Any]] = Field(default_factory=list)
    spells: List[Dict[str, Any]] = Field(default_factory=list)
    spell_slots: Dict[str, int] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    effects: List[Dict[str, Any]] = Field(default_factory=list)

class CharacterCreate(CharacterBase):
    pass

class CharacterResponse(CharacterBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
