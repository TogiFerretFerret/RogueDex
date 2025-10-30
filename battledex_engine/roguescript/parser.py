"""
The RogueScript Parser.

Takes a flat list of Tokens from the Lexer and builds a
hierarchical Abstract Syntax Tree (AST) representing the
grammatical structure of the code.

This is a recursive descent parser.
"""
from __future__ import annotations
from . import ast_nodes as ast
from .token_types import TokenType
from .lexer import Token
from .errors import ParseError

class Parser:
    """
    Parses a list of tokens into an AST.
    
    The grammar implemented is:
    
    program        → declaration* EOF
    declaration    → def_stmt | var_decl | statement
    
    def_stmt       → "def" IDENTIFIER "(" params? ")" block
    params         → IDENTIFIER ( "," IDENTIFIER )*
    var_decl       → "var" IDENTIFIER ( "=" expression )? ";"
    
    statement      → expr_stmt | if_stmt | print_stmt | return_stmt
                   | while_stmt | block
                   
    if_stmt        → "if" "(" expression ")" statement ( "else" statement )?
    while_stmt     → "while" "(" expression ")" statement
    block          → "{" declaration* "}"
    return_stmt    → "return" expression? ";"
    print_stmt     → "print" expression ";"
    expr_stmt      → expression ";"
    
    expression     → assignment
    assignment     → IDENTIFIER "=" assignment | logic_or
    logic_or       → logic_and ( "or" logic_and )*
    logic_and      → equality ( "and" equality )*
    equality       → comparison ( ( "!=" | "==" ) comparison )*
    comparison     → term ( ( ">" | ">=" | "<" | "<=" ) term )*
    term           → factor ( ( "-" | "+" ) factor )*
    factor         → unary ( ( "/" | "*" ) unary )*
    unary          → ( "!" | "-" ) unary | call
    call           → primary ( "(" arguments? ")" )*
    arguments      → expression ( "," expression )*
    primary        → "True" | "False" | "nil" | NUMBER | STRING
                   | IDENTIFIER | "(" expression ")"
    """
    
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0
        self.had_error = False

    def parse(self) -> ast.Program | None:
        """Main entry point. Parses the entire program."""
        statements: list[ast.Stmt] = []
        
        while not self._is_at_end():
            statements.append(self._declaration())
            
        # FIX: Pass the line number of the EOF token
        return ast.Program(statements, self.tokens[self.current].line)

    # --- Declaration Parsers ---
    
    def _declaration(self) -> ast.Stmt:
        """Parses one declaration or statement."""
        try:
            if self._match(TokenType.DEF):
                return self._def_statement("function")
            if self._match(TokenType.VAR):
                return self._var_declaration()
            return self._statement()
        except ParseError as e:
            # Synchronize and continue parsing
            self._synchronize()
            return None # Will be filtered out later if needed
            
    def _def_statement(self, kind: str) -> ast.DefStmt:
        """Parses 'def name(params...) { ... }'"""
        name = self._consume(TokenType.IDENTIFIER, f"Expected {kind} name.")
        
        self._consume(TokenType.LPAREN, f"Expected '(' after {kind} name.")
        params: list[Token] = []
        if not self._check(TokenType.RPAREN):
            while True:
                if len(params) >= 255:
                    self._error(self._peek(), "Cannot have more than 255 parameters.")
                params.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name."))
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RPAREN, "Expected ')' after parameters.")
        
        self._consume(TokenType.LBRACE, f"Expected '{{' before {kind} body.")
        body_line = self._previous().line
        body = self._block()
        
        # FIX: Pass the line number
        return ast.DefStmt(name, params, ast.BlockStmt(body, body_line), name.line)

    def _var_declaration(self) -> ast.VarDeclStmt:
        """Parses 'var name (= init)?; '"""
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name.")
        
        initializer: ast.Expr | None = None
        if self._match(TokenType.EQUALS):
            initializer = self._expression()
            
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        
        # FIX: Pass the line number
        return ast.VarDeclStmt(name, initializer, name.line)

    # --- Statement Parsers ---

    def _statement(self) -> ast.Stmt:
        """Parses one statement."""
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.LBRACE):
            line = self._previous().line
            # FIX: Pass the line number
            return ast.BlockStmt(self._block(), line)
        if self._match(TokenType.IF):
            return self._if_statement()
            
        return self._expression_statement()
        
    def _return_statement(self) -> ast.ReturnStmt:
        """Parses 'return ...;'"""
        keyword = self._previous()
        value: ast.Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
            
        self._consume(TokenType.SEMICOLON, "Expected ';' after return value.")
        # FIX: Pass the line number
        return ast.ReturnStmt(value, keyword.line)

    def _if_statement(self) -> ast.IfStmt:
        """Parses 'if (...) ... else ...'"""
        line = self._previous().line
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after if condition.")
        
        then_branch = self._statement()
        else_branch: ast.Stmt | None = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()
            
        # FIX: Pass the line number
        return ast.IfStmt(condition, then_branch, else_branch, line)

    def _while_statement(self) -> ast.WhileStmt:
        """Parses 'while (...) ...'"""
        line = self._previous().line
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while condition.")
        body = self._statement()
        
        # FIX: Pass the line number
        return ast.WhileStmt(condition, body, line)

    def _block(self) -> list[ast.Stmt]:
        """Parses a list of statements inside '{...}'"""
        statements: list[ast.Stmt] = []
        
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            statements.append(self._declaration())
            
        self._consume(TokenType.RBRACE, "Expected '}' after block.")
        return statements
        
    def _print_statement(self) -> ast.PrintStmt:
        """Parses 'print ...;'"""
        line = self._previous().line
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after value.")
        # FIX: Pass the line number
        return ast.PrintStmt(expr, line)

    def _expression_statement(self) -> ast.ExpressionStmt:
        """Parses an expression as a statement."""
        expr = self._expression()
        line = self._previous().line # Line of last token in expression
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        # FIX: Pass the line number
        return ast.ExpressionStmt(expr, line)
        
    # --- Expression Parsers (by precedence) ---

    def _expression(self) -> ast.Expr:
        """Entrypoint for all expressions."""
        return self._assignment()
        
    def _assignment(self) -> ast.Expr:
        """Parses assignment 'name = value'."""
        expr = self._logic_or() # Left-hand side
        
        if self._match(TokenType.EQUALS):
            equals_token = self._previous()
            value = self._assignment() # Right-hand side is recursive
            
            if isinstance(expr, ast.VariableExpr):
                name_token = expr.name
                # FIX: Pass the line number
                return ast.AssignExpr(name_token, value, equals_token.line)
            
            self._error(equals_token, "Invalid assignment target.")
            
        return expr # Not an assignment

    def _logic_or(self) -> ast.Expr:
        """Parses 'or'."""
        expr = self._logic_and()
        
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._logic_and()
            # FIX: Pass the line number
            expr = ast.LogicalExpr(expr, operator, right, operator.line)
        return expr
        
    def _logic_and(self) -> ast.Expr:
        """Parses 'and'."""
        expr = self._equality()
        
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            # FIX: Pass the line number
            expr = ast.LogicalExpr(expr, operator, right, operator.line)
        return expr

    def _equality(self) -> ast.Expr:
        """Parses '==' and '!='."""
        expr = self._comparison()
        
        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            # FIX: Pass the line number
            expr = ast.Binary(expr, operator, right, operator.line)
        return expr

    def _comparison(self) -> ast.Expr:
        """Parses '>', '>=', '<', '<='."""
        expr = self._term()
        
        while self._match(TokenType.GREATER, TokenType.GREATER_EQUAL, 
                          TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self._previous()
            right = self._term()
            # FIX: Pass the line number
            expr = ast.Binary(expr, operator, right, operator.line)
        return expr

    def _term(self) -> ast.Expr:
        """Parses '+' and '-'."""
        expr = self._factor()
        
        while self._match(TokenType.MINUS, TokenType.PLUS):
            operator = self._previous()
            right = self._factor()
            # FIX: Pass the line number
            expr = ast.Binary(expr, operator, right, operator.line)
        return expr

    def _factor(self) -> ast.Expr:
        """Parses '*' and '/'."""
        expr = self._unary()
        
        while self._match(TokenType.SLASH, TokenType.STAR):
            operator = self._previous()
            right = self._unary()
            # FIX: Pass the line number
            expr = ast.Binary(expr, operator, right, operator.line)
        return expr

    def _unary(self) -> ast.Expr:
        """Parses '!' and '-' (prefix)."""
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            # FIX: Pass the line number
            return ast.Unary(operator, right, operator.line)
        return self._call()

    def _call(self) -> ast.Expr:
        """Parses function calls."""
        expr = self._primary()
        
        while self._match(TokenType.LPAREN):
            line = self._previous().line
            expr = self._finish_call(expr, line)
            
        return expr
        
    def _finish_call(self, callee: ast.Expr, line: int) -> ast.CallExpr:
        """Parses the argument list of a call."""
        arguments: list[ast.Expr] = []
        if not self._check(TokenType.RPAREN):
            while True:
                if len(arguments) >= 255:
                    self._error(self._peek(), "Cannot have more than 255 arguments.")
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
                    
        self._consume(TokenType.RPAREN, "Expected ')' after arguments.")
        # FIX: Pass the line number
        return ast.CallExpr(callee, arguments, line)

    def _primary(self) -> ast.Expr:
        """ParsE:s literals, groupings, and identifiers."""
        line = self._peek().line
        
        if self._match(TokenType.FALSE): 
            # FIX: Pass the line number
            return ast.Literal(False, self._previous().line)
        if self._match(TokenType.TRUE): 
            # FIX: Pass the line number
            return ast.Literal(True, self._previous().line)
        if self._match(TokenType.NIL): 
            # FIX: Pass the line number
            return ast.Literal(None, self._previous().line)
            
        if self._match(TokenType.NUMBER, TokenType.STRING):
            # FIX: Pass the line number
            return ast.Literal(self._previous().value, self._previous().line)
            
        if self._match(TokenType.IDENTIFIER):
            # FIX: Pass the line number
            return ast.VariableExpr(self._previous(), self._previous().line)
            
        if self._match(TokenType.LPAREN):
            line = self._previous().line
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            # FIX: Pass the line number
            return ast.Grouping(expr, line)
            
        # FIX: Corrected SyntaxError
        raise self._error(self._peek(), "Error: Expected expression")

    # --- Parser Helpers ---

    def _match(self, *types: TokenType) -> bool:
        """Checks if the current token is one of the types."""
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        """Consumes the current token if it matches, else errors."""
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _check(self, token_type: TokenType) -> bool:
        """Checks the current token type without consuming."""
        if self._is_at_end():
            return False
        return self.tokens[self.current].type == token_type

    def _advance(self) -> Token:
        """Consumes one token and returns it."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self.tokens[self.current].type == TokenType.EOF

    def _peek(self) -> Token:
        """Returns the current token without consuming."""
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Returns the most recently consumed token."""
        return self.tokens[self.current - 1]

    def _error(self, token: Token, message: str) -> ParseError:
        """Reports a parse error."""
        line = token.line
        if token.type == TokenType.EOF:
            loc = "at end"
        else:
            loc = f"at '{token.value}'"
        
        err_msg = f"[Line {line}] Error: {message} ({loc})"
        self.had_error = True
        return ParseError(err_msg)

    def _synchronize(self):
        """Discards tokens until a probable statement boundary."""
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            
            # Look for tokens that likely start a new statement
            if self._peek().type in (
                TokenType.DEF, TokenType.VAR, TokenType.IF, 
                TokenType.WHILE, TokenType.PRINT, TokenType.RETURN,
                TokenType.FOR, TokenType.LBRACE
            ):
                return


