"""
Tests for core WS Protocol models.
"""

from src.core.ws_protocol import WsEnvelope, WsOutbound, Visibility, WsErrorCode


class TestWsEnvelope:

    def test_parse_minimal(self):
        raw = '{"type": "ping"}'
        env = WsEnvelope.model_validate_json(raw)
        assert env.type == "ping"
        assert env.request_id is None
        assert env.payload == {}

    def test_parse_full(self):
        raw = '{"type": "action", "request_id": "req_1", "payload": {"actor_id": "fighter_1"}}'
        env = WsEnvelope.model_validate_json(raw)
        assert env.type == "action"
        assert env.request_id == "req_1"
        assert env.payload["actor_id"] == "fighter_1"


class TestWsOutbound:

    def test_serialization_includes_type_and_payload(self):
        out = WsOutbound(type="test", payload={"val": 42})
        data = out.model_dump(mode="json", exclude={"visibility", "target_user_id"})
        assert data["type"] == "test"
        assert data["payload"]["val"] == 42
        assert "visibility" not in data

    def test_default_visibility_is_all(self):
        out = WsOutbound(type="test", payload={})
        assert out.visibility == Visibility.ALL


class TestEnums:

    def test_visibility_values(self):
        assert Visibility.ALL == "all"
        assert Visibility.DM_ONLY == "dm_only"

    def test_error_code_values(self):
        assert WsErrorCode.UNAUTHORIZED == "unauthorized"
        assert WsErrorCode.INTERNAL_ERROR == "internal_error"
