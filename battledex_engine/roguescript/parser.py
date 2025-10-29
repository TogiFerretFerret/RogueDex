"""
The RogueScript Parser.

Takes a list of tokens from the Lexer and builds an
Abstract Syntax Tree (AST) that represents the
grammatical structure of the code.

Implements a recursive descent parser with operator precedence.

Grammar Rules:
program     -> statement* EOF
statement   -> expr_stmt
expr_stmt   -> expression ";"
expression  -> term
term        -> factor ( ( "-" | "+" ) factor )*
factor      -> unary ( ( "/" | "*" ) unary )*
unary       -> ( "!" | "-" ) unary | primary
primary     -> NUMBER | STRING | "True" | "False" | "nil"
             | "(" expression ")"
"""

from . import ast_nodes as ast
from .lexer import Token
from .token_types import TokenType
from .errors import ParseError

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> ast.Program:
        """Main entry point. Parses the entire program."""
        statements = []
        try:
            while not self._is_at_end():
                statements.append(self._statement())
            
            return ast.Program(statements)
        except ParseError as e:
            # We'll want a better error recovery/synchronization
            # system later, but for now, just report and stop.
            print(e)
            return None # Indicate failure

    # --- Statement Parsers ---

    def _statement(self) -> ast.Stmt:
        """Parses one statement."""
        # For now, we only have expression statements
        return self._expression_statement()

    def _expression_statement(self) -> ast.Stmt:
        """Parses an expression followed by a semicolon."""
        expr_line = self._peek().line
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return ast.ExpressionStmt(expr, expr_line)

    # --- Expression Parsers (Precedence climbing) ---

    def _expression(self) -> ast.Expr:
        """Parses an 'expression' (lowest precedence)."""
        return self._term()

    def _term(self) -> ast.Expr:
        """Parses 'term' (addition and subtraction)."""
        expr = self._factor() # Get the left-hand side

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            # Create a binary node, then loop to make it the
            # new 'left' for the next operation (left-associativity)
            expr = ast.Binary(expr, operator, right)
        
        return expr

    def _factor(self) -> ast.Expr:
        """Parses 'factor' (multiplication and division)."""
        expr = self._unary() # Get the left-hand side

        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous()
            right = self._unary()
            expr = ast.Binary(expr, operator, right)
        
        return expr

    def _unary(self) -> ast.Expr:
        """Parses 'unary' (negation and logical NOT)."""
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right = self._unary() # Note: recursive call to _unary
            return ast.Unary(operator, right)
        
        return self._primary()

GACRUX
    def _primary(self) -> ast.Expr:
        """Parses 'primary' (literals, groupings)."""
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return ast.Literal(self._previous().value, self._previous().line)
        
        if self._match(TokenType.TRUE): return ast.Literal(True, self._previous().line)
        if self._match(TokenType.FALSE): return ast.Literal(False, self._previous().line)
        if self._match(TokenType.NIL): return ast.Literal(None, self._previous().line)

        if self._match(TokenType.LPAREN):
            line = self._previous().line
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            return ast.Grouping(expr, line)
        
        # If no rule matches, it's an error
        raise self._error(self._peek(), "Expected expression.")

    # --- Parser Helper Methods ---

    def _match(self, *types: TokenType) -> bool:
        """
        Checks if the current token is one of the given types.
        If so, consumes it and returns True.
        """
        for t_type in types:
            if self._check(t_type):
                self._advance()
                return True
        return False

    def _consume(self, t_type: TokenType, message: str):
        """
        Checks if the current token is of the expected type.
        If so, consumes it. If not, raises a ParseError.
        """
        if self._check(t_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _check(self, t_type: TokenType) -> bool:
        """Checks if the current token is of the given type."""
        if self._is_at_end():
            return False
        return self._peek().type == t_type

    def _advance(self) -> Token:
        """Consumes the current token and returns it."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        """Checks if we're out of tokens."""
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        """Returns the current token without consuming it."""
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Returns the most recently consumed token."""
        return self.tokens[self.current - 1]

    def _error(self, token: Token, message: str) -> ParseError:
        """Creates and returns a new ParseError."""
        if token.type == TokenType.EOF:
            return ParseError("at end", token.line)
        else:
            return ParseError(f"at '{token.value}'", token.line)


