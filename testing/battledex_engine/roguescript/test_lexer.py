"""
Unit tests for the RogueScript Lexer.

To run (from the top-level RogueDex/ directory):
    python -m unittest discover tests
"""
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..'))
sys.path.insert(0, project_root)
import unittest

# This import will work if you run from the root RogueDex/ directory
from battledex_engine.roguescript.lexer import Lexer, Token
from battledex_engine.roguescript.token_types import TokenType

class TestLexer(unittest.TestCase):

    def assertTokenTypes(self, tokens, expected_types):
        """Helper to check just the types of a list of tokens."""
        token_types = [t.type for t in tokens]
        self.assertEqual(token_types, expected_types)

    def test_single_char_tokens(self):
        """Tests single-character operators and punctuation."""
        code = "+ - * / ( ) { } . , : ;"
        lexer = Lexer(code)
        tokens = lexer.get_all_tokens()
        expected = [
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
            TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACE, TokenType.RBRACE,
            TokenType.DOT, TokenType.COMMA, TokenType.COLON, TokenType.SEMICOLON,
            TokenType.EOF
        ]
        self.assertTokenTypes(tokens, expected)

    def test_two_char_tokens(self):
        """Tests two-character operators."""
        code = "= == ! != > >= < <="
        lexer = Lexer(code)
        tokens = lexer.get_all_tokens()
        expected = [
            TokenType.EQUALS, TokenType.EQUAL_EQUAL,
            TokenType.BANG, TokenType.BANG_EQUAL,
            TokenType.GREATER, TokenType.GREATER_EQUAL,
            TokenType.LESS, TokenType.LESS_EQUAL,
            TokenType.EOF
        ]
        self.assertTokenTypes(tokens, expected)

    def test_number_literals(self):
        """Tests integer and floating-point numbers."""
        code = "123 987.65 0.5"
        lexer = Lexer(code)
        tokens = lexer.get_all_tokens()
        
        self.assertEqual(len(tokens), 4) # 3 numbers + EOF
        self.assertEqual(tokens[0].type, TokenType.NUMBER)
        self.assertEqual(tokens[0].value, 123)
        
        self.assertEqual(tokens[1].type, TokenType.NUMBER)
        self.assertEqual(tokens[1].value, 987.65)
        
        self.assertEqual(tokens[2].type, TokenType.NUMBER)
        self.assertEqual(tokens[2].value, 0.5)

    def test_string_literal(self):
        """Tests a simple string literal."""
        code = '"hello world!"'
        lexer = Lexer(code)
        tokens = lexer.get_all_tokens()
        self.assertEqual(len(tokens), 2) # string + EOF
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, "hello world!")

    def test_unterminated_string(self):
        """Tests that an unterminated string raises an exception."""
        code = '"hello'
        lexer = Lexer(code)
        # assertRaises(Exception, ...) is how you test for errors
        with self.assertRaisesRegex(Exception, "Unterminated string"):
            lexer.get_all_tokens()

    def test_keywords_and_identifiers(self):
        """Tests that keywords are distinguished from identifiers."""
        code = "if (opponent_hp < 10) return False; # check"
        lexer = Lexer(code)
        tokens = lexer.get_all_tokens()
        
        expected_types = [
            TokenType.IF, TokenType.LPAREN, TokenType.IDENTIFIER,
            TokenType.LESS, TokenType.NUMBER, TokenType.RPAREN,
            TokenType.RETURN, TokenType.FALSE, TokenType.SEMICOLON,
            TokenType.EOF
        ]
        
        self.assertTokenTypes(tokens, expected_types)
        
        # Check the identifier value
        self.assertEqual(tokens[2].value, "opponent_hp")

    def test_line_numbers(self):
        """Tests that the lexer correctly tracks line numbers."""
        code = """
        # Start on line 1
        var_a = 10
        
        # This is line 4
        var_b = "hello"
        """
        lexer = Lexer(code)
        tokens = lexer.get_all_tokens()
        
        # 'var_a' is on line 3 (due to newline at start)
        self.assertEqual(tokens[0].line, 3) 
        # 'var_b' is on line 6
        self.assertEqual(tokens[3].line, 6)
        # 'EOF' is on line 7
        self.assertEqual(tokens[6].line, 7)

# This allows running the test file directly
if __name__ == '__main__':
    unittest.main()

