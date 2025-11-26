import pytest
from src.schemas.item import ItemResponse
from src.schemas.monster import MonsterResponse
from src.schemas.character import CharacterBase
from src.services.inventory import InventoryManager
from src.services.instance_factory import InstanceFactory

class TestInventoryManager:
    def test_add_item(self):
        inventory = []
        item_template = ItemResponse(
            id="item-1",
            name="Sword",
            type="Weapon",
            rarity="Common"
        )
        
        instance = InventoryManager.add_item(inventory, item_template)
        
        assert len(inventory) == 1
        assert inventory[0].item_id == "item-1"
        assert inventory[0].quantity == 1
        assert inventory[0].template == item_template

    def test_remove_item(self):
        inventory = []
        item_template = ItemResponse(id="item-1", name="Sword", type="Weapon", rarity="Common")
        instance = InventoryManager.add_item(inventory, item_template, quantity=5)
        
        # Remove partial
        success = InventoryManager.remove_item(inventory, instance.id, quantity=2)
        assert success
        assert inventory[0].quantity == 3
        
        # Remove rest
        success = InventoryManager.remove_item(inventory, instance.id, quantity=3)
        assert success
        assert len(inventory) == 0

    def test_equip_logic(self):
        inventory = []
        armor1 = ItemResponse(id="armor-1", name="Leather", type="Armor", rarity="Common")
        armor2 = ItemResponse(id="armor-2", name="Plate", type="Armor", rarity="Common")
        
        inst1 = InventoryManager.add_item(inventory, armor1)
        inst2 = InventoryManager.add_item(inventory, armor2)
        
        # Equip first armor
        InventoryManager.equip_item(inventory, inst1.id)
        assert inst1.equipped
        assert not inst2.equipped
        
        # Equip second armor (should unequip first)
        InventoryManager.equip_item(inventory, inst2.id)
        assert not inst1.equipped
        assert inst2.equipped

    def test_monster_instance_inventory(self):
        # Create a monster instance
        template = MonsterResponse(
            id="orc-1", name="Orc", size="Medium", type="Humanoid", alignment="CE",
            armor_class=13, hit_points=15, hit_dice="2d8+6", speed={"walk": 30},
            strength=16, dexterity=12, constitution=16, intelligence=7, wisdom=11, charisma=10,
            languages="Common, Orc", challenge_rating=0.5, xp=100
        )
        monster = InstanceFactory.create_monster_instance(template)
        
        # Add item to monster's inventory
        axe = ItemResponse(id="axe-1", name="Greataxe", type="Weapon", rarity="Common")
        InventoryManager.add_item(monster.inventory, axe)
        
        assert len(monster.inventory) == 1
        assert monster.inventory[0].template.name == "Greataxe"
        
        # Equip it
        InventoryManager.equip_item(monster.inventory, monster.inventory[0].id)
        assert monster.inventory[0].equipped

    def test_character_inventory(self):
        # Create a character (using Schema, not DB model for unit test)
        character = CharacterBase(
            name="Hero",
            species_id="s1",
            class_id="c1",
            max_hp=10,
            current_hp=10,
            hit_dice="1d10"
        )
        
        # Add item to character's inventory
        potion = ItemResponse(id="pot-1", name="Potion of Healing", type="Consumable", rarity="Common")
        InventoryManager.add_item(character.inventory, potion, quantity=3)
        
        assert len(character.inventory) == 1
        assert character.inventory[0].quantity == 3
        
        # Remove one
        InventoryManager.remove_item(character.inventory, character.inventory[0].id, quantity=1)
        assert character.inventory[0].quantity == 2

class TestInstanceFactory:
    def test_create_monster_instance_static_hp(self):
        template = MonsterResponse(
            id="goblin-1",
            name="Goblin",
            size="Small",
            type="Humanoid",
            alignment="NE",
            armor_class=15,
            hit_points=7,
            hit_dice="", # No dice, use static
            speed={"walk": 30},
            strength=8, dexterity=14, constitution=10, intelligence=10, wisdom=8, charisma=8,
            languages="Goblin",
            challenge_rating=0.25,
            xp=50
        )
        
        instance = InstanceFactory.create_monster_instance(template)
        assert instance.monster_id == "goblin-1"
        assert instance.current_hp == 7
        assert instance.max_hp == 7

    def test_create_monster_instance_rolled_hp(self):
        # Mocking dice roll would be ideal, but for integration we check range
        template = MonsterResponse(
            id="goblin-1",
            name="Goblin",
            size="Small",
            type="Humanoid",
            alignment="NE",
            armor_class=15,
            hit_points=7,
            hit_dice="2d6", # Range 2-12
            speed={"walk": 30},
            strength=8, dexterity=14, constitution=10, intelligence=10, wisdom=8, charisma=8,
            languages="Goblin",
            challenge_rating=0.25,
            xp=50
        )
        
        instance = InstanceFactory.create_monster_instance(template)
        assert 2 <= instance.max_hp <= 12
        assert instance.current_hp == instance.max_hp
