import pytest
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.campaigns.router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_websocket_observer_connection():
    # Test connecting as an observer
    with client.websocket_connect("/campaigns/test_123/ws?role=observer") as websocket:
        # Upon connection, we should immediately receive the current state
        data = websocket.receive_text()
        payload = json.loads(data)
        
        assert payload["event_type"] == "STATE_UPDATE"
        state = payload["data"]
        assert state["round"] == 1
        
        # Test Sanitization: Observer should NOT see exact HP, but should see percentages
        goblin = next(c for c in state["combatants"] if c["id"] == "goblin_1")
        assert "hp_current" not in goblin
        assert "hp_max" not in goblin
        assert "hp_percent" in goblin
        assert goblin["hp_percent"] == 1.0 # 7/7

def test_websocket_dm_connection_and_intent():
    # Test connecting as a DM
    with client.websocket_connect("/campaigns/test_123/ws?role=dm") as websocket:
        data = websocket.receive_text()
        payload = json.loads(data)
        
        # Test DM Privileges: DM DOES see exact HP
        state = payload["data"]
        goblin = next(c for c in state["combatants"] if c["id"] == "goblin_1")
        assert "hp_current" in goblin
        assert "hp_max" in goblin
        
        # Test Intent: DM moves the goblin
        intent = {
            "action": "MOVE_TOKEN",
            "payload": {
                "target_id": "goblin_1",
                "path": [(6, 11), (6, 12)]
            }
        }
        websocket.send_text(json.dumps(intent))
        
        # The server should respond by broadcasting the new state
        new_data = websocket.receive_text()
        new_payload = json.loads(new_data)
        
        new_state = new_payload["data"]
        moved_goblin = next(c for c in new_state["combatants"] if c["id"] == "goblin_1")
        assert moved_goblin["x"] == 6
        assert moved_goblin["y"] == 12
