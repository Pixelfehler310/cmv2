import pytest
from datetime import datetime

from src.systems.dnd5e.content.domain.primitives import DefinitionFamily, LifecycleState
from src.systems.dnd5e.content.domain.definition_models import LoreDefinition
from src.systems.dnd5e.content.domain.invariants import CompendiumErrorCode

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
    import pydantic
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
