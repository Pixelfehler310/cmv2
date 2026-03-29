import uuid
from typing import Optional
from src.schemas.monster import MonsterResponse
from src.schemas.monster_instance import MonsterInstance
from src.engine.lib.dice import DiceService

class InstanceFactory:
    @staticmethod
    def create_monster_instance(template: MonsterResponse, x: int = 0, y: int = 0) -> MonsterInstance:
        """
        Creates a new MonsterInstance from a template.
        Rolls HP based on Hit Dice.
        """
        # Roll HP
        # Hit Dice string example: "2d6" or "2d6+2"
        # We need to handle the case where hit_dice might be missing or invalid
        max_hp = template.hit_points # Default to average/static HP
        
        if template.hit_dice:
            try:
                roll_result = DiceService.roll(template.hit_dice)
                max_hp = roll_result.total
            except Exception:
                # Fallback to static HP if rolling fails
                pass
        
        return MonsterInstance(
            id=str(uuid.uuid4()),
            monster_id=template.id,
            template=template,
            current_hp=max_hp,
            max_hp=max_hp,
            x=x,
            y=y
        )
