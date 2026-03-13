from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_db
from src.data.lib.species import Species
from src.data.lib.class_model import ClassModel
from src.data.lib.background import Background
from src.schemas.definitions import (
    SpeciesBase, SpeciesResponse,
    ClassBase, ClassResponse,
    BackgroundBase, BackgroundResponse
)

router = APIRouter(prefix="/definitions", tags=["Definitions"])
logger = logging.getLogger(__name__)

# Species


@router.post("/species", response_model=SpeciesResponse)
async def create_species(species: SpeciesBase, db: AsyncSession = Depends(get_db)):
    db_species = Species(**species.model_dump())
    db.add(db_species)
    await db.commit()
    await db.refresh(db_species)
    return db_species


@router.get("/species", response_model=List[SpeciesResponse])
async def get_all_species(db: AsyncSession = Depends(get_db)):
    logger.info("GET /definitions/species called")
    result = await db.execute(select(Species))
    species = result.scalars().all()
    if not species:
        logger.warning("GET /definitions/species returned 0 rows")
    logger.info("GET /definitions/species returning count=%s", len(species))
    return species

# Classes


@router.post("/classes", response_model=ClassResponse)
async def create_class(char_class: ClassBase, db: AsyncSession = Depends(get_db)):
    db_class = ClassModel(**char_class.model_dump())
    db.add(db_class)
    await db.commit()
    await db.refresh(db_class)
    return db_class


@router.get("/classes", response_model=List[ClassResponse])
async def get_all_classes(db: AsyncSession = Depends(get_db)):
    logger.info("GET /definitions/classes called")
    result = await db.execute(select(ClassModel))
    classes = result.scalars().all()
    if not classes:
        logger.warning("GET /definitions/classes returned 0 rows")
    logger.info("GET /definitions/classes returning count=%s", len(classes))
    return classes

# Backgrounds


@router.post("/backgrounds", response_model=BackgroundResponse)
async def create_background(background: BackgroundBase, db: AsyncSession = Depends(get_db)):
    db_bg = Background(**background.model_dump())
    db.add(db_bg)
    await db.commit()
    await db.refresh(db_bg)
    return db_bg


@router.get("/backgrounds", response_model=List[BackgroundResponse])
async def get_all_backgrounds(db: AsyncSession = Depends(get_db)):
    logger.info("GET /definitions/backgrounds called")
    result = await db.execute(select(Background))
    backgrounds = result.scalars().all()
    if not backgrounds:
        logger.warning("GET /definitions/backgrounds returned 0 rows")
    logger.info("GET /definitions/backgrounds returning count=%s", len(backgrounds))
    return backgrounds
