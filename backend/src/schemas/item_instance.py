from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from .item import ItemResponse

class ItemInstance(BaseModel):
    id: str # Unique ID for this specific instance in the inventory
    item_id: str # Reference to the template ID
    template: Optional[ItemResponse] = None # The full template data (hydrated)
    
    quantity: int = 1
    equipped: bool = False
    attuned: bool = False
    
    # Instance specific overrides or custom data (e.g. charges remaining)
    custom_name: Optional[str] = None
    current_charges: Optional[int] = None
