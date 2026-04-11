from src.systems.dnd5e.content.domain.invariants import CompendiumErrorCode
from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord
from src.systems.dnd5e.content.domain.definition_models import (
    LoreDefinition,
    SpeciesDefinition,
    BackgroundDefinition,
    ClassDefinition,
)
from src.systems.dnd5e.content.domain.primitives import (
    DefinitionFamily, LifecycleState,
    ActionOperationSpec, ActivationCost, TargetingType, OperationType,
    AttackRollPayload, HealPayload, ResultReference, ResultAttribute,
    TargetingSpec, DamageInstance
)
import pydantic
from datetime import datetime
import pytest

pytestmark = [pytest.mark.v05, pytest.mark.gold]


def test_definition_record_valid_content_version():
    """Content version must be >= 1"""
    lore = LoreDefinition(
        id="lore-1",
        slug="the-harpers",
        name="The Harpers",
        lifecycle_state=LifecycleState.DRAFT,
        content_version=1,
        schema_version=1,
        pack_id="pack-core",
        provenance_source="test",
        provenance_updated_at=datetime.utcnow(),
        lore_type="faction",
        rich_text_content="A scattered network of spellcasters and spies..."
    )
    assert lore.content_version == 1


def test_definition_record_invalid_content_version():
    """Fails validation if content_version < 1"""
    with pytest.raises(pydantic.ValidationError) as exc:
        LoreDefinition(
            id="lore-1",
            slug="the-harpers",
            name="The Harpers",
            lifecycle_state=LifecycleState.DRAFT,
            content_version=0,
            schema_version=1,
            pack_id="pack-core",
            provenance_source="test",
            provenance_updated_at=datetime.utcnow(),
            lore_type="faction",
            rich_text_content="A scattered network of spellcasters and spies..."
        )
    assert CompendiumErrorCode.VALIDATION_FAILED.value in str(exc.value)


def test_definition_record_invalid_schema_version():
    """Fails validation if schema_version < 1"""
    with pytest.raises(pydantic.ValidationError) as exc:
        LoreDefinition(
            id="lore-1",
            slug="the-harpers",
            name="The Harpers",
            lifecycle_state=LifecycleState.DRAFT,
            content_version=1,
            schema_version=0,
            pack_id="pack-core",
            provenance_source="test",
            provenance_updated_at=datetime.utcnow(),
            lore_type="faction",
            rich_text_content="A scattered network of spellcasters and spies..."
        )
    assert CompendiumErrorCode.VALIDATION_FAILED.value in str(exc.value)


def test_leaf_bundle_definitions_include_new_default_fields():
    """Leaf-bundle definitions expose required additive fields with safe defaults."""
    common_kwargs = {
        "id": "def-1",
        "slug": "def-1",
        "name": "Definition",
        "lifecycle_state": LifecycleState.DRAFT,
        "content_version": 1,
        "schema_version": 1,
        "pack_id": "pack-core",
        "provenance_source": "test",
        "provenance_updated_at": datetime.utcnow(),
    }

    species = SpeciesDefinition(
        **common_kwargs,
        family=DefinitionFamily.SPECIES,
        speed=30,
        size="medium",
    )
    assert species.languages == []

    background = BackgroundDefinition(
        **common_kwargs,
        family=DefinitionFamily.BACKGROUND,
        skill_proficiencies=["Stealth", "Sleight of Hand"],
    )
    assert background.tool_proficiencies == []
    assert background.languages == []

    class_def = ClassDefinition(
        **common_kwargs,
        family=DefinitionFamily.CLASS,
        hit_die="1d8",
        saving_throw_proficiencies=["DEX", "INT"],
    )
    assert class_def.spellcasting_ability is None
    assert class_def.armor_proficiencies == []
    assert class_def.weapon_proficiencies == []


def test_action_operation_spec_valid():
    """An action payload correctly discriminates into AttackRollPayload based on operation_type"""
    # Simulate a JSON dictionary parsed from DB/Frontend
    raw_dict = {
        "operation_id": "op-attack-001",
        "activation_cost": "action",
        "targeting_spec": {
            "type": "single",
            "range_feet": 5,
            "max_targets": 1
        },
        "payload": {
            "operation_type": "attack_roll",
            "attack_type": "melee_weapon",
            "damage_instances": [
                {
                    "value": "1d8",
                    "damage_type": "slashing",
                    "add_stat_modifier": True
                }
            ],
            "critical_threshold": 20
        }
    }
    spec = ActionOperationSpec.model_validate(raw_dict)

    assert spec.activation_cost == ActivationCost.ACTION
    assert isinstance(spec.payload, AttackRollPayload)
    assert spec.payload.attack_type == "melee_weapon"
    assert spec.payload.damage_instances[0].damage_type == "slashing"


def test_life_drain_result_piping_validation():
    """Validates that a Heal operation can reference an Attack operation's result."""

    # Example: Vampiric Touch
    # Op 1: Attack dealing damage
    attack_op = {
        "operation_id": "op-vamp-attack",
        "activation_cost": "action",
        "targeting_spec": {
            "type": "single",
            "range_feet": 5,
            "max_targets": 1
        },
        "payload": {
            "operation_type": "attack_roll",
            "attack_type": "melee_spell",
            "damage_instances": [{"value": "3d6", "damage_type": "necrotic", "add_stat_modifier": False}]
        }
    }

    # Op 2: Heal for 50% of Op 1's total damage
    heal_op = {
        "operation_id": "op-vamp-heal",
        "activation_cost": "free",
        "targeting_spec": {
            "type": "self",
            "range_feet": 0,
            "max_targets": 1
        },
        "payload": {
            "operation_type": "heal",
            "amount": {
                "source_operation_id": "op-vamp-attack",
                "attribute": "total_damage",
                "multiplier": 0.5
            },
            "add_stat_modifier": False,
            "stat_used": "none",
            "temp_hp": False
        }
    }

    op1 = ActionOperationSpec.model_validate(attack_op)
    op2 = ActionOperationSpec.model_validate(heal_op)

    assert isinstance(op2.payload, HealPayload)
    assert isinstance(op2.payload.amount, ResultReference)
    assert op2.payload.amount.source_operation_id == "op-vamp-attack"
    assert op2.payload.amount.multiplier == 0.5


def test_action_operation_spec_missing_fields():
    """Missing required payload fields should raise validation error"""
    raw_dict = {
        "operation_id": "op-error",
        "activation_cost": "action",
        "targeting_spec": {
            "type": "single",
            "range_feet": 5,
            "max_targets": 1
        },
        "payload": {
            "operation_type": "attack_roll",
            # missing attack_type and damage_instances
            "critical_threshold": 20
        }
    }
    with pytest.raises(pydantic.ValidationError):
        ActionOperationSpec.model_validate(raw_dict)


def test_content_pack_rejects_superseded_lifecycle_state():
    with pytest.raises(pydantic.ValidationError):
        ContentPackRecord(
            id="pack-invalid",
            title="Invalid Pack",
            lifecycle_state=LifecycleState.SUPERSEDED,
            is_homebrew=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
