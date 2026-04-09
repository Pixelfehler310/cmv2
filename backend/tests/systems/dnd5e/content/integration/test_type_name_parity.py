"""
V05-07 Cross-Diagram Type Name Parity Tests.

Verifies that the Python implementation exactly matches the type names
and structures defined in V05_business_and_content_entities_class_diagram.mmd.

These are structural assertions — they protect against accidental renames
or missing classes that would break the architecture contract.
"""

from __future__ import annotations

import inspect

import pytest


# =========================================================================
# Test 10: DefinitionFamily Enum Matches Diagram
# =========================================================================
def test_definition_family_enum_matches_diagram():
    """
    V05_business_and_content_entities_class_diagram defines these families:
    class, species, background, ability, spell, item, monster, lore, condition,
    action, faction, region, place.
    """
    from src.systems.dnd5e.content.domain.primitives import DefinitionFamily

    expected_families = {
        "class", "species", "background", "ability",
        "spell", "item", "monster", "lore", "condition",
        "action", "faction", "region", "place",
    }
    actual_families = {member.value for member in DefinitionFamily}

    assert expected_families == actual_families, (
        f"DefinitionFamily drift detected.\n"
        f"  Expected: {sorted(expected_families)}\n"
        f"  Actual:   {sorted(actual_families)}\n"
        f"  Missing:  {sorted(expected_families - actual_families)}\n"
        f"  Extra:    {sorted(actual_families - expected_families)}"
    )


# =========================================================================
# Test 11: All Definition Subclasses Exist
# =========================================================================
def test_all_definition_subclasses_exist():
    """
    The class diagram requires these concrete definition types.
    All must be importable from the definition_models module.
    """
    from src.systems.dnd5e.content.domain import definition_models

    expected_classes = [
        "DefinitionRecord",
        "ClassDefinition",
        "SpeciesDefinition",
        "BackgroundDefinition",
        "AbilityDefinition",
        "SpellDefinition",
        "ItemDefinition",
        "MonsterDefinition",
        "LoreDefinition",
        "ConditionDefinition",
        "ActionDefinition",
        "FactionDefinition",
        "RegionDefinition",
        "PlaceDefinition",
    ]

    for cls_name in expected_classes:
        cls = getattr(definition_models, cls_name, None)
        assert cls is not None, (
            f"Missing class '{cls_name}' in definition_models module"
        )
        assert inspect.isclass(cls), (
            f"'{cls_name}' exists but is not a class"
        )

    # Verify inheritance: all concrete subclasses extend DefinitionRecord
    base = definition_models.DefinitionRecord
    for cls_name in expected_classes[1:]:  # Skip DefinitionRecord itself
        cls = getattr(definition_models, cls_name)
        assert issubclass(cls, base), (
            f"{cls_name} does not extend DefinitionRecord"
        )


# =========================================================================
# Test 12: LinkedEntryReference Model Has Expected Fields
# =========================================================================
def test_linked_entry_reference_model_has_expected_fields():
    """
    V05 diagram defines LinkedEntryReference with:
    source_definition_id, target_definition_id, relation_kind.
    """
    from src.systems.dnd5e.content.domain.link_models import LinkedEntryReference

    assert hasattr(LinkedEntryReference, "model_fields"), (
        "LinkedEntryReference is not a Pydantic model"
    )

    expected_fields = {
        "id",
        "source_definition_id",
        "source_path",
        "target_definition_id",
        "target_family",
        "relation_kind",
        "required",
        "resolve_mode",
    }
    actual_fields = set(LinkedEntryReference.model_fields.keys())

    assert expected_fields.issubset(actual_fields), (
        f"LinkedEntryReference is missing fields:\n"
        f"  Missing: {sorted(expected_fields - actual_fields)}"
    )


