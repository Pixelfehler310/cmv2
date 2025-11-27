from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.common.database import get_db
from src.campaigns.lib.character import Character
from src.schemas.character import CharacterCreate, CharacterResponse

router = APIRouter(prefix="/characters", tags=["Characters"])

@router.post("/", response_model=CharacterResponse)
async def create_character(character: CharacterCreate, db: AsyncSession = Depends(get_db)):
    db_character = Character(**character.model_dump())
    db.add(db_character)
    await db.commit()
    await db.refresh(db_character)
    return db_character

@router.get("/", response_model=List[CharacterResponse])
async def get_characters(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Character)
        .options(selectinload(Character.species), selectinload(Character.char_class), selectinload(Character.background))
        .offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Character)
        .options(selectinload(Character.species), selectinload(Character.char_class), selectinload(Character.background))
        .where(Character.id == character_id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(character_id: str, character_update: CharacterCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    for key, value in character_update.model_dump().items():
        setattr(character, key, value)
    
    await db.commit()
    await db.refresh(character)
    return character

@router.delete("/{character_id}")
async def delete_character(character_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    await db.delete(character)
    await db.commit()
    return {"ok": True}
