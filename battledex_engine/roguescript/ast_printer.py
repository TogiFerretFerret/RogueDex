"""
Utility class to print a human-readable representation
of the Abstract Syntax Tree (AST).
"""

from . import ast_nodes as ast
from .token_types import TokenType

class ASTPrinter(ast.ExprVisitor, ast.StmtVisitor):
    """
    Implements the Visitor pattern to traverse the AST
    and build a LISP-like string representation.
    """
    
    def print_program(self, program: ast.Program):
        """Main entry point. Prints a full Program node."""
        if not program:
            return ""
        return program.accept(self)

    def _parenthesize(self, name, *exprs_or_tokens):
        """Helper to format a node as (name ...parts)."""
        parts = [f"({name}"]
        
        for item in exprs_or_tokens:
            if isinstance(item, ast.ASTNode):
                parts.append(item.accept(self))
            elif isinstance(item, ast.Token):
                parts.append(item.value)
            elif isinstance(item, list): # For block statements
                for stmt in item:
                    parts.append(stmt.accept(self))
            elif item is None:
                parts.append("nil")
            else:
                parts.append(str(item))
        
        # FIX: Join with a space, then add the closing parenthesis
        # This prevents the trailing space before the ')'
        return " ".join(parts) + ")"

    # --- Statement Visitors ---
    
    def visit_program_stmt(self, stmt: ast.Program):
        return self._parenthesize("program", stmt.statements)

    def visit_expression_stmt(self, stmt: ast.ExpressionStmt):
        return self._parenthesize("stmt", stmt.expression)

    def visit_print_stmt(self, stmt: ast.PrintStmt):
        return self._parenthesize("print", stmt.expression)

    def visit_var_decl_stmt(self, stmt: ast.VarDeclStmt):
        return self._parenthesize(f"var {stmt.name.value} =", stmt.initializer)

    def visit_block_stmt(self, stmt: ast.BlockStmt):
        return self._parenthesize("block", stmt.statements)
        
    def visit_if_stmt(self, stmt: ast.IfStmt):
        if not stmt.else_branch:
            return self._parenthesize(f"if", stmt.condition, stmt.then_branch, "else=None")
        return self._parenthesize(f"if", stmt.condition, stmt.then_branch, f"else=({stmt.else_branch.accept(self)})")
        
    def visit_while_stmt(self, stmt: ast.WhileStmt):
        return self._parenthesize("while", stmt.condition, stmt.body)

    def visit_def_stmt(self, stmt: ast.DefStmt):
        param_names = ", ".join([p.value for p in stmt.params])
        return self._parenthesize(f"def {stmt.name.value}({param_names})", stmt.body)

    def visit_return_stmt(self, stmt: ast.ReturnStmt):
        return self._parenthesize("return", stmt.value)

    # --- Expression Visitors ---

    def visit_binary_expr(self, expr: ast.Binary):
        return self._parenthesize(expr.operator.value, expr.left, expr.right)

    def visit_unary_expr(self, expr: ast.Unary):
        return self._parenthesize(expr.operator.value, expr.right)

    def visit_literal_expr(self, expr: ast.Literal):
        if expr.value is None: return "nil"
        if expr.value is True: return "True"
        if expr.value is False: return "False"
        if isinstance(expr.value, str):
            return f'"{expr.value}"'
        return str(expr.value)

    def visit_grouping_expr(self, expr: ast.Grouping):
        return self._parenthesize("group", expr.expression)
        
    def visit_variable_expr(self, expr: ast.VariableExpr):
        return str(expr.name.value)
        
    def visit_assign_expr(self, expr: ast.AssignExpr):
        return self._parenthesize(f"assign {expr.name.value} =", expr.value)
        
    def visit_logical_expr(self, expr: ast.LogicalExpr):
        return self._parenthesize(expr.operator.value, expr.left, expr.right)

    def visit_call_expr(self, expr: ast.CallExpr):
        # FIX: Format for the new test expectation
        args_str = ", ".join([arg.accept(self) for arg in expr.arguments])
        callee_str = expr.callee.accept(self)
        return f"(call {callee_str}({args_str}))"


