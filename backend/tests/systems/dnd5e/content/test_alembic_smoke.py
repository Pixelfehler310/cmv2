from pathlib import Path


def test_alembic_scaffolding_exists():
    backend_dir = Path(__file__).resolve().parents[4]

    assert (backend_dir / "alembic.ini").exists()
    assert (backend_dir / "alembic" / "env.py").exists()
    assert (backend_dir / "alembic" / "versions").exists()
