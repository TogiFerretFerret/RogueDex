"""
Utility class to print an AST for debugging.
Implements the Visitor pattern.
"""

from . import ast_nodes as ast

class ASTPrinter(ast.ExprVisitor, ast.StmtVisitor):

    def print_program(self, program: ast.Program):
        if not program:
            return "()"
        return program.accept(self)

    def _parenthesize(self, name, *exprs):
        parts = [f"({name}"]
        for expr in exprs:
            if isinstance(expr, ast.Expr) or isinstance(expr, ast.Stmt):
                parts.append(expr.accept(self))
            elif isinstance(expr, ast.Token):
                parts.append(expr.value)
            elif isinstance(expr, list): # For block statements
                for stmt in expr:
                    parts.append(stmt.accept(self))
            elif expr is None:
                parts.append("nil")
            else:
                parts.append(str(expr))
        parts.append(")")
        return " ".join(parts)

    # --- Statement Visitors ---

    def visit_program_stmt(self, stmt: ast.Program):
        return self._parenthesize("program", *stmt.statements)

    def visit_expression_stmt(self, stmt: ast.ExpressionStmt):
        return self._parenthesize("stmt", stmt.expression)

    def visit_print_stmt(self, stmt: ast.PrintStmt):
        return self._parenthesize("print", stmt.expression)

    def visit_var_decl_stmt(self, stmt: ast.VarDeclStmt):
        return self._parenthesize("var", stmt.name, "=", stmt.initializer)

    def visit_block_stmt(self, stmt: ast.BlockStmt):
        return self._parenthesize("block", *stmt.statements)

    def visit_if_stmt(self, stmt: ast.IfStmt):
        if stmt.else_branch:
            return self._parenthesize("if", stmt.condition, stmt.then_branch, f"else=({stmt.else_branch.accept(self)})")
        return self._parenthesize("if", stmt.condition, stmt.then_branch, "else=None")
        
    def visit_while_stmt(self, stmt: ast.WhileStmt):
        return self._parenthesize("while", stmt.condition, stmt.body)

    def visit_def_stmt(self, stmt: ast.DefStmt):
        param_names = ", ".join([p.value for p in stmt.params])
        return f"(def {stmt.name.value}({param_names}) {stmt.body.accept(self)})"

    def visit_return_stmt(self, stmt: ast.ReturnStmt):
        return self._parenthesize("return", stmt.value)

    # --- Expression Visitors ---

    def visit_binary_expr(self, expr: ast.Binary):
        return self._parenthesize(expr.operator.value, expr.left, expr.right)

    def visit_unary_expr(self, expr: ast.Unary):
        return self._parenthesize(expr.operator.value, expr.right)

    def visit_literal_expr(self, expr: ast.Literal):
        if expr.value is None: return "nil"
        if isinstance(expr.value, str): return f'"{expr.value}"'
        if isinstance(expr.value, bool): return "True" if expr.value else "False"
        return str(expr.value)

    def visit_grouping_expr(self, expr: ast.Grouping):
        return self._parenthesize("group", expr.expression)

    def visit_variable_expr(self, expr: ast.VariableExpr):
        return str(expr.name.value)
        
    def visit_assign_expr(self, expr: ast.AssignExpr):
        return self._parenthesize("assign", expr.name.value, "=", expr.value)

    def visit_logical_expr(self, expr: ast.LogicalExpr):
        return self._parenthesize(expr.operator.value, expr.left, expr.right)

    def visit_call_expr(self, expr: ast.CallExpr):
        return self._parenthesize("call", expr.callee, *expr.arguments)


