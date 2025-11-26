from pydantic import BaseModel
from typing import List, Optional

class DieRoll(BaseModel):
    sides: int
    count: int
    rolls: List[int]
    total: int

class DiceRollResult(BaseModel):
    expression: str
    total: int
    breakdown: str  # Human readable string, e.g. "[15] + 5"
    detailed_rolls: List[DieRoll]
