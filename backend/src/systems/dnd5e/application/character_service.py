from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.identity.models import User
from src.legacy.campaigns.lib.campaign import CampaignMember
from src.legacy.campaigns.lib.character import Character
from src.legacy.data.lib.background import Background
from src.legacy.data.lib.class_model import ClassModel
from src.legacy.data.lib.species import Species
from src.schemas.character import CharacterResponse
from src.systems.dnd5e.content.infrastructure.orm import CompendiumDefinitionModel


class CharacterWritePayload(BaseModel):
    name: str
    player_name: str | None = None
    campaign_id: str
    player_id: str
    status: str
    species_id: str
    class_id: str
    background_id: str | None = None
    ability_ids: list[str] = Field(default_factory=list)

    level: int = 1
    xp: int = 0
    alignment: str | None = None

    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    max_hp: int
    current_hp: int
    temp_hp: int = 0
    hit_dice: str
    armor_class: int = 10
    speed: int = 30
    initiative: int = 0

    inventory: list[Any] = Field(default_factory=list)
    spells: list[dict[str, Any]] = Field(default_factory=list)
    spell_slots: dict[str, int] = Field(default_factory=dict)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    effects: list[Any] = Field(default_factory=list)


@dataclass(slots=True)
class CharacterWriteDenied(Exception):
    code: str
    message: str
    unresolved_reference_ids: list[str] = field(default_factory=list)


