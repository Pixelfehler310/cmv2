import math

class RulesEngine:
    @staticmethod
    def calculate_modifier(score: int) -> int:
        """
        Calculates the ability score modifier.
        Formula: floor((score - 10) / 2)
        """
        return (score - 10) // 2

    @staticmethod
    def calculate_proficiency_bonus(level_or_cr: float) -> int:
        """
        Calculates the proficiency bonus based on Level or CR.
        Formula: floor((max(1, level) - 1) / 4) + 2
        """
        # Treat CR < 1 as 1 for the purpose of this calculation (CR 0 to 4 is +2)
        effective_level = max(1, level_or_cr)
        return int((effective_level - 1) // 4) + 2
