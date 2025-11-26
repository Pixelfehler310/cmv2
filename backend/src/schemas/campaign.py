from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .character import CharacterResponse

class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    dm_id: Optional[str] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignResponse(CampaignBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    characters: List[CharacterResponse] = []
