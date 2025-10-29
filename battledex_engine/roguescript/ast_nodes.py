"""
Defines the data structures for the Abstract Syntax Tree (AST).
Uses the Visitor pattern for operations like printing and compiling.
"""

from abc import ABC, abstractmethod
from .lexer import Token

# --- Visitor Pattern ---
# We define two separate visitor classes, one for expressions
# and one for statements, because expressions and statements
# often have different return types (e.g., a value vs. nothing).

class ExprVisitor(ABC):
    @abstractmethod
    def visit_binary_expr(self, expr): pass
    @abstractmethod
    def visit_unary_expr(self, expr): pass
    @abstractmethod
    def visit_literal_expr(self, expr): pass
    @abstractmethod
    def visit_grouping_expr(self, expr): pass

class StmtVisitor(ABC):
    @abstractmethod
    def visit_program_stmt(self, stmt): pass
    @abstractmethod
    def visit_expression_stmt(self, stmt): pass

# --- AST Node Base Classes ---

class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: ExprVisitor):
        pass

class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: StmtVisitor):
        pass

# --- Statement Node Classes ---

class Program(Stmt):
    """The root node of the entire AST."""
    def __init__(self, statements: list[Stmt]):
        self.statements = statements
        # We don't have a specific line,
        # but children nodes will.
        self.line = 1 if statements else 0 

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_program_stmt(self)

class ExpressionStmt(Stmt):
    """A statement that is just a single expression (e.g., '1 + 2;')."""
    def __init__(self, expression: Expr, line: int):
        self.expression = expression
        self.line = line

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_expression_stmt(self)

# --- Expression Node Classes ---

class Binary(Expr):
    """A binary operation (e.g., left + right)."""
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right
        self.line = operator.line # Line number comes from the operator
    
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_binary_expr(self)

class Unary(Expr):
    """A unary operation (e.g., -right, !right)."""
    def __init__(self, operator: Token, right: Expr):
        self.operator = operator
        self.right = right
        self.line = operator.line # Line number comes from the operator
    
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_unary_expr(self)

class Literal(Expr):
    """A literal value (e.g., 123, "hello", True, False, nil)."""
    def __init__(self, value: any, line: int):
        self.value = value
        self.line = line
        
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_literal_expr(self)

class Grouping(Expr):
    """A grouping (e.g., (expression))."""
    def __init__(self, expression: Expr, line: int):
        self.expression = expression
        self.line = line
    
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_grouping_expr(self)


