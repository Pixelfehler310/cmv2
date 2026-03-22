import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.database import Base
from src.campaigns.lib.campaign import Campaign
from src.campaigns.lib.character import Character
from src.systems.dnd5e.services.combat_service import CombatService
from src.systems.dnd5e.schemas.enums import ActorType


@pytest.fixture
async def db_session():
    # Use a fresh in-memory database for each test
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.anyio
async def test_load_or_create_encounter_loads_campaign_characters(db_session: AsyncSession):
    # 1. Setup Campaign and Characters in DB
    campaign = Campaign(id="camp_123", name="Test Campaign")
    char1 = Character(
        id="char_1",
        name="Aelar",
        campaign_id="camp_123",
        max_hp=20,
        current_hp=20,
        level=1,
        strength=10, dexterity=14, constitution=12, intelligence=16, wisdom=10, charisma=8,
        speed=30,
        armor_class=12,
        hit_dice="1d8"
    )
    db_session.add(campaign)
    db_session.add(char1)
    await db_session.commit()

    # 2. Call load_or_create_encounter_state
    service = CombatService(db_session)
    session, encounter = await service.load_or_create_encounter_state("camp_123")

    # 3. Assertions
    assert encounter.campaign_id == "camp_123"
    assert len(encounter.combatants) == 1
    actor = encounter.combatants[0]
    assert actor.id == "char_1"
    assert actor.name == "Aelar"
    assert actor.actor_type == ActorType.PLAYER_CHARACTER
    assert actor.max_hp == 20
    assert actor.abilities.dexterity == 14
    assert not any(a.name in {"Arannis", "Goblin"}
                   for a in encounter.combatants)


@pytest.mark.anyio
async def test_load_or_create_encounter_requires_existing_campaign(db_session: AsyncSession):
    service = CombatService(db_session)
    with pytest.raises(ValueError):
        await service.load_or_create_encounter_state("non_existent_camp")
