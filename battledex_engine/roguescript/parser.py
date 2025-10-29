"""
The RogueScript Parser.

Takes a list of tokens from the Lexer and builds an
Abstract Syntax Tree (AST) that represents the
grammatical structure of the code.

Implements a recursive descent parser with operator precedence.

Grammar Rules:
program     -> declaration* EOF
declaration -> def_stmt | var_decl | statement
statement   -> print_stmt | if_stmt | while_stmt | block_stmt
             | return_stmt | expr_stmt

def_stmt    -> "def" IDENTIFIER "(" parameters? ")" block_stmt
parameters  -> IDENTIFIER ( "," IDENTIFIER )*
var_decl    -> "var" IDENTIFIER ( "=" expression )? ";"
print_stmt  -> "print" expression ";"
return_stmt -> "return" expression? ";"
if_stmt     -> "if" "(" expression ")" statement ( "else" statement )?
while_stmt  -> "while" "(" expression ")" statement
block_stmt  -> "{" declaration* "}"
expr_stmt   -> expression ";"

expression  -> assignment
assignment  -> IDENTIFIER "=" assignment | logic_or
logic_or    -> logic_and ( "or" logic_and )*
logic_and   -> equality ( "and" equality )*
equality    -> comparison ( ( "!=" | "==" ) comparison )*
comparison  -> term ( ( ">" | ">=" | "<" | "<=" ) term )*
term        -> factor ( ( "-" | "+" ) factor )*
factor      -> unary ( ( "/" | "*" ) unary )*
unary       -> ( "!" | "-" ) unary | call
call        -> primary ( "(" arguments? ")" )*
arguments   -> expression ( "," expression )*
primary     -> NUMBER | STRING | "True" | "False" | "nil"
             | "(" expression ")" | IDENTIFIER
"""

