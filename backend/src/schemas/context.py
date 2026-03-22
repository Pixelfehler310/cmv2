from __future__ import annotations

from pydantic import BaseModel


class SceneOptionResponse(BaseModel):
    scene_id: str
    name: str


class EncounterOptionResponse(BaseModel):
    encounter_id: str
    scene_id: str
    name: str


class CampaignContextResponse(BaseModel):
    campaign_id: str
    scene_id: str | None = None
    encounter_id: str | None = None
    context_version: int = 0


class SelectCampaignContextRequest(BaseModel):
    scene_id: str
    encounter_id: str
