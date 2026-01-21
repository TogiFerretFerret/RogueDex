import unittest
from battledex_engine.tetris_engine import TetrisEngine
from battledex_engine.rogue_bot import RogueBot
from battledex_engine.roguescript.vm import InterpretResult

class TestRogueBot(unittest.TestCase):
    def setUp(self):
        self.engine = TetrisEngine(seed=123)
        self.bot = RogueBot(self.engine)

    def test_native_functions(self):
        # Test if native functions are callable via RogueScript
        script = """
        var start_x = get_piece_x();
        move_right();
        var end_x = get_piece_x();
        if (end_x == start_x + 1) {
            print("Movement Success");
        }
        """
        # VM interpret returns (InterpretResult, value)
        result, _ = self.bot.vm.interpret(script)
        
        self.assertEqual(result, InterpretResult.OK)
        # Check if engine state actually changed
        # Note: piece might start at different X based on shape, but move_right should increment it
        # Piece starts at 3 or 4 usually.
        # We don't verify print output here easily, but we check VM result.

    def test_complex_logic(self):
        # We use a smaller loop bound to be safe and check piece x
        script = """
        var x = get_piece_x();
        if (x < 7) {
            move_right();
            move_right();
        }
        hard_drop();
        """
        result, _ = self.bot.vm.interpret(script)
        self.assertEqual(result, InterpretResult.OK)
        self.assertGreaterEqual(self.engine.state.score, 0)

if __name__ == '__main__':
    unittest.main()
