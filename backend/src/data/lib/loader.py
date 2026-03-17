import json
import logging
from pathlib import Path
from typing import List, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.data.lib.item import Item
from src.data.lib.spell import Spell
from src.data.lib.monster import Monster
from src.data.lib.species import Species
from src.data.lib.class_model import ClassModel
from src.data.lib.background import Background
from src.data.lib.feat import Feat
from src.data.lib.feature import Feature
from src.campaigns.lib.campaign import Campaign
from src.campaigns.lib.character import Character
from src.systems.dnd5e.services.content_pack_importer import ContentPackImporter, ConflictPolicy
from src.database import Base

logger = logging.getLogger(__name__)


class DataLoader:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_json_dir(self, directory: str) -> List[dict]:
        target_dir = self.data_dir / directory
        if not target_dir.exists() or not target_dir.is_dir():
            logger.warning(
                f"Fixture directory not found or invalid: {target_dir}")
            return []

        results = []
        for file_path in target_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Support legacy array format if any remains
                        results.extend(data)
                    else:
                        results.append(data)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
        logger.info(f"Loaded {len(results)} JSON object(s) from {target_dir}")
        return results

    async def _import_generic(self, session: AsyncSession, directory: str, model: Type[Base], name_field: str = "name"):
        summary = {
            "directory": directory,
            "model": model.__name__,
            "discovered": 0,
            "inserted": 0,
            "skipped_existing": 0,
            "failed": 0,
        }
        data = self.load_json_dir(directory)
        summary["discovered"] = len(data)

        for item_data in data:
            item_name = item_data.get(name_field, "unknown")
            if name_field not in item_data:
                logger.error(
                    f"Missing required key '{name_field}' for {model.__name__} in directory '{directory}'"
                )
                summary["failed"] += 1
                continue

            stmt = select(model).where(
                getattr(model, name_field) == item_data[name_field])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                summary["skipped_existing"] += 1
                continue

            try:
                instance = model(**item_data)
                session.add(instance)
                summary["inserted"] += 1
            except Exception as e:
                logger.error(
                    f"Failed to instantiate {model.__name__} from data {item_name}: {e}"
                )
                summary["failed"] += 1
        await session.commit()
        logger.info(
            f"Import summary for {directory}: discovered={summary['discovered']}, "
            f"inserted={summary['inserted']}, skipped_existing={summary['skipped_existing']}, failed={summary['failed']}"
        )
        return summary

    async def import_items(self, session: AsyncSession):
        return await self._import_generic(session, "items", Item)

    async def import_spells(self, session: AsyncSession):
        return await self._import_generic(session, "spells", Spell)

    async def import_monsters(self, session: AsyncSession):
        return await self._import_generic(session, "monsters", Monster)

    async def import_definitions(self, session: AsyncSession):
        target_dir = self.data_dir / "definitions"
        summary = {
            "directory": "definitions",
            "discovered": 0,
            "inserted": 0,
            "skipped_existing": 0,
            "failed": 0,
            "unknown_prefix": 0,
        }
        if not target_dir.exists():
            logger.warning(
                f"Definitions fixture directory not found: {target_dir}")
            return summary

        for file_path in target_dir.glob("*.json"):
            summary["discovered"] += 1
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                name = data.get("name")
                if file_path.name.startswith("species_"):
                    model = Species
                elif file_path.name.startswith("class_"):
                    model = ClassModel
                elif file_path.name.startswith("background_"):
                    model = Background
                elif file_path.name.startswith("feat_"):
                    model = Feat
                elif file_path.name.startswith("feature_"):
                    model = Feature
                else:
                    logger.warning(
                        f"Unknown definition prefix for {file_path.name}")
                    summary["unknown_prefix"] += 1
                    continue

                stmt = select(model).where(model.name == name)
                result = await session.execute(stmt)
                if not result.scalar_one_or_none():
                    session.add(model(**data))
                    summary["inserted"] += 1
                else:
                    summary["skipped_existing"] += 1
            except Exception as e:
                logger.error(
                    f"Failed to import definition {file_path.name}: {e}")
                summary["failed"] += 1
        await session.commit()
        logger.info(
            f"Import summary for definitions: discovered={summary['discovered']}, "
            f"inserted={summary['inserted']}, skipped_existing={summary['skipped_existing']}, "
            f"failed={summary['failed']}, unknown_prefix={summary['unknown_prefix']}"
        )
        return summary

    async def import_campaigns(self, session: AsyncSession):
        return await self._import_generic(session, "campaigns", Campaign)

    async def import_characters(self, session: AsyncSession):
        return await self._import_generic(session, "characters", Character)

    async def import_content_packs(
        self,
        session: AsyncSession,
        directory: str = "content_packs",
        conflict_policy: ConflictPolicy = "reject_conflict",
    ):
        summary = {
            "directory": directory,
            "discovered": 0,
            "imported": 0,
            "failed": 0,
            "results": [],
        }

        packs = self.load_json_dir(directory)
        summary["discovered"] = len(packs)
        if not packs:
            return summary

        importer = ContentPackImporter()
        for payload in packs:
            try:
                result = await importer.import_content_pack(
                    session,
                    payload,
                    conflict_policy=conflict_policy,
                )
                summary["results"].append(result)
                if result.get("status") == "failed":
                    summary["failed"] += 1
                else:
                    summary["imported"] += 1
            except Exception as e:
                logger.error("Failed to import content pack: %s", e)
                summary["failed"] += 1

        return summary

    async def load_all(self, session: AsyncSession):
        summary = {
            "definitions": await self.import_definitions(session),
            "items": await self.import_items(session),
            "spells": await self.import_spells(session),
            "monsters": await self.import_monsters(session),
            "campaigns": await self.import_campaigns(session),
            "characters": await self.import_characters(session),
            "content_packs": await self.import_content_packs(session),
        }
        logger.info(f"Completed DataLoader.load_all with summary: {summary}")
        return summary
