"""
battledex_engine/state.py

Defines the data structures that hold the complete, serializable state of a
Rhythm Tetris game.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .tetromino import Tetromino

# Grid Dimensions
GRID_WIDTH = 10
GRID_HEIGHT = 20 # Visible height
BUFFER_HEIGHT = 20 # Invisible height above
TOTAL_HEIGHT = GRID_HEIGHT + BUFFER_HEIGHT

@dataclass
class GameState:
    """
    The root object representing the entire state of a Tetris game.
    """
    # The grid is a list of lists. grid[y][x].
    # 0 = empty, string = color/shape char (e.g. 'I', 'T')
    grid: List[List[str | int]] = field(default_factory=lambda: [[0] * GRID_WIDTH for _ in range(TOTAL_HEIGHT)])
    
    current_piece: Optional[Tetromino] = None
    next_queue: List[str] = field(default_factory=list) # List of shape chars
    hold_piece: Optional[str] = None
    can_hold: bool = True
    
    score: int = 0
    level: int = 1
    lines_cleared: int = 0
    combo: int = -1
    back_to_back: bool = False
    
    game_over: bool = False
    
    # Rhythm State
    bpm: float = 120.0
    current_beat: float = 0.0
    
    # Frame/Tick counter
    tick: int = 0
    
    def get_visible_grid(self):
        """Returns the bottom 20 rows of the grid."""
        return self.grid[BUFFER_HEIGHT:]