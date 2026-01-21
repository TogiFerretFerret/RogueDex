from dataclasses import dataclass, field
from typing import List, Tuple, Dict

# Shapes defined as list of (x, y) coordinates relative to a center (0, 0)
# Standard SRS bounding box usually implies a center.
# For I and O, the center is between blocks, handled via offsets or float coords?
# Common implementation: Use 0-3 grid for all except I (0-4).

# We will use the standard SRS rotation system.
# Coordinates are (x, y)
SHAPES = {
    'I': [
        [(0, 1), (1, 1), (2, 1), (3, 1)], # 0
        [(2, 0), (2, 1), (2, 2), (2, 3)], # 90
        [(0, 2), (1, 2), (2, 2), (3, 2)], # 180
        [(1, 0), (1, 1), (1, 2), (1, 3)]  # 270
    ],
    'J': [
        [(0, 0), (0, 1), (1, 1), (2, 1)], # 0
        [(1, 0), (2, 0), (1, 1), (1, 2)], # 90
        [(0, 1), (1, 1), (2, 1), (2, 2)], # 180
        [(1, 0), (1, 1), (0, 2), (1, 2)]  # 270
    ],
    'L': [
        [(2, 0), (0, 1), (1, 1), (2, 1)], # 0
        [(1, 0), (1, 1), (1, 2), (2, 2)], # 90
        [(0, 1), (1, 1), (2, 1), (0, 2)], # 180
        [(0, 0), (1, 0), (1, 1), (1, 2)]  # 270
    ],
    'O': [
        [(1, 0), (2, 0), (1, 1), (2, 1)], # 0 - O doesn't rotate effectively
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)]
    ],
    'S': [
        [(1, 0), (2, 0), (0, 1), (1, 1)], # 0
        [(1, 0), (1, 1), (2, 1), (2, 2)], # 90
        [(1, 1), (2, 1), (0, 2), (1, 2)], # 180
        [(0, 0), (0, 1), (1, 1), (1, 2)]  # 270
    ],
    'T': [
        [(1, 0), (0, 1), (1, 1), (2, 1)], # 0
        [(1, 0), (1, 1), (2, 1), (1, 2)], # 90
        [(0, 1), (1, 1), (2, 1), (1, 2)], # 180
        [(1, 0), (0, 1), (1, 1), (1, 2)]  # 270
    ],
    'Z': [
        [(0, 0), (1, 0), (1, 1), (2, 1)], # 0
        [(2, 0), (1, 1), (2, 1), (1, 2)], # 90
        [(0, 1), (1, 1), (1, 2), (2, 2)], # 180
        [(1, 0), (0, 1), (1, 1), (0, 2)]  # 270
    ]
}

COLORS = {
    'I': (0, 255, 255),    # Cyan
    'J': (0, 0, 255),      # Blue
    'L': (255, 165, 0),    # Orange
    'O': (255, 255, 0),    # Yellow
    'S': (0, 255, 0),      # Green
    'T': (128, 0, 128),    # Purple
    'Z': (255, 0, 0),      # Red
    'G': (100, 100, 100)   # Gray (Garbage)
}

# Wall Kicks (JLSTZ)
# (x, y) offset
# Test 1 is always (0, 0)
WALL_KICKS_JLSTZ = {
    (0, 1):  [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)], # 0->R
    (1, 0):  [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],   # R->0
    (1, 2):  [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],    # R->2
    (2, 1):  [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],# 2->R
    (2, 3):  [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],   # 2->L
    (3, 2):  [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)], # L->2
    (3, 0):  [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)], # L->0
    (0, 3):  [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)]    # 0->L
}

# Wall Kicks (I)
WALL_KICKS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)]
}

@dataclass
class Tetromino:
    shape: str
    rotation: int = 0 # 0, 1, 2, 3 (0, 90, 180, 270)
    x: int = 3 # Spawn position x
    y: int = -1 # Spawn position y (usually -1 or -2 to spawn above board)
    
    def get_blocks(self) -> List[Tuple[int, int]]:
        """Returns the absolute coordinates of the blocks on the grid."""
        local_coords = SHAPES[self.shape][self.rotation]
        return [(x + self.x, y + self.y) for x, y in local_coords]

    def get_color(self):
        return COLORS[self.shape]
