from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .base import GameEntity

class ItemBase(GameEntity):
    type: str
    rarity: str
    weight: float = 0.0
    price: int = 0
    properties: Dict[str, Any] = Field(default_factory=dict)

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: str
