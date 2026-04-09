from __future__ import annotations
__production_status__ = "gold"

import re
import unicodedata
from typing import Optional

from pydantic import BaseModel, Field

from .definition_models import DefinitionRecord
from .primitives import DefinitionFamily, LifecycleState


FAMILY_PAYLOAD_FILTER_KEYS: dict[DefinitionFamily, tuple[str, ...]] = {
    DefinitionFamily.LORE: ("lore_type",),
    DefinitionFamily.SPECIES: ("size", "speed"),
    DefinitionFamily.CLASS: ("hit_die",),
    DefinitionFamily.CONDITION: ("condition_type",),
    DefinitionFamily.ABILITY: ("ability_type",),
    DefinitionFamily.SPELL: ("school", "level", "casting_time"),
    DefinitionFamily.ITEM: ("item_type",),
    DefinitionFamily.MONSTER: ("challenge_rating", "armor_class"),
    DefinitionFamily.ACTION: ("action_type", "activation_cost"),
    DefinitionFamily.FACTION: ("influence_tier", "alignment"),
    DefinitionFamily.REGION: ("climate",),
    DefinitionFamily.PLACE: ("place_type",),
}


class IndexDocument(BaseModel):
    """Flat, denormalized search document — the V05 ReadModel."""

    document_id: str
    definition_id: str
    family: str
    pack_id: str
    name: str
    name_normalized: str
    search_blob: str = ""
    tags: list[str] = Field(default_factory=list)
    search_tokens: list[str] = Field(default_factory=list)
    sortable_fields: dict[str, str] = Field(default_factory=dict)
    visibility_state: str


def _normalize_text(text: str) -> str:
    """Strip accents, lowercase, and collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_only.lower().strip())


def _tokenize(text: str) -> list[str]:
    """Split into search tokens: lowercase, stripped, deduplicated."""
    normalized = _normalize_text(text)
    raw_tokens = re.split(r"[^a-z0-9]+", normalized)
    seen: set[str] = set()
    tokens: list[str] = []
    for token in raw_tokens:
        if token and token not in seen:
            seen.add(token)
            tokens.append(token)
    return tokens


def build_index_document(definition: DefinitionRecord) -> IndexDocument:
    """
    Build a flat IndexDocument from a DefinitionRecord.

    Extracts searchable content from the definition's core fields and
    family-specific payload fields to create a comprehensive search blob.
    """
    name_normalized = _normalize_text(definition.name)
    tokens = _tokenize(definition.name)

    # Build the search blob from available text fields
    search_parts = [definition.name, definition.slug, definition.family.value]

    # Extract family-specific searchable fields from the model
    family_search_fields = _extract_family_search_fields(definition)
    search_parts.extend(family_search_fields)

    # Add key:value payload tokens to support precise family-aware filtering.
    family_payload_filters = _extract_family_payload_filters(definition)
    search_parts.extend(
        f"{key}:{value}" for key, value in family_payload_filters.items()
    )

    search_blob = _normalize_text(" ".join(search_parts))

    # Build tags from family + lifecycle
    tags = [definition.family.value, definition.lifecycle_state.value]

    # Merge family-specific tokens into the token list
    for part in family_search_fields:
        tokens.extend(_tokenize(part))

    # Deduplicate tokens
    seen: set[str] = set()
    unique_tokens: list[str] = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            unique_tokens.append(t)

    return IndexDocument(
        document_id=f"idx-{definition.id}",
        definition_id=definition.id,
        family=definition.family.value,
        pack_id=definition.pack_id,
        name=definition.name,
        name_normalized=name_normalized,
        search_blob=search_blob,
        tags=tags,
        search_tokens=unique_tokens,
        sortable_fields={
            "name": name_normalized,
            "family": definition.family.value,
        },
        visibility_state=definition.lifecycle_state.value,
    )


def _extract_family_search_fields(definition: DefinitionRecord) -> list[str]:
    """Pull searchable text fields from family-specific models."""
    fields: list[str] = []

    # Use hasattr to pull from concrete subclass fields without importing all
    if hasattr(definition, "lore_type"):
        fields.append(definition.lore_type)

    if hasattr(definition, "school"):
        fields.append(definition.school)

    if hasattr(definition, "item_type"):
        fields.append(definition.item_type)

    if hasattr(definition, "condition_type"):
        fields.append(definition.condition_type)

    if hasattr(definition, "ability_type"):
        fields.append(definition.ability_type)

    if hasattr(definition, "hit_die"):
        fields.append(definition.hit_die)

    if hasattr(definition, "casting_time"):
        fields.append(definition.casting_time)

    if hasattr(definition, "action_type"):
        fields.append(definition.action_type)

    if hasattr(definition, "activation_cost"):
        fields.append(definition.activation_cost)

    if hasattr(definition, "influence_tier"):
        fields.append(definition.influence_tier)

    if hasattr(definition, "climate") and definition.climate:
        fields.append(definition.climate)

    if hasattr(definition, "place_type"):
        fields.append(definition.place_type)

    return fields


def _extract_family_payload_filters(definition: DefinitionRecord) -> dict[str, str]:
    filters: dict[str, str] = {}
    allowed_keys = FAMILY_PAYLOAD_FILTER_KEYS.get(definition.family, ())
    for key in allowed_keys:
        value = getattr(definition, key, None)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        filters[key] = str(value)
    return filters
