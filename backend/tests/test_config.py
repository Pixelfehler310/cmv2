from src.config import settings

def test_config_defaults():
    assert settings.PROJECT_NAME == "Open RPG Engine"
    assert settings.POSTGRES_PORT == 5432
    assert settings.SQLALCHEMY_DATABASE_URI.path == "/rpg_db"
