import pytest
from src.services.dice import DiceService
from src.services.rules import RulesEngine

class TestDiceService:
    def test_simple_roll(self):
        result = DiceService.roll("1d20")
        assert result.total >= 1 and result.total <= 20
        assert len(result.detailed_rolls) == 1
        assert result.detailed_rolls[0].sides == 20
        assert result.detailed_rolls[0].count == 1

    def test_constant_addition(self):
        result = DiceService.roll("5")
        assert result.total == 5
        assert result.breakdown == "5"

    def test_complex_expression(self):
        # 1d1+5 should always be 6
        result = DiceService.roll("1d1+5")
        assert result.total == 6
        # Breakdown might vary slightly depending on implementation details, 
        # but should contain the parts.
        assert "1" in result.breakdown # The roll
        assert "5" in result.breakdown

    def test_subtraction(self):
        # 1d1-1 should be 0
        result = DiceService.roll("1d1-1")
        assert result.total == 0
        
    def test_multiple_dice(self):
        # 2d1 should be 2
        result = DiceService.roll("2d1")
        assert result.total == 2
        assert len(result.detailed_rolls[0].rolls) == 2

class TestRulesEngine:
    @pytest.mark.parametrize("score,expected", [
        (1, -5),
        (9, -1),
        (10, 0),
        (11, 0),
        (12, 1),
        (20, 5),
        (30, 10)
    ])
    def test_ability_modifiers(self, score, expected):
        assert RulesEngine.calculate_modifier(score) == expected

    @pytest.mark.parametrize("level,expected", [
        (1, 2),
        (4, 2),
        (5, 3),
        (8, 3),
        (9, 4),
        (13, 5),
        (17, 6),
        (20, 6),
        (0, 2), # CR 0
        (0.125, 2), # CR 1/8
        (30, 9) # CR 30
    ])
    def test_proficiency_bonus(self, level, expected):
        assert RulesEngine.calculate_proficiency_bonus(level) == expected
