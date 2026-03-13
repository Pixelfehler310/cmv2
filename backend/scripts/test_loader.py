import asyncio
import logging
from pathlib import Path

from src.database import engine, Base, AsyncSessionLocal
from src.data.lib.loader import DataLoader
from sqlalchemy.future import select
from src.campaigns.lib.character import Character

logging.basicConfig(level=logging.INFO)

async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    fixtures_dir = Path(__file__).parent.parent / "data" / "fixtures"
    loader = DataLoader(str(fixtures_dir))
    
    async with AsyncSessionLocal() as session:
        await loader.load_all(session)
        
        # Verify Character was inserted
        res = await session.execute(select(Character))
        chars = res.scalars().all()
        print(f"Loaded {len(chars)} characters")

if __name__ == "__main__":
    asyncio.run(run())
