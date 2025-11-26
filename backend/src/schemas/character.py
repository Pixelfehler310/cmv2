from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from .base import GameEntity
from .item_instance import ItemInstance
from .effect import Effect

class CharacterBase(BaseModel):
    name: str
    player_name: Optional[str] = None
    campaign_id: Optional[str] = None
    
    species_id: str
    class_id: str
    background_id: Optional[str] = None
    
    level: int = 1
    xp: int = 0
    alignment: Optional[str] = None
    
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
    
    inventory: List[ItemInstance] = Field(default_factory=list)
    spells: List[Dict[str, Any]] = Field(default_factory=list)
    spell_slots: Dict[str, int] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    effects: List[Effect] = Field(default_factory=list)

class CharacterCreate(CharacterBase):
    pass

class CharacterResponse(CharacterBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    species: Optional[Any] = None # Typed as Any to avoid circular imports for now, or import properly
    char_class: Optional[Any] = None
    background: Optional[Any] = None
