from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.campaigns.lib.campaign import CampaignMember
from src.database import get_db
from src.identity.dependencies import get_current_active_user
from src.identity.models import User

from .services.combat_service import CombatService

router = APIRouter(prefix="/campaigns", tags=["DND5E Encounter"])


@router.get("/{campaign_id}/encounter/state")
async def get_encounter_state(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    member_stmt = select(CampaignMember).where(
        CampaignMember.campaign_id == campaign_id,
        CampaignMember.user_id == current_user.id,
    )
    member_result = await db.execute(member_stmt)
    member = member_result.scalar_one_or_none()
    if member is None and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not a member of this campaign")

    service = CombatService(db)
    try:
        _, encounter = await service.load_or_create_encounter_state(campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return encounter.model_dump(mode="json")


@router.get("/{campaign_id}/encounter/action-log")
async def get_encounter_action_log(
    campaign_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    member_stmt = select(CampaignMember).where(
        CampaignMember.campaign_id == campaign_id,
        CampaignMember.user_id == current_user.id,
    )
    member_result = await db.execute(member_stmt)
    member = member_result.scalar_one_or_none()
    if member is None and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not a member of this campaign")

    service = CombatService(db)
    logs = await service.get_action_log(campaign_id, limit=min(max(limit, 1), 500))
    return [
        {
            "id": item.id,
            "request_id": item.request_id,
            "actor_id": item.actor_id,
            "action_type": item.action_type,
            "action_state": item.action_state,
            "denial_reason": item.denial_reason,
            "authorization_checks": item.authorization_checks,
            "payload": item.payload,
            "created_at": item.created_at,
        }
        for item in logs
    ]
