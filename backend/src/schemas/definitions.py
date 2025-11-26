from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from .base import GameEntity

class SpeciesBase(GameEntity):
    description: str
    speed: int = 30
    size: str = "Medium"
    ability_bonuses: Dict[str, int] = {}
    traits: List[Dict[str, Any]] = [] # List of Features or definitions
    languages: List[str] = []

class SpeciesResponse(SpeciesBase):
    id: str

class ClassBase(GameEntity):
    description: str
    hit_die: str
    proficiencies: Dict[str, Any] = {}
    saving_throws: List[str] = []
    progression: List[Dict[str, Any]] = []

class ClassResponse(ClassBase):
    id: str

class BackgroundBase(GameEntity):
    description: str
    skill_proficiencies: List[str] = []
    tool_proficiencies: List[str] = []
    equipment: List[str] = []
    feature: Dict[str, Any] = {}

class BackgroundResponse(BackgroundBase):
    id: str
