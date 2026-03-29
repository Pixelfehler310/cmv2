from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_db
from src.data.lib.monster import Monster
from src.schemas.monster import MonsterResponse

# [LEGACY][V05-05] Superseded by /api/compendium V05 transport endpoints.
router = APIRouter(prefix="/monsters", tags=["Monsters"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[MonsterResponse])
async def get_monsters(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    logger.info("GET /monsters called with skip=%s limit=%s", skip, limit)
    result = await db.execute(select(Monster).offset(skip).limit(limit))
    monsters = result.scalars().all()
    if not monsters:
        logger.warning(
            "GET /monsters returned 0 rows (skip=%s limit=%s)", skip, limit)
    logger.info("GET /monsters returning count=%s", len(monsters))
    return monsters


@router.get("/{monster_id}", response_model=MonsterResponse)
async def get_monster(monster_id: str, db: AsyncSession = Depends(get_db)):
    logger.info("GET /monsters/%s called", monster_id)
    result = await db.execute(select(Monster).where(Monster.id == monster_id))
    monster = result.scalar_one_or_none()
    if not monster:
        logger.warning("GET /monsters/%s not found", monster_id)
        raise HTTPException(status_code=404, detail="Monster not found")
    logger.info("GET /monsters/%s found", monster_id)
    return monster
