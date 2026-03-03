import json
import asyncio
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# In a real app, this would be imported from src.engine
# We will mock the Encounter state for this bridge prototype
class MockEncounterState:
    def __init__(self):
        self.round = 1
        self.combatants = [
            {"id": "hero_1", "public_name": "Arannis", "hp_current": 45, "hp_max": 45, "x": 5, "y": 10},
            {"id": "goblin_1", "public_name": "Goblin", "hp_current": 7, "hp_max": 7, "x": 6, "y": 11}
        ]
        
    def to_json(self):
        return {
            "round": self.round,
            "combatants": self.combatants
        }

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

class ConnectionManager:
    def __init__(self):
        # We store connections as dicts: {"socket": WebSocket, "role": "dm" | "observer"}
        self.active_connections: List[Dict[str, Any]] = []
        # In MVP, we just hold one global encounter state in memory
        self.encounter = MockEncounterState()

    async def connect(self, websocket: WebSocket, role: str):
        await websocket.accept()
        self.active_connections.append({"socket": websocket, "role": role})
        # Immediately send the current state upon connection
        await self._send_state_to(websocket, role)

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [c for c in self.active_connections if c["socket"] != websocket]

    async def broadcast_state(self):
        for connection in self.active_connections:
            await self._send_state_to(connection["socket"], connection["role"])
            
    async def _send_state_to(self, websocket: WebSocket, role: str):
        state = self.encounter.to_json()
        
        # Sanitization logic for observer (Stage View)
        if role != "dm":
            sanitized_combatants = []
            for c in state["combatants"]:
                sanitized_c = {k: v for k, v in c.items() if k not in ["hp_current", "hp_max"]}
                # Add HP percentage for the stage view rings
                sanitized_c["hp_percent"] = c["hp_current"] / max(1, c["hp_max"])
                sanitized_combatants.append(sanitized_c)
            state["combatants"] = sanitized_combatants
            
        payload = {
            "event_type": "STATE_UPDATE",
            "data": state
        }
        await websocket.send_text(json.dumps(payload))
        
    def handle_intent(self, intent_json: dict):
        """Maps incoming intents to engine state changes."""
        action = intent_json.get("action")
        payload = intent_json.get("payload", {})
        
        if action == "MOVE_TOKEN":
            target_id = payload.get("target_id")
            path = payload.get("path", [])
            if path and target_id:
                final_x, final_y = path[-1]
                for c in self.encounter.combatants:
                    if c["id"] == target_id:
                        c["x"] = final_x
                        c["y"] = final_y
                        break

manager = ConnectionManager()

@router.websocket("/{campaign_id}/ws")
async def websocket_endpoint(websocket: WebSocket, campaign_id: str, role: str = "observer"):
    await manager.connect(websocket, role)
    try:
        while True:
            # Wait for any messages from the client (Intents)
            data = await websocket.receive_text()
            intent = json.loads(data)
            
            # Only DM should be sending intents in MVP
            if role == "dm":
                manager.handle_intent(intent)
                # Broadcast new state to EVERYONE
                await manager.broadcast_state()
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
