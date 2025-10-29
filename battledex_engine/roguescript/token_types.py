"""
Defines the TokenType enum and KEYWORDS dictionary for RogueScript.

This is in a separate file so that other modules (like Parser) can
import token types without creating circular dependencies with the Lexer.
"""

from enum import Enum, auto

class TokenType(Enum):
    # --- Literals ---
    NUMBER = auto()       # 123, 45.67
    STRING = auto()       # "Hello"
    IDENTIFIER = auto()   # my_variable, opponent, hp

    # --- Keywords ---
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    DEF = auto()          # For defining functions/strategies
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()          # 'nil' or 'null'
    AND = auto()
    OR = auto()
    NOT = auto()

    # --- Single-Character Punctuation ---
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    DOT = auto()          # .
    COMMA = auto()        # ,
    COLON = auto()        # :
    SEMICOLON = auto()    # ;
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACE = auto()       # { (for code blocks)
    RBRACE = auto()       # }
    
    # --- One or Two-Character Operators ---
    EQUALS = auto()       # =
    EQUAL_EQUAL = auto()  # ==
    BANG = auto()         # !
    BANG_EQUAL = auto()   # !=
    GREATER = auto()      # >
    GREATER_EQUAL = auto()# >=
    LESS = auto()         # <
    LESS_EQUAL = auto()   # <=
    
    # --- Special ---
    EOF = auto()          # End of File

# Dictionary mapping keyword strings to their TokenTypes
KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "def": TokenType.DEF,
    "return": TokenType.RETURN,
    "True": TokenType.TRUE,
    "False": TokenType.FALSE,
    "nil": TokenType.NIL,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}

