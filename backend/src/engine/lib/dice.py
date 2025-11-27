import re
import random
from typing import List
from src.schemas.dice import DiceRollResult, DieRoll

class DiceService:
    @staticmethod
    def roll(expression: str) -> DiceRollResult:
        """
        Parses and rolls a dice expression (e.g., "1d20+5", "2d6-1").
        Supports addition and subtraction.
        """
        # Remove whitespace
        clean_expr = expression.replace(" ", "")
        
        # Regex to find terms: (+/-)(count)d(sides) or (+/-)(constant)
        # Groups: 1: Full term, 2: Operator, 3: Dice part (XdY), 4: Constant
        # We need a more robust regex or a simple parser.
        
        # Let's try splitting into terms.
        # We want to match: [+-]? \d+ d \d+  OR  [+-]? \d+
        
        pattern = re.compile(r'([+-]?)(\d+)(?:d(\d+))?')
        matches = pattern.finditer(clean_expr)
        
        total = 0
        breakdown_parts = []
        detailed_rolls = []
        
        # Check if the expression was fully consumed/valid? 
        # For now, let's just process matches.
        
        for match in matches:
            full_match = match.group(0)
            if not full_match:
                continue
                
            sign_str = match.group(1)
            part1 = match.group(2)
            part2 = match.group(3) # If exists, it's 'sides' and part1 is 'count'
            
            multiplier = -1 if sign_str == '-' else 1
            sign_display = " - " if sign_str == '-' else " + "
            if not breakdown_parts and sign_str != '-':
                 sign_display = "" # Don't show + for first term
            elif not breakdown_parts and sign_str == '-':
                 sign_display = "-" # Show - for first term
            
            if part2: # It is a die roll (XdY)
                count = int(part1)
                sides = int(part2)
                
                current_rolls = []
                subtotal = 0
                for _ in range(count):
                    r = random.randint(1, sides)
                    current_rolls.append(r)
                    subtotal += r
                
                term_total = subtotal * multiplier
                total += term_total
                
                detailed_rolls.append(DieRoll(
                    sides=sides,
                    count=count,
                    rolls=current_rolls,
                    total=subtotal # The raw roll sum
                ))
                
                # Format: [3, 5] or [15]
                rolls_str = ", ".join(map(str, current_rolls))
                if count > 1:
                    breakdown_parts.append(f"{sign_display}[{rolls_str}]")
                else:
                    breakdown_parts.append(f"{sign_display}[{rolls_str}]")
                    
            else: # It is a constant
                val = int(part1)
                term_total = val * multiplier
                total += term_total
                
                breakdown_parts.append(f"{sign_display}{val}")
                
        breakdown = "".join(breakdown_parts)
        
        return DiceRollResult(
            expression=expression,
            total=total,
            breakdown=breakdown,
            detailed_rolls=detailed_rolls
        )
