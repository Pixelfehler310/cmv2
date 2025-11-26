from typing import Optional, Any, Literal
from pydantic import BaseModel, Field

class Effect(BaseModel):
    """
    Represents a modifier or rule change applied to a game entity.
    V1 Focus: Static Modifiers.
    """
    name: str
    description: Optional[str] = None
    
    # What kind of modification is this?
    # BONUS: Add to existing value (e.g. +1 AC)
    # SET: Override existing value (e.g. Set Str to 19)
    # MULTIPLY: Scale value (e.g. Speed * 2) - Maybe later
    type: Literal["BONUS", "SET"] 
    
    # What attribute is being modified?
    # e.g. "armor_class", "strength", "speed.walk", "skills.stealth"
    target: str 
    
    # The value to apply. 
    # For V1, we expect static integers mostly.
    value: int
    
    # Source of the effect (e.g. "Item: Shield", "Spell: Bless")
    source: Optional[str] = None
