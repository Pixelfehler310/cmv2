import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.sessions.models import SessionContext, UserRole
from src.database import Base
from src.systems.dnd5e.schemas.common import AbilityScores, Position, SpeedBlock
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.schemas.enums import ActorType
from src.systems.dnd5e.schemas.instances import ActorInstance
from src.systems.dnd5e.services.combat_service import CombatService


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def combat_encounter_state() -> EncounterState:
    return EncounterState(
        id="enc_test",
        campaign_id="camp_test",
        round_number=1,
        turn_phase="active",
        active_index=0,
        combatants=[
            ActorInstance(
                id="pc_1",
                owner_user_id="player_1",
                name="Hero",
                actor_type=ActorType.PLAYER_CHARACTER,
                current_hp=20,
                max_hp=20,
                abilities=AbilityScores(dexterity=14),
                speed=SpeedBlock(walk=6),
                position=Position(x=1, y=1),
            ),
            ActorInstance(
                id="goblin_1",
                owner_user_id=None,
                name="Goblin",
                actor_type=ActorType.MONSTER,
                current_hp=7,
                max_hp=7,
                abilities=AbilityScores(dexterity=14),
                speed=SpeedBlock(walk=6),
                position=Position(x=3, y=1),
            ),
        ],
    )


@pytest.mark.anyio
async def test_check_can_act_denies_non_owner_player(db_session: AsyncSession, combat_encounter_state: EncounterState):
    service = CombatService(db_session)
    encounter_session, _ = await service.load_or_create_encounter_state(combat_encounter_state.campaign_id)
    await service.save_full_state(encounter_session, combat_encounter_state)

    ctx = SessionContext(
        campaign_id="camp_test",
        user_id="player_2",
        role=UserRole.PLAYER,
        game_system="dnd5e",
    )

    result = await service.check_can_act(
        encounter_session,
        combat_encounter_state,
        actor_id="pc_1",
        action_type="action",
        ctx=ctx,
    )

    assert result.allowed is False
    assert result.reason_code == "unauthorized"


@pytest.mark.anyio
async def test_check_can_act_denies_not_active_turn(db_session: AsyncSession, combat_encounter_state: EncounterState):
    service = CombatService(db_session)
    encounter_session, _ = await service.load_or_create_encounter_state(combat_encounter_state.campaign_id)
    await service.save_full_state(encounter_session, combat_encounter_state)

    ctx = SessionContext(
        campaign_id="camp_test",
        user_id="player_1",
        role=UserRole.PLAYER,
        game_system="dnd5e",
    )

    result = await service.check_can_act(
        encounter_session,
        combat_encounter_state,
        actor_id="goblin_1",
        action_type="action",
        ctx=ctx,
    )

    assert result.allowed is False
    assert result.reason_code == "not_your_turn"


@pytest.mark.anyio
async def test_apply_movement_denies_when_exceeds_budget(db_session: AsyncSession, combat_encounter_state: EncounterState):
    service = CombatService(db_session)
    encounter_session, _ = await service.load_or_create_encounter_state(combat_encounter_state.campaign_id)
    await service.save_full_state(encounter_session, combat_encounter_state)

    ctx = SessionContext(
        campaign_id="camp_test",
        user_id="player_1",
        role=UserRole.PLAYER,
        game_system="dnd5e",
    )

    # Path distance 8 from (1,1) -> (5,1) -> (5,5), but speed budget is 6.
    result = await service.apply_movement(
        encounter_session,
        combat_encounter_state,
        ctx,
        actor_id="pc_1",
        path=[{"x": 5, "y": 1}, {"x": 5, "y": 5}],
    )

    assert result.allowed is False
    assert result.reason_code == "resource_exhausted"
