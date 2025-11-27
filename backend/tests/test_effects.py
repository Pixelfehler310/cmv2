import pytest
from src.schemas.character import CharacterBase
from src.schemas.monster_instance import MonsterInstance
from src.schemas.monster import MonsterResponse
from src.schemas.item import ItemResponse
from src.schemas.item_instance import ItemInstance
from src.schemas.effect import Effect
from src.engine.lib.effect_engine import EffectEngine
from src.campaigns.lib.inventory import InventoryManager
from src.campaigns.lib.instance_factory import InstanceFactory

class TestEffectEngine:
    def test_simple_bonus_effect(self):
        # Create character with 10 AC
        char = CharacterBase(
            name="Test", species_id="s1", class_id="c1",
            max_hp=10, current_hp=10, hit_dice="1d10", armor_class=10
        )
        
        # Add +1 AC effect
        effect = Effect(name="Blessing", type="BONUS", target="armor_class", value=1)
        char.effects.append(effect)
        
        # Apply effects
        view_model = EffectEngine.apply_effects(char)
        
        assert view_model.armor_class == 11
        assert char.armor_class == 10 # Original should be unchanged

    def test_set_effect(self):
        char = CharacterBase(
            name="Test", species_id="s1", class_id="c1",
            max_hp=10, current_hp=10, hit_dice="1d10", strength=10
        )
        
        # Set Strength to 19 (Gauntlets of Ogre Power)
        effect = Effect(name="Ogre Power", type="SET", target="strength", value=19)
        char.effects.append(effect)
        
        view_model = EffectEngine.apply_effects(char)
        
        assert view_model.strength == 19

    def test_nested_attribute_effect(self):
        # Monster with speed.walk = 30
        template = MonsterResponse(
            id="m1", name="M", size="M", type="M", alignment="N",
            armor_class=10, hit_points=10, hit_dice="", 
            speed={"walk": 30},
            strength=10, dexterity=10, constitution=10, intelligence=10, wisdom=10, charisma=10,
            languages="", challenge_rating=1, xp=100
        )
        monster = InstanceFactory.create_monster_instance(template)
        
        # Add +10 speed effect
        effect = Effect(name="Haste", type="BONUS", target="speed.walk", value=10)
        monster.template.effects.append(effect) # Add to template effects (innate)
        
        view_model = EffectEngine.apply_effects(monster)
        
        # Check nested attribute
        # Note: MonsterInstance speed is derived from template, but EffectEngine applies to the view model copy
        # We need to ensure EffectEngine handles nested dicts correctly.
        # MonsterResponse.speed is a Dict[str, int].
        
        assert view_model.template.speed["walk"] == 40

    def test_inventory_effect(self):
        char = CharacterBase(
            name="Test", species_id="s1", class_id="c1",
            max_hp=10, current_hp=10, hit_dice="1d10", armor_class=10
        )
        
        # Create Shield with +2 AC effect
        shield_effect = Effect(name="Shield Bonus", type="BONUS", target="armor_class", value=2)
        shield_template = ItemResponse(
            id="shield", name="Shield", type="Armor", rarity="Common",
            effects=[shield_effect]
        )
        
        # Add to inventory
        InventoryManager.add_item(char.inventory, shield_template)
        
        # Not equipped yet
        vm1 = EffectEngine.apply_effects(char)
        assert vm1.armor_class == 10
        
        # Equip shield
        InventoryManager.equip_item(char.inventory, char.inventory[0].id)
        
        # Should have +2 AC
        vm2 = EffectEngine.apply_effects(char)
        assert vm2.armor_class == 12
