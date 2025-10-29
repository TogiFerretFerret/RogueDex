"""
Implements the AST Visitor pattern to print a tree in a
Lisp-like (S-expression) format.

This is our primary tool for debugging the parser.
"""

from .ast_nodes import Expr, ExprVisitor, Stmt, StmtVisitor, Program, ExpressionStmt, Binary, Unary, Literal, Grouping

class ASTPrinter(ExprVisitor, StmtVisitor):
    
    def print_program(self, program: Program) -> str:
        """Main entry point."""
        try:
            results = []
            for stmt in program.statements:
                results.append(stmt.accept(self))
            return "\n".join(results)
        except Exception as e:
            return f"ASTPrinter Error: {e}"

    # --- Statement Visitors ---
    
    def visit_program_stmt(self, stmt: Program):
        # This is handled by print_program, but we could add (program ...)
        pass # Should be called via print_program

    def visit_expression_stmt(self, stmt: ExpressionStmt):
        # (stmt (expr...))
        return self._parenthesize("stmt", stmt.expression)

    # --- Expression Visitors ---

    def visit_binary_expr(self, expr: Binary):
        # (op left right)
        return self._parenthesize(expr.operator.value, expr.left, expr.right)

    def visit_unary_expr(self, expr: Unary):
        # (op right)
        return self._parenthesize(expr.operator.value, expr.right)

    def visit_literal_expr(self, expr: Literal):
        if expr.value is None:
            return "nil"
        if isinstance(expr.value, bool):
            return str(expr.value)
        return str(expr.value)

    def visit_grouping_expr(self, expr: Grouping):
        # (group expr)
        return self._parenthesize("group", expr.expression)

    # --- Helper Method ---

    def _parenthesize(self, name: str, *exprs: Expr) -> str:
        """
        Wraps an expression and its sub-expressions in parentheses.
        e.g., (name expr1_str expr2_str)
        """
        parts = [f"({name}"]
        for expr in exprs:
            # Recursively call accept to print sub-expressions
            parts.append(" " + expr.accept(self))
        parts.append(")")
        return "".join(parts)

