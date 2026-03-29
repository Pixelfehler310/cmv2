from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_db
from src.legacy.data.lib.spell import Spell
from src.schemas.spell import SpellResponse

# [LEGACY][V05-05] Superseded by /api/compendium V05 transport endpoints.
router = APIRouter(prefix="/spells", tags=["Spells"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[SpellResponse])
async def get_spells(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    logger.info("GET /spells called with skip=%s limit=%s", skip, limit)
    result = await db.execute(select(Spell).offset(skip).limit(limit))
    spells = result.scalars().all()
    if not spells:
        logger.warning(
            "GET /spells returned 0 rows (skip=%s limit=%s)", skip, limit)
    logger.info("GET /spells returning count=%s", len(spells))
    return spells


@router.get("/{spell_id}", response_model=SpellResponse)
async def get_spell(spell_id: str, db: AsyncSession = Depends(get_db)):
    logger.info("GET /spells/%s called", spell_id)
    result = await db.execute(select(Spell).where(Spell.id == spell_id))
    spell = result.scalar_one_or_none()
    if not spell:
        logger.warning("GET /spells/%s not found", spell_id)
        raise HTTPException(status_code=404, detail="Spell not found")
    logger.info("GET /spells/%s found", spell_id)
    return spell
