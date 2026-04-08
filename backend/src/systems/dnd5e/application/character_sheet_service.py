from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.legacy.campaigns.lib.character import Character
from src.legacy.data.lib.background import Background
from src.legacy.data.lib.class_model import ClassModel
from src.legacy.data.lib.species import Species
from src.systems.dnd5e.application.character_service import CharacterWriteDenied
from src.systems.dnd5e.character.sheet_models import CharacterSheetProjection, ResolutionStatus
from src.systems.dnd5e.character.sheet_projection_model import CharacterSheetProjectionModel
from src.systems.dnd5e.content.infrastructure.orm import CompendiumDefinitionModel


class CharacterSheetProjectionService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def project_character_sheet(
        self,
        character_id: str,
        *,
        catalog_revision: int,
    ) -> CharacterSheetProjection:
        character = await self._db.get(Character, character_id)
        if character is None:
            raise CharacterWriteDenied(
                code="CHARACTER_NOT_FOUND",
                message=f"Character {character_id} not found.",
            )

        if not character.campaign_id:
            raise CharacterWriteDenied(
                code="MISSING_CAMPAIGN_ID",
                message="Character is missing campaign_id.",
            )

        campaign_id = character.campaign_id

        cached = await self._db.get(CharacterSheetProjectionModel, character_id)
        if cached is not None and catalog_revision <= cached.catalog_revision:
            return self._projection_from_model(cached)

        now = datetime.now(timezone.utc)
        current_sheet_revision = cached.sheet_revision if cached is not None else 0

        if cached is not None and catalog_revision > cached.catalog_revision + 1:
            projection = CharacterSheetProjection(
                character_id=character.id,
                campaign_id=campaign_id,
                catalog_revision=catalog_revision,
                sheet_revision=current_sheet_revision,
                resolution_status="invalidated",
                computed_fields={},
                last_resolved_at=now,
                denial_reason_code="CATALOG_REVISION_MISMATCH",
                unresolved_reference_ids=[],
            )
            await self._upsert_projection(projection)
            return projection

        unresolved_reference_ids: list[str] = []
        denial_reason_code: str | None = None

        class_id = character.class_id
        if not class_id:
            denial_reason_code = "UNRESOLVED_CLASS_DEFINITION"
        else:
            class_exists = (
                await self._db.execute(select(ClassModel.id).where(ClassModel.id == class_id))
            ).scalar_one_or_none()
            if class_exists is None:
                denial_reason_code = "UNRESOLVED_CLASS_DEFINITION"
                unresolved_reference_ids.append(class_id)

        species_id = character.species_id
        if not species_id:
            if denial_reason_code is None:
                denial_reason_code = "UNRESOLVED_SPECIES_DEFINITION"
        else:
            species_exists = (
                await self._db.execute(select(Species.id).where(Species.id == species_id))
            ).scalar_one_or_none()
            if species_exists is None:
                if denial_reason_code is None:
                    denial_reason_code = "UNRESOLVED_SPECIES_DEFINITION"
                unresolved_reference_ids.append(species_id)

        if character.background_id:
            background_exists = (
                await self._db.execute(
                    select(Background.id).where(Background.id == character.background_id)
                )
            ).scalar_one_or_none()
            if background_exists is None:
                if denial_reason_code is None:
                    denial_reason_code = "UNRESOLVED_BACKGROUND_DEFINITION"
                unresolved_reference_ids.append(character.background_id)

        if character.ability_ids:
            resolved_ability_ids = set(
                (
                    await self._db.execute(
                        select(CompendiumDefinitionModel.id).where(
                            CompendiumDefinitionModel.family == "ability",
                            CompendiumDefinitionModel.id.in_(character.ability_ids),
                        )
                    )
                ).scalars()
            )
            unresolved_ability_ids = [
                ability_id
                for ability_id in character.ability_ids
                if ability_id not in resolved_ability_ids
            ]
            if unresolved_ability_ids:
                if denial_reason_code is None:
                    denial_reason_code = "UNRESOLVED_ABILITY_DEFINITION"
                unresolved_reference_ids.extend(unresolved_ability_ids)

        if denial_reason_code is not None:
            projection = CharacterSheetProjection(
                character_id=character.id,
                campaign_id=campaign_id,
                catalog_revision=catalog_revision,
                sheet_revision=current_sheet_revision,
                resolution_status="denied",
                computed_fields={},
                last_resolved_at=now,
                denial_reason_code=denial_reason_code,
                unresolved_reference_ids=unresolved_reference_ids,
            )
            await self._upsert_projection(projection)
            return projection

        projection = CharacterSheetProjection(
            character_id=character.id,
            campaign_id=campaign_id,
            catalog_revision=catalog_revision,
            sheet_revision=current_sheet_revision + 1,
            resolution_status="resolved",
            computed_fields=self._build_computed_fields(character),
            last_resolved_at=now,
        )
        await self._upsert_projection(projection)
        return projection

    @staticmethod
    def _build_computed_fields(character: Character) -> dict:
        return {
            "name": character.name,
            "status": character.status,
            "level": character.level,
            "class_id": character.class_id,
            "species_id": character.species_id,
            "background_id": character.background_id,
            "ability_ids": list(character.ability_ids or []),
            "attributes": {
                "strength": character.strength,
                "dexterity": character.dexterity,
                "constitution": character.constitution,
                "intelligence": character.intelligence,
                "wisdom": character.wisdom,
                "charisma": character.charisma,
            },
            "vitals": {
                "max_hp": character.max_hp,
                "current_hp": character.current_hp,
                "temp_hp": character.temp_hp,
                "armor_class": character.armor_class,
                "initiative": character.initiative,
                "speed": character.speed,
            },
        }

    @staticmethod
    def _projection_from_model(model: CharacterSheetProjectionModel) -> CharacterSheetProjection:
        last_resolved_at = model.last_resolved_at
        if last_resolved_at.tzinfo is None:
            last_resolved_at = last_resolved_at.replace(tzinfo=timezone.utc)

        return CharacterSheetProjection(
            character_id=model.character_id,
            campaign_id=model.campaign_id,
            catalog_revision=model.catalog_revision,
            sheet_revision=model.sheet_revision,
            resolution_status=cast(ResolutionStatus, model.resolution_status),
            computed_fields=model.computed_fields or {},
            last_resolved_at=last_resolved_at,
            denial_reason_code=model.denial_reason_code,
            unresolved_reference_ids=model.unresolved_reference_ids or [],
        )

    async def _upsert_projection(self, projection: CharacterSheetProjection) -> None:
        model = await self._db.get(CharacterSheetProjectionModel, projection.character_id)
        if model is None:
            model = CharacterSheetProjectionModel(
                character_id=projection.character_id,
                campaign_id=projection.campaign_id,
                catalog_revision=projection.catalog_revision,
                sheet_revision=projection.sheet_revision,
                resolution_status=projection.resolution_status,
                denial_reason_code=projection.denial_reason_code,
                unresolved_reference_ids=list(projection.unresolved_reference_ids),
                computed_fields=dict(projection.computed_fields),
                last_resolved_at=projection.last_resolved_at,
            )
            self._db.add(model)
        else:
            model.campaign_id = projection.campaign_id
            model.catalog_revision = projection.catalog_revision
            model.sheet_revision = projection.sheet_revision
            model.resolution_status = projection.resolution_status
            model.denial_reason_code = projection.denial_reason_code
            model.unresolved_reference_ids = list(projection.unresolved_reference_ids)
            model.computed_fields = dict(projection.computed_fields)
            model.last_resolved_at = projection.last_resolved_at

        await self._db.commit()