class CharacterWriteApplicationService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def list_characters(
        self,
        *,
        campaign_id: str,
        player_id: str,
        current_user: User,
    ) -> list[CharacterResponse]:
        if not campaign_id.strip():
            raise CharacterWriteDenied(
                code="MISSING_CAMPAIGN_ID",
                message="campaign_id is required.",
            )
        if not player_id.strip():
            raise CharacterWriteDenied(
                code="MISSING_PLAYER_ID",
                message="player_id is required.",
            )

        if not current_user.is_superuser:
            current_user_id = str(current_user.id)
            if player_id != current_user_id:
                raise CharacterWriteDenied(
                    code="PLAYER_OWNERSHIP_VIOLATION",
                    message="Authenticated user does not own this character scope.",
                )

            member_stmt = select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == player_id,
            )
            member = (await self._db.execute(member_stmt)).scalar_one_or_none()
            if member is None:
                raise CharacterWriteDenied(
                    code="CAMPAIGN_MEMBERSHIP_REQUIRED",
                    message="Player is not a member of the target campaign.",
                )

        stmt = (
            select(Character)
            .where(
                Character.campaign_id == campaign_id,
                Character.player_id == player_id,
            )
            .order_by(Character.id.asc())
        )
        rows = (await self._db.execute(stmt)).scalars().all()
        return [self._to_response(character) for character in rows]

    async def create_character(
        self,
        payload: CharacterWritePayload,
        *,
        current_user: User,
    ) -> CharacterResponse:
        await self._validate_payload(payload)
        await self._validate_ownership(payload, current_user=current_user)
        await self._validate_references(payload)

        character = Character(
            name=payload.name,
            player_name=payload.player_name,
            player_id=payload.player_id,
            status=payload.status,
            campaign_id=payload.campaign_id,
            species_id=payload.species_id,
            class_id=payload.class_id,
            background_id=payload.background_id,
            level=payload.level,
            xp=payload.xp,
            alignment=payload.alignment,
            strength=payload.strength,
            dexterity=payload.dexterity,
            constitution=payload.constitution,
            intelligence=payload.intelligence,
            wisdom=payload.wisdom,
            charisma=payload.charisma,
            max_hp=payload.max_hp,
            current_hp=payload.current_hp,
            temp_hp=payload.temp_hp,
            hit_dice=payload.hit_dice,
            armor_class=payload.armor_class,
            speed=payload.speed,
            initiative=payload.initiative,
            inventory=payload.inventory,
            spells=payload.spells,
            spell_slots=payload.spell_slots,
            actions=payload.actions,
            ability_ids=list(payload.ability_ids),
            effects=payload.effects,
        )
        self._db.add(character)
        await self._db.commit()
        await self._db.refresh(character)
        return self._to_response(character)

    async def update_character(
        self,
        character_id: str,
        payload: CharacterWritePayload,
        *,
        current_user: User,
    ) -> CharacterResponse:
        await self._validate_payload(payload)
        await self._validate_ownership(payload, current_user=current_user)
        await self._validate_references(payload)

        character = await self._db.get(Character, character_id)
        if character is None:
            raise CharacterWriteDenied(
                code="CHARACTER_NOT_FOUND",
                message=f"Character {character_id} not found.",
            )

        if character.campaign_id and character.campaign_id != payload.campaign_id:
            raise CharacterWriteDenied(
                code="CAMPAIGN_OWNERSHIP_VIOLATION",
                message="Character campaign scope cannot be reassigned.",
            )

        character.name = payload.name
        character.player_name = payload.player_name
        character.player_id = payload.player_id
        character.status = payload.status
        character.campaign_id = payload.campaign_id
        character.species_id = payload.species_id
        character.class_id = payload.class_id
        character.background_id = payload.background_id
        character.level = payload.level
        character.xp = payload.xp
        character.alignment = payload.alignment
        character.strength = payload.strength
        character.dexterity = payload.dexterity
        character.constitution = payload.constitution
        character.intelligence = payload.intelligence
        character.wisdom = payload.wisdom
        character.charisma = payload.charisma
        character.max_hp = payload.max_hp
        character.current_hp = payload.current_hp
        character.temp_hp = payload.temp_hp
        character.hit_dice = payload.hit_dice
        character.armor_class = payload.armor_class
        character.speed = payload.speed
        character.initiative = payload.initiative
        character.inventory = payload.inventory
        character.spells = payload.spells
        character.spell_slots = payload.spell_slots
        character.actions = payload.actions
        character.ability_ids = list(payload.ability_ids)
        character.effects = payload.effects

        await self._db.commit()
        await self._db.refresh(character)
        return self._to_response(character)

    @staticmethod
    async def _validate_payload(payload: CharacterWritePayload) -> None:
        if not payload.campaign_id.strip():
            raise CharacterWriteDenied(
                code="MISSING_CAMPAIGN_ID",
                message="campaign_id is required.",
            )
        if not payload.player_id.strip():
            raise CharacterWriteDenied(
                code="MISSING_PLAYER_ID",
                message="player_id is required.",
            )

        required_fields = {
            "name": payload.name,
            "status": payload.status,
            "class_id": payload.class_id,
            "species_id": payload.species_id,
        }
        for field_name, value in required_fields.items():
            if isinstance(value, str) and not value.strip():
                raise CharacterWriteDenied(
                    code="MISSING_REQUIRED_FIELD",
                    message=f"{field_name} is required.",
                )

        if payload.level < 1:
            raise CharacterWriteDenied(
                code="INVALID_LEVEL_VALUE",
                message="level must be >= 1.",
            )

        if len(payload.ability_ids) != len(set(payload.ability_ids)):
            raise CharacterWriteDenied(
                code="DUPLICATE_ABILITY_IDS",
                message="ability_ids cannot contain duplicates.",
            )

    async def _validate_ownership(
        self,
        payload: CharacterWritePayload,
        *,
        current_user: User,
    ) -> None:
        if current_user.is_superuser:
            return

        current_user_id = str(current_user.id)
        if payload.player_id != current_user_id:
            raise CharacterWriteDenied(
                code="PLAYER_OWNERSHIP_VIOLATION",
                message="Authenticated user does not own this character payload.",
            )

        member_stmt = select(CampaignMember).where(
            CampaignMember.campaign_id == payload.campaign_id,
            CampaignMember.user_id == payload.player_id,
        )
        member = (await self._db.execute(member_stmt)).scalar_one_or_none()
        if member is None:
            raise CharacterWriteDenied(
                code="CAMPAIGN_MEMBERSHIP_REQUIRED",
                message="Player is not a member of the target campaign.",
            )

    async def _validate_references(self, payload: CharacterWritePayload) -> None:
        class_exists = (
            await self._db.execute(select(ClassModel.id).where(ClassModel.id == payload.class_id))
        ).scalar_one_or_none()
        if class_exists is None:
            raise CharacterWriteDenied(
                code="UNRESOLVED_CLASS_DEFINITION",
                message="class_id does not resolve.",
                unresolved_reference_ids=[payload.class_id],
            )

        species_exists = (
            await self._db.execute(select(Species.id).where(Species.id == payload.species_id))
        ).scalar_one_or_none()
        if species_exists is None:
            raise CharacterWriteDenied(
                code="UNRESOLVED_SPECIES_DEFINITION",
                message="species_id does not resolve.",
                unresolved_reference_ids=[payload.species_id],
            )

        if payload.background_id:
            background_exists = (
                await self._db.execute(
                    select(Background.id).where(
                        Background.id == payload.background_id)
                )
            ).scalar_one_or_none()
            if background_exists is None:
                raise CharacterWriteDenied(
                    code="UNRESOLVED_BACKGROUND_DEFINITION",
                    message="background_id does not resolve.",
                    unresolved_reference_ids=[payload.background_id],
                )

        if payload.ability_ids:
            resolved_ability_ids = set(
                (
                    await self._db.execute(
                        select(CompendiumDefinitionModel.id).where(
                            CompendiumDefinitionModel.family == "ability",
                            CompendiumDefinitionModel.id.in_(
                                payload.ability_ids),
                        )
                    )
                ).scalars()
            )
            unresolved_ability_ids = [
                ability_id for ability_id in payload.ability_ids if ability_id not in resolved_ability_ids
            ]
            if unresolved_ability_ids:
                raise CharacterWriteDenied(
                    code="UNRESOLVED_ABILITY_DEFINITION",
                    message="One or more ability_ids do not resolve.",
                    unresolved_reference_ids=unresolved_ability_ids,
                )

    @staticmethod
    def _to_response(character: Character) -> CharacterResponse:
        return CharacterResponse.model_validate(
            {
                "id": character.id,
                "name": character.name,
                "player_name": character.player_name,
                "player_id": character.player_id,
                "status": character.status,
                "campaign_id": character.campaign_id,
                "species_id": character.species_id,
                "class_id": character.class_id,
                "background_id": character.background_id,
                "ability_ids": character.ability_ids or [],
                "level": character.level,
                "xp": character.xp,
                "alignment": character.alignment,
                "strength": character.strength,
                "dexterity": character.dexterity,
                "constitution": character.constitution,
                "intelligence": character.intelligence,
                "wisdom": character.wisdom,
                "charisma": character.charisma,
                "max_hp": character.max_hp,
                "current_hp": character.current_hp,
                "temp_hp": character.temp_hp,
                "hit_dice": character.hit_dice,
                "armor_class": character.armor_class,
                "speed": character.speed,
                "initiative": character.initiative,
                "inventory": character.inventory or [],
                "spells": character.spells or [],
                "spell_slots": character.spell_slots or {},
                "actions": character.actions or [],
                "effects": character.effects or [],
                "species": None,
                "char_class": None,
                "background": None,
            }
        )
