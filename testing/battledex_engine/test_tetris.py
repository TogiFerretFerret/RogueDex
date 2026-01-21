import unittest
import time
from battledex_engine.tetris_engine import TetrisEngine, GRID_WIDTH, TOTAL_HEIGHT, BUFFER_HEIGHT
from battledex_engine.tetromino import Tetromino

class TestTetrisEngine(unittest.TestCase):
    def setUp(self):
        # Use a fixed seed for deterministic tests
        self.engine = TetrisEngine(seed=42)

    def test_spawn_and_bag(self):
        self.assertIsNotNone(self.engine.state.current_piece)
        # 7-bag means after 7 spawns we used one of each
        shapes_seen = {self.engine.state.current_piece.shape}
        for _ in range(6):
            self.engine.lock_piece()
            shapes_seen.add(self.engine.state.current_piece.shape)
        
        self.assertEqual(len(shapes_seen), 7, "7-bag should provide all 7 unique shapes in one cycle")

    def test_srs_rotation_and_kicks(self):
        # T-Spin positioning test (Simple)
        # Place some blocks to force a kick
        self.engine.state.grid[TOTAL_HEIGHT-1][0] = 'G'
        self.engine.state.grid[TOTAL_HEIGHT-1][2] = 'G'
        
        # Manually place a T piece
        self.engine.state.current_piece = Tetromino('T', x=0, y=TOTAL_HEIGHT-2, rotation=0)
        
        # Rotate CW - should kick if blocked?
        # Basic 0->1 rotation for T at (0, TOTAL_HEIGHT-2)
        # Standard coords for T at 0: (1,0), (0,1), (1,1), (2,1)
        # Absolute: (1, 18), (0, 19), (1, 19), (2, 19)
        # If we rotate at (0, 18), blocks are (1, 18), (1, 19), (1, 20), (2, 19) -> 1,20 is out of bounds
        # SRS kick should move it up.
        
        success = self.engine.rotate(clockwise=True)
        self.assertTrue(success, "T-piece should rotate via SRS kick when near floor/wall")
        self.assertLess(self.engine.state.current_piece.y, TOTAL_HEIGHT-1)

    def test_scoring_and_rhythm(self):
        # Force a beat match by overriding start_time or mocking is_on_beat
        # But let's just test the logic
        self.engine.state.grid[TOTAL_HEIGHT-1] = ['I'] * GRID_WIDTH
        self.engine._clear_lines()
        
        self.assertEqual(self.engine.state.lines_cleared, 1)
        # Single line clear score is 100 * level
        self.assertGreaterEqual(self.engine.state.score, 100)

    def test_garbage_handling(self):
        self.engine.add_garbage(2)
        self.assertEqual(self.engine.state.garbage_queue, 2)
        
        # Garbage is processed on lock
        self.engine.lock_piece()
        
        # Bottom 2 rows should be garbage
        self.assertEqual(self.engine.state.grid[TOTAL_HEIGHT-1].count('G'), 9)
        self.assertEqual(self.engine.state.grid[TOTAL_HEIGHT-2].count('G'), 9)

    def test_game_over_topout(self):
        # Fill the entire spawn row in the buffer to guarantee collision
        for x in range(GRID_WIDTH):
            self.engine.state.grid[BUFFER_HEIGHT - 1][x] = 'G'
            self.engine.state.grid[BUFFER_HEIGHT - 2][x] = 'G'
        
        # Next piece will collide on spawn
        self.engine.spawn_piece()
        self.assertTrue(self.engine.state.game_over)

    def test_soft_drop_infinite(self):
        # This is client side logic mostly, but let's test engine.move(0, 1) behavior
        # Piece starts at BUFFER_HEIGHT - 2 (18)
        start_y = self.engine.state.current_piece.y
        while self.engine.move(0, 1):
            pass
        self.assertEqual(self.engine.state.current_piece.y, TOTAL_HEIGHT - 2) # Block at Y+1 for most shapes

if __name__ == '__main__':
    unittest.main()