import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.main import app
from src.database import get_db
from src.identity.models import User

# Mock DB Dependency
async def override_get_db():
    mock_session = AsyncMock()
    yield mock_session

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_register_user(client):
    payload = {
        "username": "testuser_register",
        "password": "testpassword123"
    }
    
    with patch("src.identity.router.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        with patch("src.identity.router.create_user", new_callable=AsyncMock) as mock_create_user:
            # Setup mocks
            mock_get_user.return_value = None # User does not exist
            mock_create_user.return_value = User(id="1", username=payload["username"], hashed_password="hashed")
            
            app.dependency_overrides[get_db] = override_get_db
            
            response = await client.post("/auth/register", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == payload["username"]
            assert "id" in data
            
            app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_register_duplicate_user(client):
    payload = {
        "username": "testuser_duplicate",
        "password": "testpassword123"
    }
    
    with patch("src.identity.router.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        # Setup mocks
        mock_get_user.return_value = User(id="1", username=payload["username"]) # User exists
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await client.post("/auth/register", json=payload)
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Username already registered"
        
        app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_login_user(client):
    login_payload = {
        "username": "testuser_login",
        "password": "testpassword123"
    }
    
    with patch("src.identity.router.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        with patch("src.identity.router.verify_password") as mock_verify:
            with patch("src.identity.router.create_access_token") as mock_create_token:
                # Setup mocks
                mock_get_user.return_value = User(id="1", username=login_payload["username"], hashed_password="hashed")
                mock_verify.return_value = True
                mock_create_token.return_value = "fake_token"
                
                app.dependency_overrides[get_db] = override_get_db
                
                response = await client.post("/auth/login", data=login_payload)
                
                assert response.status_code == 200
                data = response.json()
                assert data["access_token"] == "fake_token"
                assert data["token_type"] == "bearer"
                
                app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    login_payload = {
        "username": "nonexistent_user",
        "password": "wrongpassword"
    }
    
    with patch("src.identity.router.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        # Setup mocks
        mock_get_user.return_value = None # User not found
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await client.post("/auth/login", data=login_payload)
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"
        
        app.dependency_overrides = {}
