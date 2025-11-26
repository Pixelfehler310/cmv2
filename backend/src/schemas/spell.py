from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .base import GameEntity

class SpellBase(GameEntity):
    level: int
    school: str
    casting_time: str
    range: str
    components: Dict[str, Any] = Field(default_factory=dict)
    duration: str

class SpellCreate(SpellBase):
    pass

class SpellResponse(SpellBase):
    id: str
