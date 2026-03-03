import pytest
from src.engine.combat_state import Combatant
from src.engine.effect_engine import EffectEngine, Effect, ConditionType

def test_effect_engine_initialization():
    engine = EffectEngine()
    assert len(engine.active_effects) == 0

def test_apply_simple_stat_modifier():
    engine = EffectEngine()
    hero = Combatant(id="hero")
    
    # Base speed is 30. Let's add Haste (+30 speed)
    haste_effect = Effect(
        id="haste_1", 
        name="Haste", 
        target_id="hero",
        stat_modifiers={"speed": 30}
    )
    
    engine.apply_effect(haste_effect)
    
    # Calculate stats
    stats = engine.calculate_stats(hero)
    assert stats["speed"] == 60.0

def test_standard_condition_restrained():
    engine = EffectEngine()
    hero = Combatant(id="hero")
    
    # Apply restrained
    restrain_effect = Effect(
        id="restrained_1",
        name="Restrained",
        target_id="hero",
        condition=ConditionType.RESTRAINED
    )
    
    engine.apply_effect(restrain_effect)
    stats = engine.calculate_stats(hero)
    
    # Restrained sets speed to 0, regardless of bonuses
    assert stats["speed"] == 0.0
    
    # Let's test that even with haste, speed is still 0
    haste_effect = Effect(id="haste_1", name="Haste", target_id="hero", stat_modifiers={"speed": 30})
    engine.apply_effect(haste_effect)
    
    stats_after_haste = engine.calculate_stats(hero)
    assert stats_after_haste["speed"] == 0.0

def test_effect_duration_tick():
    engine = EffectEngine()
    
    # Effect lasts 1 round
    bless_effect = Effect(
        id="bless_1",
        name="Bless",
        target_id="hero",
        source_id="cleric",
        duration_rounds=1
    )
    
    engine.apply_effect(bless_effect)
    assert engine.has_effect("hero", "Bless")
    
    # Tick for the source's turn
    engine.tick_durations(source_id="cleric")
    
    # Should be removed
    assert not engine.has_effect("hero", "Bless")
