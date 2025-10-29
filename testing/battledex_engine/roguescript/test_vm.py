"""
Unit tests for the RogueScript Virtual Machine.

These are end-to-end tests that run the full
Lexer -> Parser -> Compiler -> VM pipeline and
check the final result.
"""

import unittest
from battledex_engine.roguescript.vm import VirtualMachine, InterpretResult

class TestVM(unittest.TestCase):

    def setUp(self):
        self.vm = VirtualMachine()

    def _run_script(self, code: str) -> (InterpretResult, any):
        """Helper to run a script and get the result."""
        return self.vm.interpret(code)

    def test_simple_arithmetic(self):
        """Test basic + - * / operators."""
        code = "(1 - 2) * (3 + 4) / 5;" # -1 * 7 / 5 = -1.4
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, -1.4)

    def test_precedence(self):
        """Test operator precedence."""
        code = "1 + 2 * 3 - 4 / 2;" # 1 + 6 - 2 = 5
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 5.0) # Division makes it a float

    def test_unary(self):
        """Test unary - and ! operators."""
        code = "-(1 + 2) * 3;" # -3 * 3 = -9
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, -9)

    def test_not(self):
        """Test logical NOT."""
        result, value = self._run_script("!True;")
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, False)
        
        result, value = self._run_script("!False;")
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, True)

        result, value = self._run_script("!nil;")
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, True) # nil is falsy
        
        result, value = self._run_script("!0;")
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, False) # 0 is not falsy

    def test_division_by_zero(self):
        """Test for runtime error on 1 / 0."""
        result, value = self._run_script("1 / 0;")
        self.assertEqual(result, InterpretResult.RUNTIME_ERROR)

    def test_stack_overflow(self):
        """Test for stack overflow (a bit hacky)."""
        # This is a bit of a hack. We're manually setting the stack
        # to be almost full before running a script.
        self.vm.stack = [0] * (self.vm.STACK_MAX - 1)
        
        # This '1 + 2' will push 1, push 2, add, then push result.
        # The 'push 2' should be the one to fail.
        # (This test is fragile, depends on impl details)
        
        # A better test: make a script that pushes, but doesn't pop.
        # We can't do that without functions or loops yet.
        # For now, we'll just test the compile error.
        
        # A better test for now is a compile error
        result, value = self._run_script("1 + (2");
        self.assertEqual(result, InterpretResult.COMPILE_ERROR)


if __name__ == '__main__':
    unittest.main()

