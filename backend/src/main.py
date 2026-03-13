from src.config import settings
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .data.routers import items, spells, monsters, definitions
from .campaigns.routers import campaigns, characters
from .campaigns.router import router as campaigns_ws_router
from .identity.router import router as identity_router
from .core.ws_dispatcher import router as ws_dispatcher_router, register_system_handler
from .systems.dnd5e.ws_handler import Dnd5eWsHandler
from .database import engine, Base
import logging
from pathlib import Path

app = FastAPI(
    title="Open RPG Engine API",
    description="Backend for the Open RPG Engine VTT",
    version="0.1.0"
)


logger = logging.getLogger("main")

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
    # Register game system handlers
    register_system_handler("dnd5e", Dnd5eWsHandler())
    logger.info(
        "Backend startup: cwd=%s, LOAD_MOCK_DATA=%s",
        Path.cwd(),
        settings.LOAD_MOCK_DATA,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.LOAD_MOCK_DATA:
        from src.database import AsyncSessionLocal
        from src.data.lib.loader import DataLoader

        logger.info("LOAD_MOCK_DATA=true. Loading mock data from fixtures.")
        fixtures_dir = Path(__file__).parent.parent / "data" / "fixtures"
        loader = DataLoader(str(fixtures_dir))

        async with AsyncSessionLocal() as session:
            db_summary = await loader.load_all(session)
            logger.info("Startup fixture load summary: %s", db_summary)
    else:
        logger.info(
            "LOAD_MOCK_DATA is false. Skipping startup fixture import and dev router registration.")

app.include_router(items.router)
app.include_router(spells.router)
app.include_router(monsters.router)
app.include_router(definitions.router)
app.include_router(campaigns.router)
app.include_router(campaigns_ws_router)
app.include_router(characters.router)
app.include_router(identity_router)
app.include_router(ws_dispatcher_router)

# Dev routes
if settings.LOAD_MOCK_DATA:
    from .routers.dev import router as dev_router
    app.include_router(dev_router)


@app.get("/")
async def root():
    return {"message": "Open RPG Engine Backend is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
