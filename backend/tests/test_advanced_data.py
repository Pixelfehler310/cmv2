import pytest
from src.models.monster import Monster
from src.models.character import Character
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
            if item.get("type") == "Weapon":
                actions.append({
                    "name": f"Attack with {item['name']}",
                    "type": "Melee Weapon Attack",
                    "damage": item.get("properties", {}).get("damage", "1d4") # Simplified
                })
                
    # Implicit Actions from Spells
    if hasattr(entity, 'spells') and entity.spells:
        for spell in entity.spells:
            actions.append({
                "name": f"Cast {spell['name']}",
                "type": "Spell",
                "level": spell.get("level", 0)
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
            {"name": "Scimitar", "desc": "Melee Weapon Attack: +4 to hit...", "damage": "1d6+2"}
        ]
    }
    monster = MonsterCreate(**monster_data)
    assert len(monster.actions) == 1
    assert monster.actions[0]["name"] == "Scimitar"
    
    resolved = resolve_actions(monster)
    assert len(resolved) == 1
    assert resolved[0]["name"] == "Scimitar"

def test_character_with_explicit_actions():
    character_data = {
        "name": "Fighter",
        "race": "Human",
        "class_name": "Fighter",
        "max_hp": 10,
        "current_hp": 10,
        "hit_dice": "1d10",
        "actions": [
            {"name": "Second Wind", "desc": "Regain 1d10+1 HP"}
        ]
    }
    character = CharacterCreate(**character_data)
    assert len(character.actions) == 1
    assert character.actions[0]["name"] == "Second Wind"
    
    resolved = resolve_actions(character)
    assert len(resolved) == 1
    assert resolved[0]["name"] == "Second Wind"

def test_monster_with_inventory_implicit_actions():
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
    character_data = {
        "name": "Wizard",
        "race": "Elf",
        "class_name": "Wizard",
        "max_hp": 6,
        "current_hp": 6,
        "hit_dice": "1d6",
        "inventory": [
            {"name": "Dagger", "type": "Weapon", "properties": {"damage": "1d4"}}
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
