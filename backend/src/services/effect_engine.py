from typing import Any, List, Union
from copy import deepcopy
from src.schemas.character import CharacterBase
from src.schemas.monster_instance import MonsterInstance
from src.schemas.effect import Effect

class EffectEngine:
    @staticmethod
    def apply_effects(entity: Union[CharacterBase, MonsterInstance]) -> Union[CharacterBase, MonsterInstance]:
        """
        Applies all active effects to the entity and returns a NEW modified instance (View Model).
        Does not mutate the original entity.
        """
        # Create a deep copy to avoid mutating the source
        modified_entity = deepcopy(entity)
        
        # Collect all effects
        all_effects: List[Effect] = []
        
        # 1. Innate Effects
        if hasattr(modified_entity, 'effects'):
            all_effects.extend(modified_entity.effects)
            
        # 1.1 Template Effects (for MonsterInstances)
        if hasattr(modified_entity, 'template') and modified_entity.template and hasattr(modified_entity.template, 'effects'):
            all_effects.extend(modified_entity.template.effects)
            
        # 2. Inventory Effects (Equipped Items)
        if hasattr(modified_entity, 'inventory'):
            for item in modified_entity.inventory:
                if item.equipped and item.template and hasattr(item.template, 'effects'):
                    all_effects.extend(item.template.effects)
        
        # Apply effects
        for effect in all_effects:
            EffectEngine._apply_single_effect(modified_entity, effect)
            
        return modified_entity

    @staticmethod
    def _apply_single_effect(entity: Any, effect: Effect):
        """
        Applies a single effect to the entity.
        """
        # Resolve target (handle dot notation e.g. "speed.walk")
        target_path = effect.target.split('.')
        target_obj = entity
        
        # Navigate to the parent of the target attribute
        for i, part in enumerate(target_path[:-1]):
            if hasattr(target_obj, part):
                target_obj = getattr(target_obj, part)
            elif isinstance(target_obj, dict) and part in target_obj:
                target_obj = target_obj[part]
            else:
                # Target path invalid, skip
                return

        final_attr = target_path[-1]
        
        # Get current value
        current_value = None
        if hasattr(target_obj, final_attr):
            current_value = getattr(target_obj, final_attr)
        elif isinstance(target_obj, dict) and final_attr in target_obj:
            current_value = target_obj[final_attr]
        else:
            # Attribute doesn't exist, maybe we should create it? 
            # For now, let's assume we only modify existing stats or properly defined dict keys.
            return

        # Apply modification
        new_value = current_value
        
        if effect.type == "BONUS":
            # Assume addition works (int, float)
            try:
                new_value = current_value + effect.value
            except TypeError:
                pass # Can't add to this type
                
        elif effect.type == "SET":
            new_value = effect.value
            
        # Set new value
        if hasattr(target_obj, final_attr):
            setattr(target_obj, final_attr, new_value)
        elif isinstance(target_obj, dict):
            target_obj[final_attr] = new_value
