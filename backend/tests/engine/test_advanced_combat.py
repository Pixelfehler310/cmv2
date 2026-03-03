import pytest
from src.engine.combat_state import Combatant
from src.engine.effect_engine import EffectEngine, Effect
from src.engine.advanced_combat import CombatController

def test_concentration_trigger_on_damage():
    # Setup
    engine = EffectEngine()
    controller = CombatController(effect_engine=engine)
    
    cleric = Combatant(id="cleric")
    cleric.is_concentrating = True # We add this flag to Combatant
    cleric.concentrating_on_effect_id = "bless_aura_1"
    
    # Let's say the Cleric cast Bless
    bless = Effect(id="bless_aura_1", name="Bless", target_id="cleric", source_id="cleric")
    engine.apply_effect(bless)
    
    # 1. Take 10 damage -> DC should be 10 (Minimum)
    event1 = controller.apply_damage(target=cleric, amount=10)
    assert event1.requires_concentration_save is True
    assert event1.concentration_dc == 10
    
    # 2. Take 24 damage -> DC should be 12 (Half damage)
    event2 = controller.apply_damage(target=cleric, amount=24)
    assert event2.requires_concentration_save is True
    assert event2.concentration_dc == 12
    
def test_concentration_failure_drops_effect():
    engine = EffectEngine()
    controller = CombatController(effect_engine=engine)
    
    cleric = Combatant(id="cleric")
    cleric.is_concentrating = True
    cleric.concentrating_on_effect_id = "bless_aura_1"
    
    bless = Effect(id="bless_aura_1", name="Bless", target_id="cleric", source_id="cleric")
    engine.apply_effect(bless)
    
    assert engine.has_effect("cleric", "Bless")
    
    # DM rolls save and tells the system they failed
    controller.resolve_concentration_save(target=cleric, passed=False)
    
    # Effect should be gone, and concentrating flag lowered
    assert cleric.is_concentrating is False
    assert cleric.concentrating_on_effect_id is None
    assert not engine.has_effect("cleric", "Bless")