# =========================================================================
# Test 13: ActionOperationSpec and ModifierSpec Exist with Discriminators
# =========================================================================
def test_action_operation_spec_and_modifier_spec_exist():
    """
    Both ActionOperationSpec and ModifierSpec (as union) must be importable
    and have the expected discriminator structure.
    """
    from src.systems.dnd5e.content.domain.primitives import (
        ActionOperationSpec,
        ModifierSpec,
        FlatModifierSpec,
        DiceModifierSpec,
        RuleOverrideModifierSpec,
        AttackRollPayload,
        SavePayload,
        HealPayload,
        EffectApplicationPayload,
    )

    # ActionOperationSpec must have a 'payload' field with discriminator
    assert "payload" in ActionOperationSpec.model_fields
    assert "activation_cost" in ActionOperationSpec.model_fields
    assert "targeting_spec" in ActionOperationSpec.model_fields
    assert "operation_id" in ActionOperationSpec.model_fields

    # ModifierSpec is a Union — validate concrete types
    assert FlatModifierSpec.model_fields["modifier_type"] is not None
    assert DiceModifierSpec.model_fields["modifier_type"] is not None
    assert RuleOverrideModifierSpec.model_fields["modifier_type"] is not None

    # Operation payloads must have operation_type field
    for payload_cls in [AttackRollPayload, SavePayload, HealPayload, EffectApplicationPayload]:
        assert "operation_type" in payload_cls.model_fields, (
            f"{payload_cls.__name__} missing operation_type field"
        )


# =========================================================================
# Test 14: LifecycleState Enum Coverage
# =========================================================================
def test_lifecycle_state_enum_coverage():
    """
    LifecycleState must contain: draft, published, archived, superseded.
    """
    from src.systems.dnd5e.content.domain.primitives import LifecycleState

    expected_states = {"draft", "published", "archived", "superseded"}
    actual_states = {member.value for member in LifecycleState}

    assert expected_states == actual_states, (
        f"LifecycleState drift detected.\n"
        f"  Expected: {sorted(expected_states)}\n"
        f"  Actual:   {sorted(actual_states)}"
    )


# =========================================================================
# Test 15: RelationKind Enum Matches Diagram
# =========================================================================
def test_relation_kind_enum_matches_diagram():
    """
    V05 diagram defines relation_kind values:
    inline_ref, prerequisite, replacement, parent_child, related, grants.
    """
    from src.systems.dnd5e.content.domain.link_models import RelationKind

    # The diagram specifies these relation kinds
    expected_kinds = {
        "inline_ref", "prerequisite", "replacement",
        "parent_child", "related", "grants",
    }
    actual_kinds = {member.value for member in RelationKind}

    assert expected_kinds.issubset(actual_kinds), (
        f"RelationKind missing diagram values:\n"
        f"  Missing: {sorted(expected_kinds - actual_kinds)}"
    )


# =========================================================================
# Test 16: ContentPackRecord Model Has Expected Fields
# =========================================================================
def test_content_pack_record_has_expected_fields():
    """
    ContentPackRecord must have the core pack management fields.
    """
    from src.systems.dnd5e.content.domain.pack_models import ContentPackRecord

    expected_fields = {
        "id", "title", "lifecycle_state", "is_homebrew",
        "author_user_id",
    }
    actual_fields = set(ContentPackRecord.model_fields.keys())

    assert expected_fields.issubset(actual_fields), (
        f"ContentPackRecord is missing fields:\n"
        f"  Missing: {sorted(expected_fields - actual_fields)}"
    )


# =========================================================================
# Test 17: CompendiumErrorCode Taxonomy Completeness
# =========================================================================
def test_compendium_error_code_taxonomy():
    """
    All reason codes used in the denial taxonomy must exist in
    CompendiumErrorCode.
    """
    from src.systems.dnd5e.content.domain.invariants import CompendiumErrorCode

    expected_codes = {
        "VALIDATION_FAILED",
        "LINKED_TARGET_NOT_FOUND",
        "INVALID_LIFECYCLE_TRANSITION",
        "CYCLE_DETECTED",
        "PACK_NOT_FOUND",
        "PACK_ID_CONFLICT",
        "DEFINITION_NOT_FOUND",
        "DEFINITION_ID_CONFLICT",
        "DUPLICATE_SLUG",
        "VERSION_MISMATCH",
        "INVALID_REPLACEMENT_TARGET",
        "LINKED_TARGET_IN_USE",
        "ILLEGAL_STATE_DEPENDENCY",
        "GRAPH_CYCLE_DETECTED",
    }
    actual_codes = {member.value for member in CompendiumErrorCode}

    assert expected_codes.issubset(actual_codes), (
        f"CompendiumErrorCode missing expected codes:\n"
        f"  Missing: {sorted(expected_codes - actual_codes)}"
    )
