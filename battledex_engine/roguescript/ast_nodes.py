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
    @abstractmethod
    def visit_variable_expr(self, expr): pass
    @abstractmethod
    def visit_assign_expr(self, expr): pass
    @abstractmethod
    def visit_logical_expr(self, expr): pass
    @abstractmethod
    def visit_call_expr(self, expr): pass

class StmtVisitor(ABC):
    @abstractmethod
    def visit_program_stmt(self, stmt): pass
    @abstractmethod
    def visit_expression_stmt(self, stmt): pass
    @abstractmethod
    def visit_print_stmt(self, stmt): pass
    @abstractmethod
    def visit_var_decl_stmt(self, stmt): pass
    @abstractmethod
    def visit_block_stmt(self, stmt): pass
    @abstractmethod
    def visit_if_stmt(self, stmt): pass
    @abstractmethod
    def visit_while_stmt(self, stmt): pass
    @abstractmethod
    def visit_def_stmt(self, stmt): pass
    @abstractmethod
    def visit_return_stmt(self, stmt): pass


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

class PrintStmt(Stmt):
    """A 'print' statement."""
    def __init__(self, expression: Expr, line: int):
        self.expression = expression
        self.line = line
        
    def accept(self, visitor: StmtVisitor):
        return visitor.visit_print_stmt(self)

class VarDeclStmt(Stmt):
    """A 'var' variable declaration."""
    def __init__(self, name: Token, initializer: Expr | None):
        self.name = name
        self.initializer = initializer
        self.line = name.line
        
    def accept(self, visitor: StmtVisitor):
        return visitor.visit_var_decl_stmt(self)

class BlockStmt(Stmt):
    """A code block '{ ... }'."""
    def __init__(self, statements: list[Stmt], line: int):
        self.statements = statements
        self.line = line
        
    def accept(self, visitor: StmtVisitor):
        return visitor.visit_block_stmt(self)

class IfStmt(Stmt):
    """An 'if' ( 'else' ) statement."""
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Stmt | None, line: int):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.line = line
        
    def accept(self, visitor: StmtVisitor):
        return visitor.visit_if_stmt(self)

class WhileStmt(Stmt):
    """A 'while' loop statement."""
    def __init__(self, condition: Expr, body: Stmt, line: int):
        self.condition = condition
        self.body = body
        self.line = line
        
    def accept(self, visitor: StmtVisitor):
        return visitor.visit_while_stmt(self)

class DefStmt(Stmt):
    """A 'def' function declaration."""
    def __init__(self, name: Token, params: list[Token], body: BlockStmt):
        self.name = name
        self.params = params
        self.body = body
        self.line = name.line

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_def_stmt(self)
        
class ReturnStmt(Stmt):
    """A 'return' statement."""
    def __init__(self, keyword: Token, value: Expr | None):
        self.keyword = keyword # The 'return' token
        self.value = value
        self.line = keyword.line

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_return_stmt(self)

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

class VariableExpr(Expr):
    """A variable access (e.g., 'my_var')."""
    def __init__(self, name: Token):
        self.name = name
        self.line = name.line
    
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_variable_expr(self)

class AssignExpr(Expr):
    """A variable assignment (e.g., 'my_var = 10')."""
    def __init__(self, name: Token, value: Expr):
        self.name = name
        self.value = value
        self.line = name.line
        
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_assign_expr(self)

class LogicalExpr(Expr):
    """A logical 'and' or 'or' expression."""
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right
        self.line = operator.line
        
    def accept(self, visitor: ExprVisitor):
        return visitor.visit_logical_expr(self)

class CallExpr(Expr):
    """A function call expression."""
    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]):
        self.callee = callee
        self.paren = paren # The ')' token, for its line number
        self.arguments = arguments
        self.line = paren.line

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_call_expr(self)


