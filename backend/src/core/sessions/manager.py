"""
Session Manager.

Manages in-memory campaign rooms, user connections, and visibility-aware
broadcasting. System-agnostic — the dispatch layer decides *what* to
broadcast; this layer decides *who* receives it.

Per architecture doc 09 § 3.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import WebSocket

from .models import CampaignRoom, ConnectedUser, SessionContext, UserRole
from ..ws_protocol import Visibility, WsOutbound

logger = logging.getLogger(__name__)


class SessionManager:
    """In-memory registry of campaign rooms and connected users."""

    def __init__(self) -> None:
        self._rooms: dict[str, CampaignRoom] = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def register_connection(
        self,
        campaign_id: str,
        user: ConnectedUser,
        *,
        game_system: str = "dnd5e",
    ) -> SessionContext:
        """Add a user to a campaign room; creates the room if needed."""
        if campaign_id not in self._rooms:
            self._rooms[campaign_id] = CampaignRoom(
                campaign_id=campaign_id,
                game_system=game_system,
            )

        room = self._rooms[campaign_id]
        room.users[user.user_id] = user

        logger.info(
            "User %s (%s) joined room %s",
            user.display_name, user.role.value, campaign_id,
        )

        return SessionContext(
            campaign_id=campaign_id,
            user_id=user.user_id,
            display_name=user.display_name,
            role=user.role,
            game_system=room.game_system,
        )

    def unregister_connection(self, campaign_id: str, user_id: str) -> None:
        """Remove a user from a campaign room. Deletes room if empty."""
        room = self._rooms.get(campaign_id)
        if room is None:
            return

        room.users.pop(user_id, None)
        logger.info("User %s left room %s", user_id, campaign_id)

        if room.is_empty():
            del self._rooms[campaign_id]
            logger.info("Room %s is empty — removed", campaign_id)

    # ------------------------------------------------------------------
    # Room queries
    # ------------------------------------------------------------------

    def get_room(self, campaign_id: str) -> Optional[CampaignRoom]:
        return self._rooms.get(campaign_id)

    def list_campaign_ids(self) -> list[str]:
        return list(self._rooms.keys())

    def get_connected_users(self, campaign_id: str) -> list[ConnectedUser]:
        room = self._rooms.get(campaign_id)
        if room is None:
            return []
        return list(room.users.values())

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def broadcast(
        self,
        campaign_id: str,
        event: WsOutbound,
    ) -> None:
        """Send an event to the appropriate recipients based on visibility."""
        room = self._rooms.get(campaign_id)
        if room is None:
            return

        payload = event.model_dump(mode="json", exclude={
                                   "visibility", "target_user_id"})

        for user in room.users.values():
            if self._should_receive(user, event):
                try:
                    await user.ws.send_json(payload)
                except Exception as exc:
                    logger.warning(
                        "Failed to send event type=%s to user=%s in campaign=%s: %s",
                        event.type,
                        user.user_id,
                        campaign_id,
                        exc,
                    )

    async def send_to_user(
        self,
        campaign_id: str,
        user_id: str,
        event: WsOutbound,
    ) -> None:
        """Send an event to a specific user in a room."""
        room = self._rooms.get(campaign_id)
        if room is None:
            logger.debug(
                "send_to_user skipped: missing room campaign=%s user=%s",
                campaign_id,
                user_id,
            )
            return

        user = room.users.get(user_id)
        if user is None:
            logger.debug(
                "send_to_user skipped: missing user campaign=%s user=%s",
                campaign_id,
                user_id,
            )
            return

        payload = event.model_dump(mode="json", exclude={
                                   "visibility", "target_user_id"})
        try:
            await user.ws.send_json(payload)
        except Exception as exc:
            logger.warning(
                "Failed to send event type=%s to user=%s in campaign=%s: %s",
                event.type,
                user_id,
                campaign_id,
                exc,
            )

    # ------------------------------------------------------------------
    # Delegation
    # ------------------------------------------------------------------

    def start_delegation(self, campaign_id: str, controlling_user_id: str, target_user_id: str) -> tuple[bool, str]:
        """Start delegation: controlling_user takes control as target_user.

        Returns: (success, reason_code_or_message)
        Fails if target_user not connected or already in delegation.
        """
        room = self._rooms.get(campaign_id)
        if room is None:
            return False, "campaign_not_found"

        # Verify target user is connected
        if target_user_id not in room.users:
            return False, "target_user_not_connected"

        # Already delegating from this user?
        if controlling_user_id in room.active_delegations:
            return False, "already_delegating"

        room.active_delegations[controlling_user_id] = target_user_id
        logger.info(
            "Delegation started: campaign=%s controlling_user=%s target_user=%s",
            campaign_id, controlling_user_id, target_user_id,
        )
        return True, ""

    def stop_delegation(self, campaign_id: str, controlling_user_id: str) -> bool:
        """Stop delegation: controlling_user resumes normal authority.

        Returns: True if delegation was active and stopped, False otherwise.
        """
        room = self._rooms.get(campaign_id)
        if room is None:
            return False

        if controlling_user_id not in room.active_delegations:
            return False

        del room.active_delegations[controlling_user_id]
        logger.info(
            "Delegation stopped: campaign=%s controlling_user=%s",
            campaign_id, controlling_user_id,
        )
        return True

    def get_delegation(self, campaign_id: str, controlling_user_id: str) -> Optional[str]:
        """Get current delegation for a user, or None if not delegating.

        Returns: target_user_id if delegating, None otherwise.
        """
        room = self._rooms.get(campaign_id)
        if room is None:
            return None
        return room.active_delegations.get(controlling_user_id)

    def resolve_effective_user_id(self, campaign_id: str, user_id: str) -> str:
        """Get effective user_id: if delegating, return target; else return user_id."""
        target = self.get_delegation(campaign_id, user_id)
        return target if target else user_id

    # ------------------------------------------------------------------
    # Visibility logic
    # ------------------------------------------------------------------

    @staticmethod
    def _should_receive(user: ConnectedUser, event: WsOutbound) -> bool:
        """Determine if a user should receive an event based on visibility."""
        vis = event.visibility

        if vis == Visibility.ALL:
            return True

        if vis == Visibility.DM_ONLY:
            return user.role == UserRole.DM

        if vis == Visibility.ACTOR_OWNER:
            # DM always sees everything; otherwise only the target user
            return user.role == UserRole.DM or user.user_id == event.target_user_id

        if vis == Visibility.EXCLUDE_ACTOR:
            return user.user_id != event.target_user_id

        return True
