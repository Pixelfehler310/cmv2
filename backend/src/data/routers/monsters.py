from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_db
from src.data.lib.monster import Monster
from src.schemas.monster import MonsterResponse

router = APIRouter(prefix="/monsters", tags=["Monsters"])


@router.get("", response_model=List[MonsterResponse])
async def get_monsters(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Monster).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{monster_id}", response_model=MonsterResponse)
async def get_monster(monster_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Monster).where(Monster.id == monster_id))
    monster = result.scalar_one_or_none()
    if not monster:
        raise HTTPException(status_code=404, detail="Monster not found")
    return monster
