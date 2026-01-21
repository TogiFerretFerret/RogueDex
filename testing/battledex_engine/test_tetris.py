import unittest
from battledex_engine.tetris_engine import TetrisEngine, GRID_WIDTH, TOTAL_HEIGHT

class TestTetrisEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TetrisEngine()

    def test_spawn(self):
        self.assertIsNotNone(self.engine.state.current_piece)
        self.assertEqual(len(self.engine.state.next_queue), 5)

    def test_movement(self):
        start_x = self.engine.state.current_piece.x
        self.engine.move(-1, 0)
        self.assertEqual(self.engine.state.current_piece.x, start_x - 1)
        
        self.engine.move(1, 0)
        self.assertEqual(self.engine.state.current_piece.x, start_x)

    def test_hard_drop_lock(self):
        self.engine.hard_drop()
        # Piece should change (spawn new one)
        # And we should have blocks in the grid
        found_block = False
        for row in self.engine.state.grid:
            if any(cell != 0 for cell in row):
                found_block = True
                break
        self.assertTrue(found_block)

    def test_hold(self):
        first_piece = self.engine.state.current_piece.shape
        self.engine.hold()
        self.assertEqual(self.engine.state.hold_piece, first_piece)
        self.assertNotEqual(self.engine.state.current_piece.shape, first_piece)
        self.assertFalse(self.engine.state.can_hold)

    def test_line_clear(self):
        # Manually fill a row
        self.engine.state.grid[TOTAL_HEIGHT - 1] = ['I'] * GRID_WIDTH
        # Manually set a piece above it that won't interfere immediately
        # Actually, simpler to just call _clear_lines directly if it was public,
        # but let's simulate a drop that locks.
        
        # We need to hack the grid to test line clear easily without playing
        self.engine.state.grid[TOTAL_HEIGHT - 1] = ['X'] * GRID_WIDTH
        self.engine._clear_lines()
        
        # Should be empty now
        self.assertEqual(self.engine.state.grid[TOTAL_HEIGHT - 1], [0] * GRID_WIDTH)
        self.assertEqual(self.engine.state.lines_cleared, 1)

if __name__ == '__main__':
    unittest.main()
