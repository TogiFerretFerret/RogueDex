"""
Unit tests for the RogueScript Parser.

These tests work by:
1. Lexing a source string
2. Parsing the tokens
3. Using ASTPrinter to convert the resulting AST back into a string
4. Asserting that the string matches the expected tree structure.
"""

import unittest

from battledex-engine.roguescript.lexer import Lexer
from battledex-engine.roguescript.parser import Parser
from battledex-engine.roguescript.ast_printer import ASTPrinter

class TestParser(unittest.TestCase):

    def setUp(self):
        """This method is called before each test."""
        self.printer = ASTPrinter()

    def _produce_ast_string(self, code: str) -> str:
        """Helper function to run the full pipeline."""
        lexer = Lexer(code)
        tokens = lexer.get_all_tokens()
        
        parser = Parser(tokens)
        program = parser.parse()
        
        # We print the first (and likely only) statement in the program
        return program.statements[0].accept(self.printer)

    def test_addition(self):
        """Tests simple addition."""
        code = "1 + 2;"
        # Expected: (stmt (+ 1 2))
        expected_ast = "(stmt (+ 1 2))"
        result_ast = self._produce_ast_string(code)
        self.assertEqual(result_ast, expected_ast)

    def test_operator_precedence_simple(self):
        """Tests that multiplication binds tighter than addition."""
        code = "1 + 2 * 3;"
        # Expected: (stmt (+ 1 (* 2 3)))
        expected_ast = "(stmt (+ 1 (* 2 3)))"
        result_ast = self._produce_ast_string(code)
        self.assertEqual(result_ast, expected_ast)

    def test_operator_precedence_complex(self):
        """Tests a more complex precedence chain."""
        code = "1 - 2 * 3 / 4 + 5;"
        # Expected: (stmt (+ (- 1 (/ (* 2 3) 4)) 5))
        expected_ast = "(stmt (+ (- 1 (/ (* 2 3) 4)) 5))"
        result_ast = self._produce_ast_string(code)
        self.assertEqual(result_ast, expected_ast)

    def test_grouping(self):
        """Tests that parentheses override precedence."""
        code = "(1 + 2) * 3;"
        # Expected: (stmt (* (group (+ 1 2)) 3))
        expected_ast = "(stmt (* (group (+ 1 2)) 3))"
        result_ast = self._produce_ast_string(code)
        self.assertEqual(result_ast, expected_ast)

    def test_unary(self):
        """Tests unary operators."""
        code = "-1 + !False;"
        # Expected: (stmt (+ (- 1) (! False)))
        expected_ast = "(stmt (+ (- 1) (! False)))"
        result_ast = self._produce_ast_string(code)
        self.assertEqual(result_ast, expected_ast)

    def test_parse_error(self):
        """Tests that a syntax error raises a ParseError."""
        code = "1 + ;" # Missing right-hand side
        lexer = Lexer(code)
        tokens = lexer.get_all_tokens()
        parser = Parser(tokens)
        
        # We must use assertRaises to catch the expected error
        with self.assertRaisesRegex(Exception, "Expected expression"):
            parser.parse()

if __name__ == '__main__':
    unittest.main()

