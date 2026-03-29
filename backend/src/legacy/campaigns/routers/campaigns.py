from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.database import get_db
from src.legacy.campaigns.lib.campaign import Campaign, CampaignMember, CampaignRole
from src.legacy.campaigns.lib.character import Character
from src.schemas.campaign import CampaignCreate, CampaignResponse
from src.schemas.context import (
    CampaignContextResponse,
    EncounterOptionResponse,
    SceneOptionResponse,
    SelectCampaignContextRequest,
)
from src.identity.models import User
from src.identity.dependencies import get_current_active_user
from src.systems.dnd5e.application.context_service import CampaignContextApplicationService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def _campaign_with_character_relations():
    return (
        selectinload(Campaign.characters).selectinload(Character.species),
        selectinload(Campaign.characters).selectinload(Character.char_class),
        selectinload(Campaign.characters).selectinload(Character.background),
    )


async def _resolve_member_or_raise(
    db: AsyncSession,
    campaign_id: str,
    current_user: User,
) -> tuple[CampaignMember | None, bool]:
    from src.config import settings

    is_admin = current_user.username == settings.ADMIN_USERNAME or current_user.is_superuser
    stmt = select(CampaignMember).where(
        CampaignMember.campaign_id == campaign_id,
        CampaignMember.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()
    if member is None and not is_admin:
        raise HTTPException(
            status_code=403, detail="Not a member of this campaign")
    return member, is_admin


@router.post("", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 1. Create Campaign
    db_campaign = Campaign(**campaign.model_dump())
    db_campaign.dm_id = str(current_user.id)  # Legacy support
    db.add(db_campaign)
    await db.flush()  # Get ID

    # 2. Create Member (DM)
    member = CampaignMember(
        campaign_id=db_campaign.id,
        user_id=current_user.id,
        role=CampaignRole.DM
    )
    db.add(member)

    await db.commit()

    # Refresh with relationships loaded
    stmt = select(Campaign).options(
        *_campaign_with_character_relations()).where(Campaign.id == db_campaign.id)
    result = await db.execute(stmt)
    db_campaign_loaded = result.scalar_one()

    # Return with role
    response = CampaignResponse.model_validate(db_campaign_loaded)
    response.role = "DM"
    return response


@router.get("", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from src.config import settings
    # Admin bypass
    is_admin = current_user.username == settings.ADMIN_USERNAME or current_user.is_superuser
    if is_admin:
        stmt = (
            select(Campaign)
            .options(*_campaign_with_character_relations())
            .offset(skip).limit(limit)
        )
        result = await db.execute(stmt)
        campaigns = []
        for campaign in result.scalars():
            resp = CampaignResponse.model_validate(campaign)
            resp.role = "DM"
            campaigns.append(resp)
        return campaigns

    # Fetch campaigns where user is a member
    stmt = (
        select(Campaign, CampaignMember.role)
        .options(*_campaign_with_character_relations())
        .join(CampaignMember, Campaign.id == CampaignMember.campaign_id)
        .where(CampaignMember.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)

    campaigns = []
    for campaign, role in result:
        resp = CampaignResponse.model_validate(campaign)
        resp.role = role
        campaigns.append(resp)

    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from src.config import settings
    is_admin = current_user.username == settings.ADMIN_USERNAME or current_user.is_superuser

    # Check membership
    stmt = select(CampaignMember).where(
        CampaignMember.campaign_id == campaign_id,
        CampaignMember.user_id == current_user.id
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member and not is_admin:
        raise HTTPException(
            status_code=403, detail="Not a member of this campaign")

    # Fetch campaign
    result = await db.execute(
        select(Campaign)
        .options(*_campaign_with_character_relations())
        .where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    resp = CampaignResponse.model_validate(campaign)
    resp.role = "DM" if is_admin else member.role
    return resp


@router.post("/{campaign_id}/join")
async def join_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if already member
    stmt = select(CampaignMember).where(
        CampaignMember.campaign_id == campaign_id,
        CampaignMember.user_id == current_user.id
    )
    if (await db.execute(stmt)).scalar_one_or_none():
        return {"message": "Already joined"}

    # Check if campaign exists
    if not await db.get(Campaign, campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Add as Player
    member = CampaignMember(
        campaign_id=campaign_id,
        user_id=current_user.id,
        role=CampaignRole.PLAYER
    )
    db.add(member)
    await db.commit()

    return {"message": "Joined successfully", "role": "PLAYER"}


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from src.config import settings
    is_admin = current_user.username == settings.ADMIN_USERNAME or current_user.is_superuser

    if not is_admin:
        # Check if DM
        stmt = select(CampaignMember).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == current_user.id,
            CampaignMember.role == CampaignRole.DM
        )
        if not (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(
                status_code=403, detail="Only DM can delete campaign")

    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await db.delete(campaign)
    await db.commit()
    return {"ok": True}


@router.get("/{campaign_id}/context", response_model=CampaignContextResponse)
async def get_campaign_context(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _resolve_member_or_raise(db, campaign_id, current_user)

    service = CampaignContextApplicationService(db)
    try:
        campaign = await service.get_context(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return CampaignContextResponse(
        campaign_id=campaign.id,
        scene_id=campaign.current_scene,
        encounter_id=campaign.active_encounter_id,
        context_version=campaign.context_version,
    )


@router.get("/{campaign_id}/scenes", response_model=List[SceneOptionResponse])
async def list_campaign_scenes(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _resolve_member_or_raise(db, campaign_id, current_user)

    service = CampaignContextApplicationService(db)
    try:
        scenes = await service.list_scenes(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [SceneOptionResponse(scene_id=scene.scene_id, name=scene.name) for scene in scenes]


@router.get("/{campaign_id}/scenes/{scene_id}/encounters", response_model=List[EncounterOptionResponse])
async def list_scene_encounters(
    campaign_id: str,
    scene_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _resolve_member_or_raise(db, campaign_id, current_user)

    service = CampaignContextApplicationService(db)
    try:
        encounters = await service.list_encounters(campaign_id, scene_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [
        EncounterOptionResponse(
            encounter_id=encounter.encounter_id,
            scene_id=encounter.scene_id,
            name=encounter.name,
        )
        for encounter in encounters
    ]


@router.post("/{campaign_id}/context/select", response_model=CampaignContextResponse)
async def select_campaign_context(
    campaign_id: str,
    request: SelectCampaignContextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    member, is_admin = await _resolve_member_or_raise(db, campaign_id, current_user)
    if not is_admin and (member is None or member.role != CampaignRole.DM):
        raise HTTPException(
            status_code=403, detail="Only DM can change campaign context")

    service = CampaignContextApplicationService(db)
    try:
        campaign = await service.select_context(campaign_id, request.scene_id, request.encounter_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return CampaignContextResponse(
        campaign_id=campaign.id,
        scene_id=campaign.current_scene,
        encounter_id=campaign.active_encounter_id,
        context_version=campaign.context_version,
    )
