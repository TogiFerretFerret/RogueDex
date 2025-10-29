from enum import Enum, auto

class TokenType(Enum):
    # --- Literals ---
    NUMBER = auto()       # 123, 45.67
    STRING = auto()       # "Hello"
    IDENTIFIER = auto()   # my_variable, opponent, hp

    # --- Keywords ---
    VAR = auto()          # var
    PRINT = auto()        # print
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    DEF = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
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

KEYWORDS = {
    "var": TokenType.VAR,
    "print": TokenType.PRINT,
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


