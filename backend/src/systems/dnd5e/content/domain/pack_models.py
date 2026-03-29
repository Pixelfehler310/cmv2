__production_status__ = "gold"
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from .primitives import LifecycleState

class ContentPackRecord(BaseModel):
    id: str
    author_user_id: Optional[str] = None
    title: str
    lifecycle_state: LifecycleState
    is_homebrew: bool
    pack_key: Optional[str] = None
    compatibility_target: Optional[str] = None
    published_version: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    def publish(self) -> None:
        pass
        
    def archive(self) -> None:
        pass

    def restore(self) -> None:
        pass
