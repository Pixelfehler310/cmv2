from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .character import CharacterResponse


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    dm_id: Optional[str] = None


class CampaignCreate(CampaignBase):
    pass


class CampaignMemberResponse(BaseModel):
    user_id: str
    role: str
    active_character_id: Optional[str] = None


class CampaignResponse(CampaignBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    characters: List[CharacterResponse] = []
    current_scene: Optional[str] = None
    active_encounter_id: Optional[str] = None
    context_version: int = 0
    # We can include members if needed, or just the current user's role
    role: Optional[str] = None  # Computed field for the current user
