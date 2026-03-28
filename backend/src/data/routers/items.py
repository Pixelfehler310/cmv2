from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_db
from src.data.lib.item import Item
from src.schemas.item import ItemResponse

# [LEGACY][V05-05] Superseded by /api/compendium V05 transport endpoints.
router = APIRouter(prefix="/items", tags=["Items"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[ItemResponse])
async def get_items(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    logger.info("GET /items called with skip=%s limit=%s", skip, limit)
    result = await db.execute(select(Item).offset(skip).limit(limit))
    items = result.scalars().all()
    if not items:
        logger.warning(
            "GET /items returned 0 rows (skip=%s limit=%s)", skip, limit)
    logger.info("GET /items returning count=%s", len(items))
    return items


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str, db: AsyncSession = Depends(get_db)):
    logger.info("GET /items/%s called", item_id)
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        logger.warning("GET /items/%s not found", item_id)
        raise HTTPException(status_code=404, detail="Item not found")
    logger.info("GET /items/%s found", item_id)
    return item
