__production_status__ = "gold"
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, model_validator

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

    @model_validator(mode="after")
    def validate_lifecycle_state(self) -> "ContentPackRecord":
        if self.lifecycle_state == LifecycleState.SUPERSEDED:
            raise ValueError("Content packs cannot use superseded lifecycle state.")
        return self
    
    def publish(self) -> None:
        pass
        
    def archive(self) -> None:
        pass

    def restore(self) -> None:
        pass
