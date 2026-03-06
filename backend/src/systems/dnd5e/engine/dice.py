"""
D&D 5e Dice Service.

Pure functions for dice rolling, expression parsing, and advantage/disadvantage.
No mutable state — results returned as immutable DiceRoll models.
"""

from __future__ import annotations

import random
import re
from typing import Optional, List

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------

class DiceRoll(BaseModel):
    """Result of a dice roll."""

    individual_rolls: List[int]
    modifier: int = 0
    total: int
    roll_count: int = 1
    roll_used: Optional[int] = None  # For adv/disadv: which roll was selected


# ---------------------------------------------------------------------------
# Expression parsing
# ---------------------------------------------------------------------------

_DICE_RE = re.compile(r"^(\d+)d(\d+)([+-]\d+)?$")


def _parse_expression(expression: str) -> tuple[int, int, int]:
    """Parse a dice expression like '2d10+8' into (count, sides, modifier).

    Raises ValueError if the expression is invalid or has 0 dice.
    """
    expression = expression.strip().lower()
    match = _DICE_RE.match(expression)
    if not match:
        raise ValueError(f"Invalid dice expression: '{expression}'")

    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if count <= 0:
        raise ValueError(f"Dice count must be positive, got {count}")
    if sides <= 0:
        raise ValueError(f"Dice sides must be positive, got {sides}")

    return count, sides, modifier


# ---------------------------------------------------------------------------
# DiceService
# ---------------------------------------------------------------------------

class DiceService:
    """Stateless dice rolling service."""

    @staticmethod
    def roll(expression: str, *, seed: Optional[int] = None) -> DiceRoll:
        """Roll dice from an expression like '2d10+8'.

        Args:
            expression: Dice notation string (e.g. "1d20", "2d10+8", "4d6-1").
            seed: Optional RNG seed for deterministic results.

        Returns:
            DiceRoll with individual rolls, modifier, and total.
        """
        count, sides, modifier = _parse_expression(expression)

        rng = random.Random(seed)
        rolls = [rng.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier

        return DiceRoll(
            individual_rolls=rolls,
            modifier=modifier,
            total=total,
            roll_count=count,
        )

    @staticmethod
    def roll_d20(
        *,
        advantage: bool = False,
        disadvantage: bool = False,
        modifier: int = 0,
        roll_overrides: Optional[List[int]] = None,
        seed: Optional[int] = None,
    ) -> DiceRoll:
        """Roll a d20 with optional advantage/disadvantage.

        Per PHB: if both advantage and disadvantage apply, they cancel
        and a single d20 is rolled.

        Args:
            advantage: Roll 2d20, take higher.
            disadvantage: Roll 2d20, take lower.
            modifier: Flat bonus/penalty to add.
            roll_overrides: Override the actual die rolls (for testing).
            seed: Optional RNG seed.

        Returns:
            DiceRoll with roll_used indicating selected value.
        """
        # Cancel out if both present
        if advantage and disadvantage:
            advantage = False
            disadvantage = False

        rng = random.Random(seed)
        use_two = advantage or disadvantage

        if roll_overrides:
            rolls = roll_overrides
        elif use_two:
            rolls = [rng.randint(1, 20), rng.randint(1, 20)]
        else:
            rolls = [rng.randint(1, 20)]

        if advantage:
            roll_used = max(rolls)
        elif disadvantage:
            roll_used = min(rolls)
        else:
            roll_used = rolls[0]

        return DiceRoll(
            individual_rolls=rolls,
            modifier=modifier,
            total=roll_used + modifier,
            roll_count=len(rolls),
            roll_used=roll_used,
        )
