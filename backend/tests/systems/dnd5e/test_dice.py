"""
Tests for D&D 5e Dice Service.

TDD: Tests written before implementation.
Validates dice expression parsing, rolling, and advantage/disadvantage mechanics.
"""

import pytest

from src.systems.dnd5e.engine.dice import DiceRoll, DiceService


# ---------------------------------------------------------------------------
# Basic Rolling
# ---------------------------------------------------------------------------

class TestDiceRolling:

    def test_roll_d20_returns_1_to_20(self):
        """1d20 always returns a value between 1 and 20."""
        for _ in range(1000):
            result = DiceService.roll("1d20")
            assert 1 <= result.total <= 20

    def test_roll_with_modifier(self):
        """1d20+5 returns a value between 6 and 25."""
        for _ in range(100):
            result = DiceService.roll("1d20+5")
            assert 6 <= result.total <= 25
            assert result.modifier == 5

    def test_roll_with_negative_modifier(self):
        """1d20-3 returns a value between -2 and 17."""
        for _ in range(100):
            result = DiceService.roll("1d20-3")
            assert -2 <= result.total <= 17
            assert result.modifier == -3

    def test_damage_expression_multi_dice(self):
        """2d10+8 returns value between 10 and 28."""
        for _ in range(100):
            result = DiceService.roll("2d10+8")
            assert 10 <= result.total <= 28
            assert len(result.individual_rolls) == 2
            assert result.modifier == 8

    def test_simple_expression_no_modifier(self):
        """4d6 returns value between 4 and 24."""
        for _ in range(100):
            result = DiceService.roll("4d6")
            assert 4 <= result.total <= 24
            assert len(result.individual_rolls) == 4
            assert result.modifier == 0

    def test_single_die(self):
        """1d8 returns value between 1 and 8."""
        for _ in range(100):
            result = DiceService.roll("1d8")
            assert 1 <= result.total <= 8
            assert len(result.individual_rolls) == 1


# ---------------------------------------------------------------------------
# Seeded / Deterministic Rolling
# ---------------------------------------------------------------------------

class TestDiceSeeded:

    def test_seeded_roll_is_deterministic(self):
        """Same seed produces same result."""
        r1 = DiceService.roll("1d20", seed=42)
        r2 = DiceService.roll("1d20", seed=42)
        assert r1.total == r2.total
        assert r1.individual_rolls == r2.individual_rolls


# ---------------------------------------------------------------------------
# Advantage / Disadvantage
# ---------------------------------------------------------------------------

class TestAdvantageDisadvantage:

    def test_advantage_takes_higher_roll(self):
        """Advantage rolls 2d20 and takes the higher."""
        result = DiceService.roll_d20(advantage=True, roll_overrides=[8, 15])
        assert result.total == 15
        assert result.roll_used == 15

    def test_disadvantage_takes_lower_roll(self):
        """Disadvantage rolls 2d20 and takes the lower."""
        result = DiceService.roll_d20(disadvantage=True, roll_overrides=[8, 15])
        assert result.total == 8
        assert result.roll_used == 8

    def test_advantage_and_disadvantage_cancel(self):
        """If both present, roll normally (single d20)."""
        result = DiceService.roll_d20(advantage=True, disadvantage=True)
        assert result.roll_count == 1
        assert 1 <= result.total <= 20

    def test_normal_roll_single_die(self):
        """Normal d20 roll uses single die."""
        result = DiceService.roll_d20()
        assert result.roll_count == 1
        assert 1 <= result.total <= 20

    def test_advantage_roll_count(self):
        """Advantage rolls 2 dice."""
        result = DiceService.roll_d20(advantage=True)
        assert result.roll_count == 2


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestDiceEdgeCases:

    def test_invalid_expression_raises(self):
        """Invalid dice expression raises ValueError."""
        with pytest.raises(ValueError):
            DiceService.roll("not_dice")

    def test_zero_dice_raises(self):
        """0d20 raises ValueError."""
        with pytest.raises(ValueError):
            DiceService.roll("0d20")
