from src.schemas.item import ItemCreate
from src.schemas.spell import SpellCreate
from src.schemas.monster import MonsterCreate

def test_item_schema_validation():
    item_data = {
        "id": "123",
        "name": "Sword",
        "description": "A sharp blade",
        "type": "Weapon",
        "rarity": "Common",
        "weight": 2.0,
        "price": 100,
        "properties": {"damage": "1d8"},
        "effects": []
    }
    item = ItemCreate(**item_data)
    assert item.name == "Sword"
    assert item.properties["damage"] == "1d8"

def test_spell_schema_validation():
    spell_data = {
        "id": "456",
        "name": "Fireball",
        "description": "Boom",
        "level": 3,
        "school": "Evocation",
        "casting_time": "1 Action",
        "range": "150 feet",
        "components": {"V": True, "S": True, "M": "bat guano"},
        "duration": "Instantaneous",
        "effects": []
    }
    spell = SpellCreate(**spell_data)
    assert spell.level == 3
    assert spell.components["M"] == "bat guano"

def test_monster_schema_validation():
    monster_data = {
        "id": "789",
        "name": "Goblin",
        "description": "Small and green",
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
        "languages": "Common, Goblin",
        "challenge_rating": 0.25,
        "xp": 50,
        "effects": []
    }
    monster = MonsterCreate(**monster_data)
    assert monster.name == "Goblin"
    assert monster.challenge_rating == 0.25
