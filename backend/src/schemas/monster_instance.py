from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .monster import MonsterResponse
from .item_instance import ItemInstance
from .effect import Effect

class MonsterInstance(BaseModel):
    id: str # Unique Instance ID
    monster_id: str # Reference to template
    template: Optional[MonsterResponse] = None
    
    # Instance State
    current_hp: int
    max_hp: int # Can differ from template if rolled
    temp_hp: int = 0
    
    initiative: Optional[int] = None
    
    # Position (Abstract for now, or grid coordinates)
    x: int = 0
    y: int = 0
    
    # Inventory & Effects
    inventory: List[ItemInstance] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list) # e.g. "Prone", "Poisoned"
    effects: List[Effect] = Field(default_factory=list)
