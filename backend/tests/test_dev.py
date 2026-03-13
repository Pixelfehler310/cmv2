import pytest
from fastapi.testclient import TestClient
from src.main import app


def test_load_seeds():
    client = TestClient(app)
    response = client.post("/api/dev/load-seeds")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in {"success", "partial_success", "failed"}

    summary = data["summary"]
    assert "db_seeds_loaded" in summary
    assert "db_import_summary" in summary
    assert "encounters_total" in summary
    assert "encounters_loaded" in summary
    assert "encounters_failed" in summary

    assert summary["encounters_total"] >= 2
    assert summary["encounters_loaded"] >= 2
    assert summary["encounters_failed"] == 0

    loaded_files = data["encounters_loaded_files"]
    assert "01_basic_combat.json" in loaded_files
    assert "02_large_map_test.json" in loaded_files
    assert isinstance(data["errors"], dict)
