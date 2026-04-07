import pytest
from src.legacy.data.lib.monster import Monster
from src.legacy.campaigns.lib.character import Character
from src.schemas.monster import MonsterCreate
from src.schemas.character import CharacterCreate

# Helper function to simulate Logic Service resolving actions
def resolve_actions(entity):
    actions = []
    
    # Explicit Actions
    if hasattr(entity, 'actions') and entity.actions:
        actions.extend(entity.actions)
        
    # Implicit Actions from Inventory (Weapons)
    if hasattr(entity, 'inventory') and entity.inventory:
        for item in entity.inventory:
            # Handle ItemInstance object or dict
            item_type = None
            item_name = None
            damage = "1d4"
            
            if isinstance(item, dict):
                item_type = item.get("type")
                item_name = item.get("name")
                damage = item.get("properties", {}).get("damage", "1d4")
            else:
                # ItemInstance object
                if item.template:
                    item_type = item.template.type
                    item_name = item.template.name
                    damage = item.template.properties.get("damage", "1d4")
            
            if item_type == "Weapon":
                actions.append({
                    "name": f"Attack with {item_name}",
                    "type": "Melee Weapon Attack",
                    "damage": damage
                })
                
    # Implicit Actions from Spells
    if hasattr(entity, 'spells') and entity.spells:
        for spell in entity.spells:
            # Handle dict (spells are still dicts in CharacterBase for now?)
            # CharacterBase has spells: List[Dict[str, Any]]
            name = spell.get("name") if isinstance(spell, dict) else spell.name
            level = spell.get("level", 0) if isinstance(spell, dict) else spell.level
            
            actions.append({
                "name": f"Cast {name}",
                "type": "Spell",
                "level": level
            })
            
    return actions

def test_monster_with_explicit_actions():
    monster_data = {
        "name": "Goblin",
        "size": "Small",
        "type": "Humanoid",
        "alignment": "Neutral Evil",
        "armor_class": 15,
        "hit_points": 7,
        "hit_dice": "2d6",
        "speed": {"walk": 30},
        "strength": 8,
        "dexterity": 14,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 8,
        "charisma": 8,
        "languages": "Goblin",
        "challenge_rating": 0.25,
        "xp": 50,
        "actions": [
            {"action_id": "monster.goblin.scimitar", "display_name": "Scimitar"}
        ]
    }
    monster = MonsterCreate(**monster_data)
    assert len(monster.actions) == 1
    assert monster.actions[0].display_name == "Scimitar"
    
    resolved = resolve_actions(monster)
    assert len(resolved) == 1
    # resolve_actions helper still uses 'name' which isn't on the object anymore, 
    # it needs to be updated to handle MonsterActionRef objects
    assert resolved[0].display_name == "Scimitar"

def test_character_with_explicit_actions():
    character_data = {
        "name": "Fighter",
        "species_id": "s1",
        "class_id": "c1",
        "max_hp": 10,
        "current_hp": 10,
        "hit_dice": "1d10",
        "actions": [
            {"name": "Second Wind", "desc": "Regain 1d10+1 HP"}
        ]
    }
    # Check CharacterCreate schema before assuming it's the same as Monster
    character = CharacterCreate(**character_data)
    assert len(character.actions) == 1
    assert character.actions[0]["name"] == "Second Wind"
    
    resolved = resolve_actions(character)
    assert len(resolved) == 1
    assert resolved[0]["name"] == "Second Wind"

def test_monster_with_inventory_implicit_actions():
    # Monster inventory is List[ItemInstance] now too?
    # MonsterBase has inventory: List[Dict] but MonsterInstance has List[ItemInstance]
    # MonsterCreate inherits from MonsterBase.
    # Let's check MonsterCreate schema.
    # It seems MonsterCreate uses MonsterBase which has List[Dict].
    # So this test might still work with dicts for Monsters.
    monster_data = {
        "name": "Orc",
        "size": "Medium",
        "type": "Humanoid",
        "alignment": "Chaotic Evil",
        "armor_class": 13,
        "hit_points": 15,
        "hit_dice": "2d8+6",
        "speed": {"walk": 30},
        "strength": 16,
        "dexterity": 12,
        "constitution": 16,
        "intelligence": 7,
        "wisdom": 11,
        "charisma": 10,
        "languages": "Common, Orc",
        "challenge_rating": 0.5,
        "xp": 100,
        "inventory": [
            {"name": "Greataxe", "type": "Weapon", "properties": {"damage": "1d12"}}
        ]
    }
    monster = MonsterCreate(**monster_data)
    assert len(monster.inventory) == 1
    
    resolved = resolve_actions(monster)
    # Should have implicit action from Greataxe
    assert len(resolved) == 1
    assert resolved[0]["name"] == "Attack with Greataxe"

def test_character_with_inventory_and_spells_implicit_actions():
    # CharacterCreate expects List[ItemInstance]
    # We need to construct valid ItemInstance data
    character_data = {
        "name": "Wizard",
        "species_id": "s1",
        "class_id": "c1",
        "max_hp": 6,
        "current_hp": 6,
        "hit_dice": "1d6",
        "inventory": [
            {
                "id": "inst1", 
                "item_id": "dagger", 
                "template": {"id": "dagger", "name": "Dagger", "type": "Weapon", "properties": {"damage": "1d4"}, "rarity": "Common", "weight": 1, "price": 2},
                "quantity": 1,
                "equipped": True
            }
        ],
        "spells": [
            {"name": "Fireball", "level": 3}
        ]
    }
    character = CharacterCreate(**character_data)
    
    resolved = resolve_actions(character)
    # Should have Dagger attack and Fireball cast
    assert len(resolved) == 2
    names = [a["name"] for a in resolved]
    assert "Attack with Dagger" in names
    assert "Cast Fireball" in names
