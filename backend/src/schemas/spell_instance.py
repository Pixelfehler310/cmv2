from typing import Optional
from pydantic import BaseModel
from .spell import SpellResponse

class SpellInstance(BaseModel):
    spell_id: str
    template: Optional[SpellResponse] = None
    
    prepared: bool = False
    always_prepared: bool = False # For domain spells etc.
