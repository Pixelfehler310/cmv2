import pytest
from src.engine.combat_state import Combatant, Encounter

def test_combatant_initialization():
    hero = Combatant(id="hero", initiative=15)
    assert hero.id == "hero"
    assert hero.initiative == 15
    assert hero.action_used is False
    assert hero.bonus_action_used is False
    assert hero.reaction_used is False
    assert hero.movement_remaining == 0.0

def test_encounter_initialization_and_sorting():
    c1 = Combatant(id="hero", initiative=10)
    c2 = Combatant(id="monster", initiative=20)
    c3 = Combatant(id="sidekick", initiative=15)
    
    encounter = Encounter()
    encounter.add_combatant(c1)
    encounter.add_combatant(c2)
    encounter.add_combatant(c3)
    
    assert len(encounter.combatants) == 3
    # Initiative 20 should be first, then 15, then 10
    assert encounter.combatants[0].id == "monster"
    assert encounter.combatants[1].id == "sidekick"
    assert encounter.combatants[2].id == "hero"

def test_start_combat():
    c1 = Combatant(id="hero", initiative=10)
    c2 = Combatant(id="monster", initiative=20)
    
    encounter = Encounter()
    encounter.add_combatant(c1)
    encounter.add_combatant(c2)
    
    encounter.start_combat()
    
    assert encounter.active_combatant_index == 0
    assert encounter.get_active_combatant().id == "monster"
    assert encounter.turn_phase == "main_phase"

def test_next_turn_loop():
    c1 = Combatant(id="hero", initiative=10)
    c2 = Combatant(id="monster", initiative=20)
    
    encounter = Encounter()
    encounter.add_combatant(c1)
    encounter.add_combatant(c2)
    
    encounter.start_combat()
    assert encounter.get_active_combatant().id == "monster"
    assert encounter.round_number == 1
    
    encounter.next_turn()
    assert encounter.get_active_combatant().id == "hero"
    assert encounter.round_number == 1
    
    encounter.next_turn()
    assert encounter.get_active_combatant().id == "monster"
    assert encounter.round_number == 2

def test_action_economy_reset_at_start_of_turn():
    hero = Combatant(id="hero", initiative=10)
    
    encounter = Encounter()
    encounter.add_combatant(hero)
    encounter.start_combat()
    
    # Simulate heroic action usage
    active = encounter.get_active_combatant()
    active.action_used = True
    active.bonus_action_used = True
    
    assert active.action_used is True
    
    # Loop back to hero's turn
    encounter.next_turn() # Round 2 Start
    
    active_again = encounter.get_active_combatant()
    assert active_again.action_used is False # Should be reset
    assert active_again.bonus_action_used is False # Should be reset