from . import ast_nodes as ast
from .lexer import Token
from .token_types import TokenType
from .errors import ParseError

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0
        self._had_error = False

    def parse(self) -> ast.Program:
        """Main entry point. Parses the entire program."""
        statements = []
        while not self._is_at_end():
            try:
                statements.append(self._declaration())
            except ParseError as e:
                print(e) # Report the error
                self._had_error = True
                self._synchronize() # Recover and keep parsing
        
        if self._had_error:
            return None # Don't feed a broken AST to the compiler
            
        return ast.Program(statements)

    # --- Statement Parsers ---

    def _declaration(self) -> ast.Stmt:
        """Parses a declaration or a statement."""
        if self._match(TokenType.DEF):
            return self._def_statement("function")
        if self._match(TokenType.VAR):
            return self._var_declaration()
        return self._statement()

    def _def_statement(self, kind: str) -> ast.Stmt:
        """Parses a function declaration."""
        name = self._consume(TokenType.IDENTIFIER, f"Expected {kind} name.")
        self._consume(TokenType.LPAREN, f"Expected '(' after {kind} name.")
        
        parameters = []
        if not self._check(TokenType.RPAREN):
            # Parse parameters
            parameters.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name."))
            while self._match(TokenType.COMMA):
                if len(parameters) >= 255:
                    self._error(self._peek(), "Cannot have more than 255 parameters.")
                parameters.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name."))
                
        self._consume(TokenType.RPAREN, "Expected ')' after parameters.")
        
        self._consume(TokenType.LBRACE, f"Expected '{{' before {kind} body.")
        body_line = self._previous().line
        body = ast.BlockStmt(self._block(), body_line)
        
        return ast.DefStmt(name, parameters, body)

    def _var_declaration(self) -> ast.Stmt:
        """Parses 'var' IDENTIFIER ('=' expression)? ';'"""
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name.")
        
        initializer = None
        if self._match(TokenType.EQUALS):
            initializer = self._expression()
            
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return ast.VarDeclStmt(name, initializer)

    def _statement(self) -> ast.Stmt:
        """Parses one statement."""
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.LBRACE):
            line = self._previous().line
            return ast.BlockStmt(self._block(), line)
        if self._match(TokenType.RETURN):
            return self._return_statement()
            
        return self._expression_statement()

    def _print_statement(self) -> ast.Stmt:
        """Parses 'print' expression ';'"""
        line = self._previous().line
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after value.")
        return ast.PrintStmt(value, line)

    def _return_statement(self) -> ast.Stmt:
        """Parses 'return' expression? ';'"""
        keyword = self._previous()
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        
        self._consume(TokenType.SEMICOLON, "Expected ';' after return value.")
        return ast.ReturnStmt(keyword, value)

    def _if_statement(self) -> ast.Stmt:
        """Parses 'if' '(' expression ')' statement ('else' statement)?"""
        line = self._previous().line
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after if condition.")
        
        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()
            
        return ast.IfStmt(condition, then_branch, else_branch, line)

    def _while_statement(self) -> ast.Stmt:
        """Parses 'while' '(' expression ')' statement"""
        line = self._previous().line
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while condition.")
        body = self._statement()
        
        return ast.WhileStmt(condition, body, line)

    def _block(self) -> list[ast.Stmt]:
        """Parses a block: '{' declaration* '}'"""
        statements = []
        
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            statements.append(self._declaration())
            
        self._consume(TokenType.RBRACE, "Expected '}' after block.")
        return statements

    def _expression_statement(self) -> ast.Stmt:
        """Parses an expression followed by a semicolon."""
        expr_line = self._peek().line
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return ast.ExpressionStmt(expr, expr_line)

    # --- Expression Parsers (Precedence climbing) ---

    def _expression(self) -> ast.Expr:
        """Parses an 'expression' (assignment)."""
        return self._assignment()

    def _assignment(self) -> ast.Expr:
        """Parses an assignment or a lower-precedence expression."""
        expr = self._logic_or() # Left-hand side
        
        if self._match(TokenType.EQUALS):
            equals_token = self._previous()
            value = self._assignment() # Right-hand side is recursive
            
            if isinstance(expr, ast.VariableExpr):
                name_token = expr.name
                return ast.AssignExpr(name_token, value)
            
            # If we get here, it's an invalid assignment target
            raise self._error(equals_token, "Invalid assignment target.")
            
        return expr # Not an assignment

    def _logic_or(self) -> ast.Expr:
        """Parses 'or' logical expressions."""
        expr = self._logic_and()
        
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._logic_and()
            expr = ast.LogicalExpr(expr, operator, right)
            
        return expr

    def _logic_and(self) -> ast.Expr:
        """Parses 'and' logical expressions."""
        expr = self._equality()
        
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = ast.LogicalExpr(expr, operator, right)
            
        return expr

    def _equality(self) -> ast.Expr:
        """Parses '==' and '!=' expressions."""
        expr = self._comparison()
        
        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = ast.Binary(expr, operator, right)
        
        return expr

    def _comparison(self) -> ast.Expr:
        """Parses '>', '>=', '<', '<=' expressions."""
        expr = self._term()
        
        while self._match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self._previous()
            right = self._term()
            expr = ast.Binary(expr, operator, right)
            
        return expr

    def _term(self) -> ast.Expr:
        """Parses '+' and '-' expressions."""
        expr = self._factor()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            expr = ast.Binary(expr, operator, right)
        
        return expr

    def _factor(self) -> ast.Expr:
        """Parses '*' and '/' expressions."""
        expr = self._unary()

        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous()
            right = self._unary()
            expr = ast.Binary(expr, operator, right)
        
        return expr

    def _unary(self) -> ast.Expr:
        """Parses '!' and '-' expressions."""
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return ast.Unary(operator, right)
        
        return self._call()

    def _call(self) -> ast.Expr:
        """Parses a function call."""
        expr = self._primary()
        
        # This while loop handles repeated calls like func(1)(2)
        while self._match(TokenType.LPAREN):
            expr = self._finish_call(expr)
            
        return expr

    def _finish_call(self, callee: ast.Expr) -> ast.Expr:
        """Parses the argument list for a call."""
        arguments = []
        if not self._check(TokenType.RPAREN):
            # Parse arguments
            arguments.append(self._expression())
            while self._match(TokenType.COMMA):
                if len(arguments) >= 255:
                    self._error(self._peek(), "Cannot have more than 255 arguments.")
                arguments.append(self._expression())
                
        paren = self._consume(TokenType.RPAREN, "Expected ')' after arguments.")
        return ast.CallExpr(callee, paren, arguments)

    def _primary(self) -> ast.Expr:
        """Parses literals, groupings, and variable names."""
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return ast.Literal(self._previous().value, self._previous().line)
        
        if self._match(TokenType.TRUE): return ast.Literal(True, self._previous().line)
        if self._match(TokenType.FALSE): return ast.Literal(False, self._previous().line)
        if self._match(TokenType.NIL): return ast.Literal(None, self._previous().line)

        if self._match(TokenType.IDENTIFIER):
            return ast.VariableExpr(self._previous())

        if self._match(TokenType.LPAREN):
            line = self._previous().line
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            return ast.Grouping(expr, line)
        
        raise self._error(self._peek(), "Expected expression")

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
        """Creates and raises a new ParseError."""
        if token.type == TokenType.EOF:
            raise ParseError(f"{message} (at end)", token.line)
        else:
            raise ParseError(f"{message} (at '{token.value}')", token.line)

    def _synchronize(self):
        """Error recovery: advance until we're at a likely statement boundary."""
        self._advance()
        
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return # We're at the end of a statement

            # Check for tokens that likely start a new statement
            if self._peek().type in (
                TokenType.DEF, TokenType.VAR, TokenType.FOR, 
                TokenType.IF, TokenType.WHILE, TokenType.PRINT, 
                TokenType.RETURN
            ):
                return
            
            self._advance()


