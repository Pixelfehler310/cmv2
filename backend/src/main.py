from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import items, spells, monsters, campaigns, characters, definitions

app = FastAPI(
    title="Open RPG Engine API",
    description="Backend for the Open RPG Engine VTT",
    version="0.1.0"
)

# CORS Configuration
origins = [
    "http://localhost:3000",  # React Host
    "http://localhost:5173",  # Vite Default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router)
app.include_router(spells.router)
app.include_router(monsters.router)
app.include_router(campaigns.router)
app.include_router(characters.router)
app.include_router(definitions.router)

@app.get("/")
async def root():
    return {"message": "Open RPG Engine Backend is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
