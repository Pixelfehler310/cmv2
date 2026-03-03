from typing import List, Optional

class Combatant:
    def __init__(self, id: str, initiative: int = 0):
        self.id = id
        self.initiative = initiative
        self.action_used = False
        self.bonus_action_used = False
        self.reaction_used = False
        self.movement_remaining = 0.0
        
        # Phase 4 additions
        self.is_concentrating = False
        self.concentrating_on_effect_id: Optional[str] = None

    def start_of_turn(self):
        """Resets action economy at the start of a turn."""
        self.action_used = False
        self.bonus_action_used = False
        self.movement_remaining = 30.0 # Default speed for now, to be expanded

class Encounter:
    def __init__(self):
        self.combatants: List[Combatant] = []
        self.active_combatant_index: int = 0
        self.round_number: int = 0
        self.turn_phase: str = "pre_combat"

    def add_combatant(self, combatant: Combatant):
        """Adds a combatant and immediately re-sorts initiative descending."""
        self.combatants.append(combatant)
        self.combatants.sort(key=lambda x: x.initiative, reverse=True)

    def start_combat(self):
        """Initializes the first round of combat."""
        if not self.combatants:
            return
            
        self.round_number = 1
        self.active_combatant_index = 0
        self._trigger_start_of_turn()
        
    def get_active_combatant(self) -> Optional[Combatant]:
        """Returns the combatant whose turn it currently is."""
        if not self.combatants or self.round_number == 0:
            return None
        return self.combatants[self.active_combatant_index]

    def next_turn(self):
        """Advances initiative to the next combatant."""
        if not self.combatants:
            return
            
        self._trigger_end_of_turn()
        
        self.active_combatant_index += 1
        
        # Wrap around to the next round
        if self.active_combatant_index >= len(self.combatants):
            self.active_combatant_index = 0
            self.round_number += 1
            
        self._trigger_start_of_turn()

    def _trigger_start_of_turn(self):
        """Internal hook for resolving start-of-turn mechanics."""
        self.turn_phase = "start_of_turn"
        active = self.get_active_combatant()
        if active:
            active.start_of_turn()
        self.turn_phase = "main_phase"

    def _trigger_end_of_turn(self):
        """Internal hook for resolving end-of-turn mechanics."""
        self.turn_phase = "end_of_turn"
