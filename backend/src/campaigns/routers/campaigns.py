from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.database import get_db
from src.campaigns.lib.campaign import Campaign, CampaignMember, CampaignRole
from src.campaigns.lib.character import Character
from src.schemas.campaign import CampaignCreate, CampaignResponse
from src.identity.models import User
from src.identity.dependencies import get_current_active_user

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def _campaign_with_character_relations():
    return (
        selectinload(Campaign.characters).selectinload(Character.species),
        selectinload(Campaign.characters).selectinload(Character.char_class),
        selectinload(Campaign.characters).selectinload(Character.background),
    )


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
