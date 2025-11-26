from typing import List, Optional, Any
from pydantic import BaseModel, Field

class EffectConfig(BaseModel):
    """
    Represents a dynamic effect in the game logic.
    Example: {"trigger": "ON_EQUIP", "action": "ADD_AC", "value": 1}
    """
    trigger: str
    action: str
    value: Any
    target: Optional[str] = None


class GameEntity(BaseModel):
    """
    Base class for all game entities (Items, Spells, Feats).
    """
    name: str
    description: Optional[str] = None
    effects: List[EffectConfig] = Field(default_factory=list)
