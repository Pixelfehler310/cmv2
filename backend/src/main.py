from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .data.routers import items, spells, monsters, definitions
from .campaigns.routers import campaigns, characters
from .identity.router import router as identity_router
from .database import engine, Base

app = FastAPI(
    title="Open RPG Engine API",
    description="Backend for the Open RPG Engine VTT",
    version="0.1.0"
)

from starlette.middleware.sessions import SessionMiddleware
from src.config import settings

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:3020",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3020",
]

# Add origins from environment if present
if hasattr(settings, "CORS_ORIGINS") and settings.CORS_ORIGINS:
    if isinstance(settings.CORS_ORIGINS, str):
        origins.extend([o.strip() for o in settings.CORS_ORIGINS.split(",")])
    else:
        origins.extend(settings.CORS_ORIGINS)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(items.router)
app.include_router(spells.router)
app.include_router(monsters.router)
app.include_router(definitions.router)
app.include_router(campaigns.router)
app.include_router(characters.router)
app.include_router(identity_router)


@app.get("/")
async def root():
    return {"message": "Open RPG Engine Backend is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
