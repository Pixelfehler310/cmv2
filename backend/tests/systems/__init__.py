import pytest
from src.engine.spatial_map import MapManager, TokenSize

def test_distance_calculation_standard():
    # 5e Standard math (Chebyshev distance)
    # distance = max(dx, dy) * 5ft
    
    manager = MapManager()
    
    # Horizontal move
    dist1 = manager.calculate_distance((0,0), (5,0))
    assert dist1 == 25 # 5 squares * 5ft
    
    # Diagonal move
    dist2 = manager.calculate_distance((0,0), (5,5))
    assert dist2 == 25 # 5 squares * 5ft
    
    # Mixed move
    dist3 = manager.calculate_distance((2,2), (5,6))
    # dx = 3, dy = 4. Max is 4. -> 20ft
    assert dist3 == 20

def test_movement_cost():
    manager = MapManager()
    
    # Define a difficult terrain zone
    manager.add_difficult_terrain((2,0))
    manager.add_difficult_terrain((3,0))
    
    # Moving through normal terrain
    cost1 = manager.calculate_movement_cost([(0,0), (1,0)])
    assert cost1 == 5.0
    
    # Moving through the difficult terrain (2 squares, one normal, one difficult)
    # Path: (0,0) -> (1,0) [5ft] -> (2,0) [10ft] -> (3,0) [10ft]
    cost2 = manager.calculate_movement_cost([(0,0), (1,0), (2,0), (3,0)])
    assert cost2 == 25.0

def test_token_occupancy():
    manager = MapManager()
    
    # Medium creature (occupies 1 square)
    medium_squares = manager.get_occupied_squares((5,5), TokenSize.MEDIUM)
    assert len(medium_squares) == 1
    assert (5,5) in medium_squares
    
    # Large creature (occupies 2x2)
    large_squares = manager.get_occupied_squares((5,5), TokenSize.LARGE)
    assert len(large_squares) == 4
    for sq in [(5,5), (6,5), (5,6), (6,6)]:
        assert sq in large_squares

    # Huge creature (occupies 3x3)
    huge_squares = manager.get_occupied_squares((5,5), TokenSize.HUGE)
    assert len(huge_squares) == 9
