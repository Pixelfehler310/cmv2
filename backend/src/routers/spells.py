from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import get_db
from ..models.spell import Spell
from ..schemas.spell import SpellResponse

router = APIRouter(prefix="/spells", tags=["Spells"])

@router.get("/", response_model=List[SpellResponse])
async def get_spells(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Spell).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{spell_id}", response_model=SpellResponse)
async def get_spell(spell_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Spell).where(Spell.id == spell_id))
    spell = result.scalar_one_or_none()
    if not spell:
        raise HTTPException(status_code=404, detail="Spell not found")
    return spell
