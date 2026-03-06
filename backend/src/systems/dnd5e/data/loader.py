"""
D&D 5e Compendium Loader.

Reads Open5e-format JSON files and hydrates them into Definition models.
Handles field normalization between Open5e JSON format and our Pydantic schemas.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from ..schemas.common import (
    AbilityScores,
    Components,
    SavingThrows,
    SpeedBlock,
)
from ..schemas.definitions import (
    ActionDefinition,
    ItemDefinition,
    MonsterDefinition,
    SpellDefinition,
    TraitDefinition,
)
from .registry import CompendiumRegistry


class CompendiumLoader:
    """Parses Open5e JSON into Definition models and registers them."""

    def __init__(self, registry: CompendiumRegistry):
        self.registry = registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_monster_file(self, path: str | Path) -> MonsterDefinition:
        """Load a single monster JSON file and register it."""
        raw = self._read_json(path)
        monster = self._parse_monster(raw)
        self.registry.register_monster(monster)
        return monster

    def load_spell_file(self, path: str | Path) -> SpellDefinition:
        """Load a single spell JSON file and register it."""
        raw = self._read_json(path)
        spell = self._parse_spell(raw)
        self.registry.register_spell(spell)
        return spell

    def load_item_file(self, path: str | Path) -> ItemDefinition:
        """Load a single item JSON file and register it."""
        raw = self._read_json(path)
        item = self._parse_item(raw)
        self.registry.register_item(item)
        return item

    def load_directory(self, base_path: str | Path, entity_type: str = "monsters") -> int:
        """Load all JSON files from a directory.

        Args:
            base_path: Directory containing JSON files.
            entity_type: One of 'monsters', 'spells', 'items'.

        Returns:
            Number of entities successfully loaded.
        """
        base = Path(base_path)
        if not base.is_dir():
            return 0

        parsers = {
            "monsters": self.load_monster_file,
            "spells": self.load_spell_file,
            "items": self.load_item_file,
        }
        parser = parsers.get(entity_type)
        if parser is None:
            raise ValueError(f"Unknown entity type: {entity_type}")

        count = 0
        for json_file in sorted(base.glob("*.json")):
            try:
                parser(json_file)
                count += 1
            except Exception as e:
                # Log but don't stop on individual file failures
                print(f"Warning: Failed to load {json_file.name}: {e}")
        return count

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_json(path: str | Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def _parse_monster(cls, raw: dict) -> MonsterDefinition:
        """Transform Open5e monster JSON into a MonsterDefinition."""
        # Build structured sub-models from flat Open5e fields
        speed_data = raw.get("speed", {})
        if isinstance(speed_data, dict):
            speed = SpeedBlock(**speed_data)
        else:
            speed = SpeedBlock(walk=30)

        abilities = AbilityScores(
            strength=raw.get("strength", 10),
            dexterity=raw.get("dexterity", 10),
            constitution=raw.get("constitution", 10),
            intelligence=raw.get("intelligence", 10),
            wisdom=raw.get("wisdom", 10),
            charisma=raw.get("charisma", 10),
        )

        saves = SavingThrows(
            strength_save=raw.get("strength_save"),
            dexterity_save=raw.get("dexterity_save"),
            constitution_save=raw.get("constitution_save"),
            intelligence_save=raw.get("intelligence_save"),
            wisdom_save=raw.get("wisdom_save"),
            charisma_save=raw.get("charisma_save"),
        )

        # Parse actions — Open5e provides a list of dicts with name/desc/attack_bonus/damage_dice
        actions = [
            ActionDefinition(**a) for a in (raw.get("actions") or [])
        ]
        legendary_actions = [
            ActionDefinition(**a) for a in (raw.get("legendary_actions") or [])
        ]
        special_abilities = [
            TraitDefinition(**t) for t in (raw.get("special_abilities") or [])
        ]

        # Handle CR — Open5e provides both "challenge_rating" (str) and "cr" (float)
        cr = raw.get("cr")
        if cr is None:
            cr_str = raw.get("challenge_rating", "0")
            try:
                cr = float(cr_str)
            except (ValueError, TypeError):
                cr = 0.0

        # Legendary action count — parse from legendary_desc or default to 3
        legendary_action_count = 0
        if legendary_actions:
            legendary_action_count = 3  # standard for most legendary creatures

        return MonsterDefinition(
            slug=raw.get("slug", ""),
            name=raw.get("name", ""),
            size=raw.get("size", "Medium"),
            type=raw.get("type", ""),
            subtype=raw.get("subtype", ""),
            alignment=raw.get("alignment", ""),
            armor_class=raw.get("armor_class", 10),
            armor_desc=raw.get("armor_desc"),
            hit_points=raw.get("hit_points", 1),
            hit_dice=raw.get("hit_dice", "1d8"),
            speed=speed,
            abilities=abilities,
            saves=saves,
            skills=raw.get("skills") or {},
            damage_vulnerabilities=raw.get("damage_vulnerabilities", ""),
            damage_resistances=raw.get("damage_resistances", ""),
            damage_immunities=raw.get("damage_immunities", ""),
            condition_immunities=raw.get("condition_immunities", ""),
            senses=raw.get("senses", ""),
            languages=raw.get("languages", ""),
            cr=cr,
            xp=raw.get("xp", 0) or 0,
            actions=actions,
            legendary_actions=legendary_actions,
            special_abilities=special_abilities,
            legendary_desc=raw.get("legendary_desc", "") or "",
            legendary_action_count=legendary_action_count,
            spell_list=raw.get("spell_list") or [],
        )

    @classmethod
    def _parse_spell(cls, raw: dict) -> SpellDefinition:
        """Transform Open5e spell JSON into a SpellDefinition."""
        # Build Components from Open5e's boolean fields
        components = Components(
            verbal=raw.get("requires_verbal_components", False),
            somatic=raw.get("requires_somatic_components", False),
            material=raw.get("requires_material_components", False),
            material_desc=raw.get("material"),
        )

        # Handle the ritual field — Open5e uses both bool and "yes"/"no" string
        ritual = raw.get("can_be_cast_as_ritual", False)
        if isinstance(ritual, str):
            ritual = ritual.lower() in ("yes", "true")

        return SpellDefinition(
            slug=raw.get("slug", ""),
            name=raw.get("name", ""),
            level_int=raw.get("level_int", raw.get("spell_level", 0)),
            school=raw.get("school", "Evocation"),
            casting_time=raw.get("casting_time", ""),
            range=raw.get("range", ""),
            target_range_sort=raw.get("target_range_sort", 0),
            components=components,
            material=raw.get("material", "") or "",
            duration=raw.get("duration", ""),
            requires_concentration=raw.get("requires_concentration", False),
            ritual=ritual,
            desc=raw.get("desc", ""),
            higher_level=raw.get("higher_level", "") or "",
            spell_lists=raw.get("spell_lists") or [],
        )

    @classmethod
    def _parse_item(cls, raw: dict) -> ItemDefinition:
        """Transform Open5e weapon/item JSON into an ItemDefinition."""
        return ItemDefinition(
            slug=raw.get("slug", ""),
            name=raw.get("name", ""),
            category=raw.get("category", ""),
            cost=raw.get("cost", ""),
            damage_dice=raw.get("damage_dice"),
            damage_type=raw.get("damage_type"),
            weight=raw.get("weight", ""),
            properties=raw.get("properties") or [],
        )
