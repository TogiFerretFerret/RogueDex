"""
Defines all the Abstract Syntax Tree (AST) node classes for RogueScript.

Also defines the Visitor pattern (ABC) which is the key to interacting
with the AST (e.g., for printing, compiling, or interpreting).
"""

from abc import ABC, abstractmethod
from .token_types import Token

# --- Visitor Pattern ---
# This is the magic. Any class that wants to "walk" the AST
# must implement this interface.
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

# --- Base Classes for Nodes ---

class ASTNode(ABC):
    """Base class for all AST nodes."""
    @abstractmethod
    def accept(self, visitor):
        pass

class Expr(ASTNode):
    """Base class for all Expression nodes."""
    pass

class Stmt(ASTNode):
    """Base class for all Statement nodes."""
    pass

# --- Statement (Stmt) Node Classes ---
# Statements form the backbone/flow (e.g., `if`, `while`, var decl)

class Program(Stmt):
    """The root node of the entire AST."""
    def __init__(self, statements: list[Stmt]):
        self.statements = statements

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_program_stmt(self)

class ExpressionStmt(Stmt):
    """A statement that is just a single expression (e.g., '1 + 2;')."""
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_expression_stmt(self)

# --- Expression (Expr) Node Classes ---
# Expressions evaluate to a value (e.g., `1 + 2`, `my_var`, `False`)

class Binary(Expr):
    """A binary operation (e.g., left + right)."""
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right
    
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_binary_expr(self)

class Unary(Expr):
    """A unary operation (e.g., -right, !right)."""
    def __init__(self, operator: Token, right: Expr):
        self.operator = operator
        self.right = right
    
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_unary_expr(self)

class Literal(Expr):
    """A literal value (e.g., 123, "hello", True, False, nil)."""
    def __init__(self, value: any):
        self.value = value
        
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_literal_expr(self)

class Grouping(Expr):
    """A grouping (e.g., (expression))."""
    def __init__(self, expression: Expr):
        self.expression = expression
    
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_grouping_expr(self)

