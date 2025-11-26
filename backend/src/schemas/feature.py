from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from .base import GameEntity

class FeatureBase(GameEntity):
    description: str
    source: str
    level_required: int = 1
    effects: List[Dict[str, Any]] = []

class FeatureResponse(FeatureBase):
    id: str

class FeatBase(GameEntity):
    description: str
    prerequisites: Optional[str] = None
    effects: List[Dict[str, Any]] = []

class FeatResponse(FeatBase):
    id: str
