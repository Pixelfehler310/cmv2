import json
import os
from typing import List, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.item import Item
from ..models.spell import Spell
from ..models.monster import Monster
from ..schemas.item import ItemCreate
from ..schemas.spell import SpellCreate
from ..schemas.monster import MonsterCreate
from ..database import Base

T = TypeVar("T", bound=Base)

class DataLoader:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def load_json(self, filename: str) -> List[dict]:
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def import_items(self, session: AsyncSession, filename: str = "items.json"):
        data = self.load_json(filename)
        for item_data in data:
            # Check if exists
            stmt = select(Item).where(Item.name == item_data["name"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                item = Item(**item_data)
                session.add(item)
        await session.commit()

    async def import_spells(self, session: AsyncSession, filename: str = "spells.json"):
        data = self.load_json(filename)
        for spell_data in data:
            stmt = select(Spell).where(Spell.name == spell_data["name"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                spell = Spell(**spell_data)
                session.add(spell)
        await session.commit()

    async def import_monsters(self, session: AsyncSession, filename: str = "monsters.json"):
        data = self.load_json(filename)
        for monster_data in data:
            stmt = select(Monster).where(Monster.name == monster_data["name"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                monster = Monster(**monster_data)
                session.add(monster)
        await session.commit()
