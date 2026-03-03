from typing import Dict, List, Optional
from enum import Enum
from src.engine.combat_state import Combatant

class ConditionType(Enum):
    BLINDED = "Blinded"
    CHARMED = "Charmed"
    DEAFENED = "Deafened"
    FRIGHTENED = "Frightened"
    GRAPPLED = "Grappled"
    INCAPACITATED = "Incapacitated"
    INVISIBLE = "Invisible"
    PARALYZED = "Paralyzed"
    PETRIFIED = "Petrified"
    POISONED = "Poisoned"
    PRONE = "Prone"
    RESTRAINED = "Restrained"
    STUNNED = "Stunned"
    UNCONSCIOUS = "Unconscious"

class Effect:
    def __init__(
        self, 
        id: str, 
        name: str, 
        target_id: str, 
        source_id: Optional[str] = None,
        duration_rounds: Optional[int] = None,
        condition: Optional[ConditionType] = None,
        stat_modifiers: Optional[Dict[str, float]] = None
    ):
        self.id = id
        self.name = name
        self.target_id = target_id
        self.source_id = source_id
        self.duration_rounds = duration_rounds
        self.condition = condition
        self.stat_modifiers = stat_modifiers or {}

class EffectEngine:
    def __init__(self):
        # Store effects globally for the encounter
        self.active_effects: List[Effect] = []

    def apply_effect(self, effect: Effect):
        self.active_effects.append(effect)

    def remove_effect(self, effect_id: str):
        self.active_effects = [e for e in self.active_effects if e.id != effect_id]

    def has_effect(self, target_id: str, effect_name: str) -> bool:
        return any(e.name == effect_name and e.target_id == target_id for e in self.active_effects)

    def tick_durations(self, source_id: str):
        """Called at the start/end of a turn to decrement durations."""
        effects_to_remove = []
        for effect in self.active_effects:
            if effect.source_id == source_id and effect.duration_rounds is not None:
                effect.duration_rounds -= 1
                if effect.duration_rounds <= 0:
                    effects_to_remove.append(effect.id)
                    
        for eid in effects_to_remove:
            self.remove_effect(eid)

    def calculate_stats(self, combatant: Combatant) -> Dict[str, float]:
        """Dynamically computes the final stats of a combatant based on base stats + effect modifiers."""
        
        # Base stats (in a real system these would come from the Definition/Librarian)
        computed_stats = {
            "speed": 30.0,
            "ac": 10.0,
            "hp_max": 10.0
        }
        
        # 1. Apply numeric modifiers first
        for effect in self.active_effects:
            if effect.target_id == combatant.id:
                for stat, value in effect.stat_modifiers.items():
                    if stat in computed_stats:
                        computed_stats[stat] += value
                        
        # 2. Apply Condition Overrides (These trump numeric modifiers)
        for effect in self.active_effects:
            if effect.target_id == combatant.id and effect.condition:
                self._apply_condition_overrides(effect.condition, computed_stats)
                
        # Ensure stats don't go below 0 where inappropriate
        computed_stats["speed"] = max(0.0, computed_stats["speed"])
        
        return computed_stats

    def _apply_condition_overrides(self, condition: ConditionType, stats: Dict[str, float]):
        """Hardcoded D&D 5e rule overrides based on conditions."""
        
        # Speed Overrides
        if condition in [ConditionType.GRAPPLED, ConditionType.RESTRAINED, ConditionType.PARALYZED, 
                         ConditionType.PETRIFIED, ConditionType.STUNNED, ConditionType.UNCONSCIOUS]:
            stats["speed"] = 0.0
            
        # Others can be added here (Advantage/Disadvantage flags, etc)
