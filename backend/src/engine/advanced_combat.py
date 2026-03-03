import math
from typing import Optional
from src.engine.combat_state import Combatant
from src.engine.effect_engine import EffectEngine

class DamageEvent:
    def __init__(self, target: Combatant, amount: float):
        self.target = target
        self.amount = amount
        self.requires_concentration_save = target.is_concentrating
        self.concentration_dc = max(10, math.floor(amount / 2))

class CombatController:
    """Orchestrates complex interactions bringing together multiple state pieces."""
    
    def __init__(self, effect_engine: EffectEngine):
        self.effect_engine = effect_engine

    def apply_damage(self, target: Combatant, amount: float) -> DamageEvent:
        """
        Applies damage and returns an event that details side-effects (like concentration DCs).
        """
        event = DamageEvent(target, amount)
        # Note: Actual HP deduction would happen here in a full implementation.
        return event
        
    def resolve_concentration_save(self, target: Combatant, passed: bool):
        """
        Resolves the result of a DM's manual save roll.
        """
        if not target.is_concentrating or not target.concentrating_on_effect_id:
            return
            
        if not passed:
            self.effect_engine.remove_effect(target.concentrating_on_effect_id)
            target.is_concentrating = False
            target.concentrating_on_effect_id = None
