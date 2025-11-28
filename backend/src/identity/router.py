from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.config import settings
from src.identity.lib.auth import verify_password, create_access_token
from src.identity.lib.users import get_user_by_username, create_user
from src.identity.schemas import UserCreate, UserResponse, Token
from src.identity.dependencies import get_current_active_user
from src.identity.models import User, UserSocialAuth
from src.identity.lib.oauth import oauth

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400, detail="Username already registered")
    return await create_user(db=db, user=user)


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/{provider}/authorize")
async def authorize(provider: str, request: Request):
    if provider not in ['google', 'discord']:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    redirect_uri = request.url_for('auth_callback', provider=provider)
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback", name="auth_callback")
async def auth_callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    if provider not in ['google', 'discord']:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    try:
        token = await oauth.create_client(provider).authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    user_info = token.get('userinfo')
    if not user_info:
        # Fallback for providers that don't return userinfo in token (like Discord sometimes needs separate call)
        client = oauth.create_client(provider)
        if provider == 'discord':
            resp = await client.get('users/@me', token=token)
            user_info = resp.json()
        elif provider == 'google':
             user_info = await client.userinfo(token=token)

    if not user_info:
         raise HTTPException(status_code=400, detail="Could not fetch user info")

    # Extract common fields
    provider_user_id = str(user_info.get('sub') or user_info.get('id'))
    email = user_info.get('email')
    username = user_info.get('name') or user_info.get('username') or email.split('@')[0]

    # Check if social auth exists
    stmt = select(UserSocialAuth).where(
        UserSocialAuth.provider == provider,
        UserSocialAuth.provider_user_id == provider_user_id
    )
    result = await db.execute(stmt)
    social_auth = result.scalar_one_or_none()

    if social_auth:
        user = await db.get(User, social_auth.user_id)
    else:
        # Check if user with email exists (link account)
        if email:
            stmt = select(User).where(User.username == email) # Using email as username for now or check if we have email field on User?
            # Wait, User model only has username. Let's assume username is unique.
            # If we want to link by email, we need email on User.
            # For now, let's just check username.
            # Actually, let's create a new user if not found.
            pass
        
        # Create new user
        # Handle username collision
        base_username = username
        counter = 1
        while True:
            stmt = select(User).where(User.username == username)
            if not (await db.execute(stmt)).scalar_one_or_none():
                break
            username = f"{base_username}{counter}"
            counter += 1
            
        user = User(username=username, hashed_password=None)
        db.add(user)
        await db.flush() # Get ID
        
        social_auth = UserSocialAuth(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            extra_data=user_info
        )
        db.add(social_auth)
        await db.commit()
        await db.refresh(user)

    # Create JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Redirect to frontend
    frontend_url = "http://localhost:3000/login" # Or from config
    return RedirectResponse(url=f"{frontend_url}?token={access_token}")
