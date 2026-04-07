from src.legacy.data.lib.monster_action_refs import normalize_monster_actions


def test_normalize_monster_actions_converts_legacy_payload_and_deduplicates() -> None:
    normalized = normalize_monster_actions(
        "Bandit",
        [
            {
                "name": "Basic Attack",
                "description": "Melee Weapon Attack. Hit: 7 (1d8 + 3) damage.",
            },
            {
                "name": "Basic Attack",
                "description": "Duplicate legacy action entry.",
            },
        ],
    )

    assert normalized == [
        {
            "action_id": "monster.bandit.basic_attack",
            "display_name": "Basic Attack",
        }
    ]


def test_normalize_monster_actions_keeps_canonical_ref_entries_idempotent() -> None:
    payload = [
        {"action_id": "monster.goblin.scimitar"},
        {"action_id": "monster.goblin.shortbow", "display_name": "Shortbow"},
    ]

    normalized_once = normalize_monster_actions("Goblin", payload)
    normalized_twice = normalize_monster_actions("Goblin", normalized_once)

    assert normalized_once == payload
    assert normalized_twice == payload


def test_normalize_monster_actions_migrates_non_prefixed_action_id_then_becomes_idempotent() -> None:
    legacy_like_payload = [
        {"action_id": "Scimitar", "display_name": "Scimitar"}]

    normalized_once = normalize_monster_actions("Goblin", legacy_like_payload)
    normalized_twice = normalize_monster_actions("Goblin", normalized_once)

    assert normalized_once == [
        {
            "action_id": "monster.goblin.scimitar",
            "display_name": "Scimitar",
        }
    ]
    assert normalized_twice == normalized_once
