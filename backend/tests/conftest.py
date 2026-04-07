import os
from pathlib import Path

import pytest
from httpx import AsyncClient
from src.main import app


# Legacy suite is intentionally excluded from default runs.
# Set RUN_LEGACY_TESTS=1 to include these tests.
LEGACY_PATH_SUBSTRINGS = (
    "tests/campaigns/",
)

LEGACY_FILE_NAMES = {
    "test_logic_routers.py",
    "test_definitions.py",
    "test_dev.py",
    "test_fixtures.py",
    "test_monster_fixture_action_refs.py",
    "test_routers.py",
}


def _is_legacy_path(test_path: str) -> bool:
    normalized = test_path.replace("\\", "/")
    path_obj = Path(normalized)
    if path_obj.name in LEGACY_FILE_NAMES:
        return True
    return any(fragment in normalized for fragment in LEGACY_PATH_SUBSTRINGS)


def pytest_collection_modifyitems(config, items):
    run_legacy = os.getenv("RUN_LEGACY_TESTS", "").strip().lower() in {"1", "true", "yes"}
    if run_legacy:
        return

    skip_legacy = pytest.mark.skip(reason="Legacy/outdated test; set RUN_LEGACY_TESTS=1 to include")
    for item in items:
        if item.get_closest_marker("legacy") or _is_legacy_path(str(item.fspath)):
            item.add_marker(skip_legacy)

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def client():
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
