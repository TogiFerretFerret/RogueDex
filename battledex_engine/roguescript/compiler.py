"""
The RogueScript Compiler.

Walks the AST from the Parser and emits bytecode
into a Chunk for the VM to execute.
"""

from . import ast_nodes as ast
from .bytecode import Chunk, OpCode
from .token_types import TokenType
from .errors import RogueScriptError

class CompileError(RogueScriptError):
    pass

class Compiler(ast.ExprVisitor, ast.StmtVisitor):
    """
    Implements the Visitor pattern to traverse the AST
    and generate bytecode.
    """
    def __init__(self):
        self.chunk = Chunk()

    def compile(self, program: ast.Program) -> Chunk:
        """
        Main entry point. Compiles a full Program AST node.
        Returns a Chunk of bytecode.
        """
        try:
            for statement in program.statements:
                statement.accept(self)
            return self.chunk
        except RogueScriptError as e:
            # We don't have great error reporting yet, but
            # this will at least stop the compile.
            print(f"Compile Error: {e}")
            return None

    def _current_chunk(self) -> Chunk:
        """In the future, this will point to a function's chunk."""
        return self.chunk

    # --- Emit Helper Methods ---

    def _emit_byte(self, byte: OpCode | int, line: int):
        """Writes a single byte to the chunk."""
        self._current_chunk().write(byte, line)

    def _emit_bytes(self, byte1: OpCode | int, byte2: int, line: int):
        """Writes two bytes to the chunk."""
        self._emit_byte(byte1, line)
        self._emit_byte(byte2, line)

    def _emit_constant(self, value: any, line: int):
        """Adds a constant and emits OP_PUSH_CONST."""
        const_index = self._current_chunk().add_constant(value)
        
        # We can only support 256 constants right now.
        if const_index > 255:
            raise CompileError("Too many constants in one chunk.", line)
            
        self._emit_bytes(OpCode.OP_PUSH_CONST, const_index, line)

    def _emit_return(self, line: int):
        """Emits the OP_RETURN instruction."""
        self._emit_byte(OpCode.OP_RETURN, line)

    # --- Statement Visitor Impls ---

    def visit_program_stmt(self, stmt: ast.Program):
        # Should be called via compile()
        pass 

    def visit_expression_stmt(self, stmt: ast.ExpressionStmt):
        # Evaluate the expression, leaving its value on the stack
        stmt.expression.accept(self)
        # For now, we'll just return the value of the expression.
        # Later, we might just pop it.
        self._emit_return(stmt.line)

    # --- Expression Visitor Impls ---

    def visit_binary_expr(self, expr: ast.Binary):
        # Compile left and right operands
        expr.left.accept(self)
        expr.right.accept(self)
        
        # Emit the operator instruction
        op = expr.operator.type
        if op == TokenType.PLUS:    self._emit_byte(OpCode.OP_ADD, expr.operator.line)
        elif op == TokenType.MINUS: self._emit_byte(OpCode.OP_SUBTRACT, expr.operator.line)
        elif op == TokenType.STAR:  self._emit_byte(OpCode.OP_MULTIPLY, expr.operator.line)
        elif op == TokenType.SLASH: self._emit_byte(OpCode.OP_DIVIDE, expr.operator.line)
        else:
            # This should be caught by the parser, but good to have.
            raise CompileError(f"Unknown binary operator '{op}'.", expr.operator.line)

    def visit_unary_expr(self, expr: ast.Unary):
        # Compile the operand
        expr.right.accept(self)
        
        # Emit the operator instruction
        op = expr.operator.type
        if op == TokenType.MINUS:   self._emit_byte(OpCode.OP_NEGATE, expr.operator.line)
        elif op == TokenType.BANG:  self._emit_byte(OpCode.OP_NOT, expr.operator.line)
        else:
            raise CompileError(f"Unknown unary operator '{op}'.", expr.operator.line)

    def visit_literal_expr(self, expr: ast.Literal):
        # Add the literal value to the constant pool
        self._emit_constant(expr.value, expr.line)

    def visit_grouping_expr(self, expr: ast.Grouping):
        # Just compile the expression inside the parens
        expr.expression.accept(self)

