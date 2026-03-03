from typing import Tuple, List, Set
from enum import Enum

class TokenSize(Enum):
    TINY = "Tiny" # 1/2 square (occupies 1 logically for grid math)
    SMALL = "Small" # 1 square
    MEDIUM = "Medium" # 1 square
    LARGE = "Large" # 2x2 squares
    HUGE = "Huge" # 3x3 squares
    GARGANTUAN = "Gargantuan" # 4x4 squares (can be bigger, standardizing to 4)

class MapManager:
    def __init__(self):
        # A set of grid coordinate tuples (x, y) that represent difficult terrain
        self.difficult_terrain: Set[Tuple[int, int]] = set()

    def add_difficult_terrain(self, coord: Tuple[int, int]):
        self.difficult_terrain.add(coord)

    def calculate_distance(self, start: Tuple[int, int], end: Tuple[int, int]) -> int:
        """
        Calculates standard 5e Chebyshev distance.
        Every diagonal costs the same as a straight move (Max of dx or dy).
        Returns distance in feet.
        """
        dx = abs(start[0] - end[0])
        dy = abs(start[1] - end[1])
        squares = max(dx, dy)
        return squares * 5

    def calculate_movement_cost(self, path: List[Tuple[int, int]]) -> float:
        """
        Calculates the explicit cost in feet of moving step-by-step through a path.
        Assumes contiguous adjacent steps.
        """
        if not path or len(path) < 2:
            return 0.0
            
        total_cost = 0.0
        current = path[0]
        
        for next_step in path[1:]:
            # Base cost of 1 step is always 5ft in 5e standard geometry
            step_cost = 5.0
            
            # If the square entered is difficult terrain, the cost doubles
            if next_step in self.difficult_terrain:
                step_cost *= 2.0
                
            total_cost += step_cost
            current = next_step
            
        return total_cost

    def get_occupied_squares(self, root: Tuple[int, int], size: TokenSize) -> List[Tuple[int, int]]:
        """
        Returns all grid squares occupied by a token based on its size,
        assuming `root` is the top-left coordinate.
        """
        x, y = root
        
        if size in [TokenSize.TINY, TokenSize.SMALL, TokenSize.MEDIUM]:
            return [(x, y)]
            
        if size == TokenSize.LARGE:
            # 2x2
            return [
                (x, y), (x+1, y),
                (x, y+1), (x+1, y+1)
            ]
            
        if size == TokenSize.HUGE:
            # 3x3
            # We construct dynamically
            return [(x+i, y+j) for i in range(3) for j in range(3)]
            
        if size == TokenSize.GARGANTUAN:
            # 4x4 standard
            return [(x+i, y+j) for i in range(4) for j in range(4)]
            
        return [(x, y)]
