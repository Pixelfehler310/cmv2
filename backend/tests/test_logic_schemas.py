from src.schemas.campaign import CampaignCreate
from src.schemas.character import CharacterCreate

def test_campaign_schema_validation():
    campaign_data = {
        "name": "The Lost Mine",
        "description": "A starter adventure",
        "dm_id": "dm123"
    }
    campaign = CampaignCreate(**campaign_data)
    assert campaign.name == "The Lost Mine"
    assert campaign.dm_id == "dm123"

def test_character_schema_validation():
    character_data = {
        "name": "Aragorn",
        "player_name": "Viggo",
        "race": "Human",
        "class_name": "Ranger",
        "level": 5,
        "max_hp": 40,
        "current_hp": 35,
        "hit_dice": "5d10",
        "inventory": [{"name": "Sword", "equipped": True}],
        "effects": []
    }
    character = CharacterCreate(**character_data)
    assert character.name == "Aragorn"
    assert character.level == 5
    assert character.inventory[0]["name"] == "Sword"

def test_campaign_schema_invalid():
    from pydantic import ValidationError
    import pytest
    
    # Missing required field 'name'
    with pytest.raises(ValidationError):
        CampaignCreate(description="No Name")

def test_character_schema_invalid():
    from pydantic import ValidationError
    import pytest
    
    # Missing required field 'max_hp'
    with pytest.raises(ValidationError):
        CharacterCreate(name="Fail", race="Human", class_name="Fighter")
