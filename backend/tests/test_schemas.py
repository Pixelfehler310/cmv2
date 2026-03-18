from src.schemas.item import ItemCreate
from src.schemas.spell import SpellCreate
from src.schemas.monster import MonsterCreate, MonsterResponse


def _valid_monster_payload(**overrides):
    payload = {
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
        "effects": [],
    }
    payload.update(overrides)
    return payload


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
    monster_data = _valid_monster_payload()
    monster = MonsterCreate(**monster_data)
    assert monster.name == "Goblin"
    assert monster.challenge_rating == 0.25


def test_monster_schema_actions_reference_validation_accepts_canonical_action_refs():
    monster = MonsterCreate(
        **_valid_monster_payload(
            actions=[
                {"action_id": "monster.goblin.scimitar"},
                {"action_id": "monster.goblin.shortbow", "display_name": "Shortbow"},
            ]
        )
    )
    assert [action.action_id for action in monster.actions] == [
        "monster.goblin.scimitar",
        "monster.goblin.shortbow",
    ]


def test_monster_schema_actions_reference_validation_rejects_empty_action_id():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        MonsterCreate(**_valid_monster_payload(actions=[{"action_id": "   "}]))


def test_monster_schema_actions_reference_validation_rejects_non_canonical_action_id():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(
        ValidationError,
        match="canonical monster action reference",
    ):
        MonsterCreate(
            **_valid_monster_payload(actions=[{"action_id": "scimitar"}]))


def test_monster_schema_actions_reference_validation_rejects_duplicate_action_id():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        MonsterCreate(
            **_valid_monster_payload(
                actions=[
                    {"action_id": "monster.goblin.scimitar"},
                    {"action_id": "monster.goblin.scimitar"},
                ]
            )
        )


def test_monster_schema_actions_reference_validation_rejects_legacy_mechanics_fields():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        MonsterCreate(
            **_valid_monster_payload(
                actions=[
                    {
                        "action_id": "monster.goblin.scimitar",
                        "description": "Melee Weapon Attack: +4 to hit...",
                    }
                ]
            )
        )


def test_monster_schema_actions_reference_serialization_for_create_and_response():
    payload = _valid_monster_payload(
        actions=[
            {
                "action_id": "monster.goblin.scimitar",
                "display_name": "Scimitar",
            }
        ]
    )

    monster_create = MonsterCreate(**payload)
    create_dump = monster_create.model_dump(mode="json")
    assert create_dump["actions"] == [
        {"action_id": "monster.goblin.scimitar", "display_name": "Scimitar"}
    ]

    monster_response = MonsterResponse(**payload)
    response_dump = monster_response.model_dump(mode="json")
    assert response_dump["id"] == "789"
    assert response_dump["actions"] == [
        {"action_id": "monster.goblin.scimitar", "display_name": "Scimitar"}
    ]


def test_item_schema_invalid():
    from pydantic import ValidationError
    import pytest

    # Missing required field 'name'
    with pytest.raises(ValidationError):
        ItemCreate(type="Weapon", rarity="Common")


def test_spell_schema_invalid():
    from pydantic import ValidationError
    import pytest

    # Invalid level (should be int) - Pydantic might coerce string "3" to int 3, so use something definitely invalid
    with pytest.raises(ValidationError):
        SpellCreate(name="Fail", description="Desc", level="not_a_number",
                    school="Evo", casting_time="1A", range="30ft", duration="Inst")


def test_monster_schema_invalid():
    from pydantic import ValidationError
    import pytest

    # Missing required field 'size'
    with pytest.raises(ValidationError):
        MonsterCreate(name="Fail", description="Desc", type="Beast", alignment="U", armor_class=10, hit_points=10, hit_dice="1d10", speed={
        }, strength=10, dexterity=10, constitution=10, intelligence=10, wisdom=10, charisma=10, languages="Common", challenge_rating=1.0, xp=100)
