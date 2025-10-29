"""
The Lexer (Tokenizer) for RogueScript.

Takes raw source code text and breaks it into a list of Tokens.
"""

from dataclasses import dataclass
from .token_types import TokenType, KEYWORDS

@dataclass
class Token:
    """A simple data container for a single token."""
    type: TokenType
    value: any = None
    line: int = 1

    def __repr__(self):
        val = f", {self.value}" if self.value is not None else ""
        return f"Token({self.type.name}{val}, line {self.line})"

class Lexer:
    """
    The main Lexer class. Call get_all_tokens() to process a string.
    """
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
        self.line = 1

    def advance(self):
        """Move the 'pos' pointer and update current_char."""
        if self.current_char == '\n':
            self.line += 1
            
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        """Look one character ahead without advancing."""
        peek_pos = self.pos + 1
        if peek_pos >= len(self.text):
            return None
        return self.text[peek_pos]

    def skip_whitespace_and_comments(self):
        """Skip whitespace and single-line comments (starting with #)."""
        while self.current_char is not None:
            if self.current_char.isspace():
                self.advance()
            elif self.current_char == '#':
                # Skip until the end of the line
                while self.current_char is not None and self.current_char != '\n':
                    self.advance()
            else:
                break # Not whitespace or a comment

    def get_number(self):
        """Consume a full multi-digit integer or float."""
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        # Handle floating point
        if self.current_char == '.' and self.peek() is not None and self.peek().isdigit():
            result += '.'
            self.advance() # Consume the '.'
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()
            return Token(TokenType.NUMBER, float(result), self.line)
        
        return Token(TokenType.NUMBER, int(result), self.line)

    def get_string(self):
        """Consume a string literal. (Doesn't support escape chars yet)"""
        start_line = self.line
        self.advance() # Consume the opening "
        result = ""
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\n':
                # Multi-line strings aren't supported by default
                raise Exception(f"Line {start_line}: Unterminated string.")
            result += self.current_char
            self.advance()
        
        if self.current_char is None:
            raise Exception(f"Line {start_line}: Unterminated string.")
            
        self.advance() # Consume the closing "
        return Token(TokenType.STRING, result, start_line)

    def get_identifier_or_keyword(self):
        """Consume an identifier or a keyword."""
        result = ""
        # Identifiers can start with a letter or _
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        # Check if it's a keyword or just a plain identifier
        token_type = KEYWORDS.get(result, TokenType.IDENTIFIER)
        
        if token_type == TokenType.IDENTIFIER:
            return Token(token_type, result, self.line)
        else:
            # It's a keyword. Store the keyword string ("if", "while")
            # as the value for better error messages.
            return Token(token_type, result, line=self.line)

    def get_next_token(self) -> Token:
        """Get the very next token from the stream."""
        while self.current_char is not None:
            
            self.skip_whitespace_and_comments()

            # Handle case where whitespace/comments are at end of file
            if self.current_char is None:
                break

            if self.current_char.isdigit():
                return self.get_number()

            if self.current_char.isalpha() or self.current_char == '_':
                return self.get_identifier_or_keyword()
            
            if self.current_char == '"':
                return self.get_string()

            # --- Two-character tokens FIRST ---
            if self.current_char == '=':
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.EQUAL_EQUAL, "==", self.line)
                return Token(TokenType.EQUALS, "=", self.line)

            if self.current_char == '!':
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.BANG_EQUAL, "!=", self.line)
                return Token(TokenType.BANG, "!", self.line)

            if self.current_char == '>':
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.GREATER_EQUAL, ">=", self.line)
                return Token(TokenType.GREATER, ">", self.line)
            
            if self.current_char == '<':
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.LESS_EQUAL, "<=", self.line)
                return Token(TokenType.LESS, "<", self.line)

            # --- Single-character tokens ---
            token_map = {
                '+': TokenType.PLUS, '-': TokenType.MINUS,
                '*': TokenType.STAR, '/': TokenType.SLASH,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '.': TokenType.DOT, ',': TokenType.COMMA,
                ':': TokenType.COLON, ';': TokenType.SEMICOLON,
            }
            
            if self.current_char in token_map:
                token_type = token_map[self.current_char]
                op_char = self.current_char # Capture the character
                self.advance()
                return Token(token_type, op_char, line=self.line) # Pass it as the value

            raise Exception(f"Line {self.line}: Invalid character '{self.current_char}'")

        return Token(TokenType.EOF, line=self.line)
    
    def get_all_tokens(self) -> list[Token]:
        """Generate a list of all tokens from the input text."""
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens


