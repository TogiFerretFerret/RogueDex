"""
Unit tests for the Parser.

These tests do *not* run the VM. They only check if
the parser builds the correct AST.
"""

import unittest
from battledex_engine.roguescript.lexer import Lexer
from battledex_engine.roguescript.parser import Parser
from battledex_engine.roguescript.errors import ParseError
from battledex_engine.roguescript.ast_printer import ASTPrinter

class TestParser(unittest.TestCase):

    def setUp(self):
        self.printer = ASTPrinter()

    def _assert_ast(self, code: str, expected_ast: str):
        """Helper to run the parser and check its AST output."""
        try:
            lexer = Lexer(code)
            tokens = lexer.get_all_tokens()
            
            parser = Parser(tokens)
            program = parser.parse()
            
            self.assertIsNotNone(program, "Parser returned None")
            
            result_ast = self.printer.print_program(program)
            self.assertEqual(result_ast, expected_ast)
            
        except ParseError as e:
            self.fail(f"Parser failed with: {e}")

    def test_addition(self):
        """Tests simple addition."""
        code = "1 + 2;"
        expected = "(program (stmt (+ 1 2)))"
        self._assert_ast(code, expected)

    def test_operator_precedence_simple(self):
        """Tests that multiplication binds tighter than addition."""
        code = "1 + 2 * 3;"
        expected = "(program (stmt (+ 1 (* 2 3))))"
        self._assert_ast(code, expected)

    def test_operator_precedence_complex(self):
        """Tests a more complex precedence chain."""
        code = "1 - 2 * 3 / 4 + 5;"
        expected = "(program (stmt (+ (- 1 (/ (* 2 3) 4)) 5)))"
        self._assert_ast(code, expected)
        
    def test_grouping(self):
        """Tests that parentheses override precedence."""
        code = "(1 + 2) * 3;"
        expected = "(program (stmt (* (group (+ 1 2)) 3)))"
        self._assert_ast(code, expected)
        
    def test_unary(self):
        """Tests unary operators."""
        code = "-1 + !False;"
        expected = "(program (stmt (+ (- 1) (! False))))"
        self._assert_ast(code, expected)

    def test_parse_error(self):
        """Tests that a syntax error raises a ParseError."""
        lexer = Lexer("1 +;")
        tokens = lexer.get_all_tokens()
        parser = Parser(tokens)
        
        # The new parser catches its own errors and returns None
        program = parser.parse()
        self.assertIsNone(program)

    # --- New Tests ---
    
    def test_var_declaration(self):
        code = "var a = 10;"
        expected = "(program (var a = 10))"
        self._assert_ast(code, expected)
        
    def test_var_declaration_no_init(self):
        code = "var a;"
        expected = "(program (var a = nil))" # nil is implied
        self._assert_ast(code, expected)

    def test_assignment(self):
        code = "a = 10;"
        expected = "(program (stmt (assign a = 10)))"
        self._assert_ast(code, expected)

    def test_block_statement(self):
        code = "{ var a = 1; print a; }"
        expected = "(program (block (var a = 1) (print a)))"
        self._assert_ast(code, expected)
        
    def test_if_statement(self):
        code = "if (True) print 1;"
        expected = "(program (if True (print 1) else=None))"
        self._assert_ast(code, expected)
        
    def test_if_else_statement(self):
        code = "if (False) print 1; else print 2;"
        expected = "(program (if False (print 1) else=(print 2)))"
        self._assert_ast(code, expected)

    def test_while_loop(self):
        code = "while (a < 10) print a;"
        expected = "(program (while (< a 10) (print a)))"
        self._assert_ast(code, expected)
        
    def test_function_declaration(self):
        code = "def my_func(a, b) { return a + b; }"
        expected = "(program (def my_func(a, b) (block (return (+ a b)))))"
        self._assert_ast(code, expected)

    def test_call_expression(self):
        code = "my_func(1, 2 + 3);"
        expected = "(program (stmt (call my_func(1, (+ 2 3)))))"
        self._assert_ast(code, expected)


