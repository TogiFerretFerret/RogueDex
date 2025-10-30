"""
End-to-end tests for the VirtualMachine.

These tests run the full pipeline:
Lexer -> Parser -> Compiler -> VM
"""

import unittest
from battledex_engine.roguescript.vm import VirtualMachine, InterpretResult
from battledex_engine.roguescript.errors import RogueScriptRuntimeError

class TestVM(unittest.TestCase):

    def setUp(self):
        self.vm = VirtualMachine()

    def _run_script(self, code: str) -> (InterpretResult, any):
        """Helper to run a script and get its final result."""
        # We wrap this to catch runtime errors, which the VM
        # now raises as exceptions.
        try:
            result, value = self.vm.interpret(code)
            return (result, value)
        except RogueScriptRuntimeError as e:
            # This is a bit of a hack. The VM's interpret()
            # *also* catches this, but for testing it's
            # easier to catch it here.
            print(e)
            return (InterpretResult.RUNTIME_ERROR, None)


    def test_simple_arithmetic(self):
        code = "(1 + 2) * (10 - 4) / 2;" # 3 * 6 / 2 = 9
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 9)

    def test_precedence(self):
        code = "1 + 2 * 3 - 4 / 2;" # 1 + 6 - 2 = 5
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 5)

    def test_unary(self):
        code = "-(1 + 2) * 5;" # -3 * 5 = -15
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, -15)

    def test_not_and_falsiness(self):
        code = "!True;"
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, False)

        code = "!False;"
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, True)
        
        code = "!nil;"
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, True)
        
        code = "!0;"
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, False) # 0 is not falsy
        
        code = "!(1 + 2);"
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, False) # 3 is not falsy

    def test_comparisons(self):
        code = "1 < 2;"
        result, value = self._run_script(code)
        self.assertEqual(value, True)
        
        code = "1 > 2;"
        result, value = self._run_script(code)
        self.assertEqual(value, False)
        
        code = "2 >= 2;"
        result, value = self._run_script(code)
        self.assertEqual(value, True) # !(2 < 2)
        
        code = "3 <= 2;"
        result, value = self._run_script(code)
        self.assertEqual(value, False) # !(3 > 2)
        
        code = "1 == 1;"
        result, value = self._run_script(code)
        self.assertEqual(value, True)
        
        code = "1 != 1;"
        result, value = self._run_script(code)
        self.assertEqual(value, False)
        
        code = "\"hello\" == \"hello\";"
        result, value = self._run_script(code)
        self.assertEqual(value, True)
        
        code = "\"hello\" != \"world\";"
        result, value = self._run_script(code)
        self.assertEqual(value, True)

    def test_string_concatenation(self):
        code = "\"hello\" + \" \" + \"world\";"
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, "hello world")
        
    def test_division_by_zero(self):
        """Test for runtime error on 1 / 0."""
        code = "1 / 0;"
        # The new VM raises an exception
        with self.assertRaises(RogueScriptRuntimeError):
            self.vm.interpret(code)

    def test_type_errors(self):
        """Test for runtime errors on mismatched types."""
        with self.assertRaises(RogueScriptRuntimeError):
            self.vm.interpret("1 + \"hello\";") # No
            
        with self.assertRaises(RogueScriptRuntimeError):
            self.vm.interpret("\"hello\" - \"world\";") # No

    def test_compile_error_parse(self):
        """Tests that a parse error returns a COMPILE_ERROR result."""
        # FIX: Make this valid syntax that fails to parse
        code = "1 + (2 / );" # Missing expression after '/'
        result, value = self.vm.interpret(code)
        self.assertEqual(result, InterpretResult.COMPILE_ERROR)

    # --- New Tests for Full Language ---
    
    def test_global_variables(self):
        code = """
        var a = 10;
        var b = 20;
        a + b;
        """
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 30)
        
    def test_global_variable_assignment(self):
        code = """
        var a = 10;
        a = a + 5;
        a;
        """
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 15)

    def test_undefined_global(self):
        with self.assertRaises(RogueScriptRuntimeError):
            self.vm.interpret("a + 10;") # 'a' is not defined

    def test_print_statement(self):
        # This just tests that it runs without error
        code = "print \"hello\";"
        result, value = self.vm.interpret(code)
        self.assertEqual(result, InterpretResult.OK)
        # print statements implicitly return nil
        self.assertEqual(value, None)
        
    def test_local_scopes(self):
        code = """
        var a = "global";
        {
            var a = "local";
            print a;
        }
        print a;
        a; # Final expression should be "global"
        """
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, "global")
        
    def test_if_statement(self):
        code = """
        var a = 10;
        if (a > 5) {
            a = 20;
        } else {
            a = 0;
        }
        a;
        """
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 20)
        
    def test_if_else_statement(self):
        code = """
        var a = 3;
        if (a > 5) {
            a = 20;
        } else {
            a = 0;
        }
        a;
        """
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 0)

    def test_logical_operators(self):
        code = "True and False;"
        result, value = self._run_script(code)
        self.assertEqual(value, False)
        
        code = "True or False;"
        result, value = self._run_script(code)
        self.assertEqual(value, True)
        
        code = "nil or \"hello\";" # 'nil' is falsy
        result, value = self._run_script(code)
        self.assertEqual(value, "hello")
        
    def test_while_loop(self):
        code = """
        var a = 0;
        while (a < 5) {
            a = a + 1;
        }
        a;
        """
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 5)

    def test_native_function_call(self):
        # 'use_move' is registered in the VM
        code = "use_move(\"Tackle\");"
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, "Used Tackle!")
        
    def test_user_function_call(self):
        code = """
        def add(a, b) {
            return a + b;
        }
        
        add(5, 3);
        """
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 8)
        
    def test_recursion_fibonacci(self):
        code = """
        def fib(n) {
            if (n < 2) {
                return n;
            }
            return fib(n - 1) + fib(n - 2);
        }
        
        fib(10);
        """
        result, value = self._run_script(code)
        self.assertEqual(result, InterpretResult.OK)
        self.assertEqual(value, 55)

if __name__ == '__main__':
    unittest.main()



