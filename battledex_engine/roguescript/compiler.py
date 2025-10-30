"""
The RogueScript Compiler.

Walks the AST from the Parser and emits bytecode
into a Chunk for the VM to execute.
"""
from __future__ import annotations # Fix for type hints
from . import ast_nodes as ast
from .bytecode import Chunk, OpCode
from .token_types import TokenType
from .lexer import Token # FIX: Import Token directly
from .errors import CompileError
from .function import RogueScriptFunction
from dataclasses import dataclass

@dataclass
class Local:
    """Stores info about a local variable on the compiler's stack."""
    name: Token
    depth: int
    
class Compiler(ast.ExprVisitor, ast.StmtVisitor):
    """
    Implements the Visitor pattern to traverse the AST
    and generate bytecode.
    """
    def __init__(self, parent_compiler: 'Compiler' | None = None, func_type: str = "script"):
        self.chunk: Chunk = Chunk(name="<script>")
        self.locals: list[Local] = []
        self.scope_depth: int = 0
        
        # This setup allows for nested function compilation
        self.parent: 'Compiler' | None = parent_compiler
        
        if func_type == "script":
            self.function: RogueScriptFunction = RogueScriptFunction(name="<script>", arity=0)
        else:
            # The 'name' will be set by visit_def_stmt
            self.function: RogueScriptFunction = RogueScriptFunction(name="", arity=0)
            
        self.chunk = self.function.chunk # All code goes into the function's chunk
        
        if func_type != "script":
            # Add a stack slot for the function itself (for recursion)
            # FIX: Call the correct Token constructor (type, value, line)
            self.locals.append(Local(Token(TokenType.IDENTIFIER, "", 0), 0))
        
    def compile(self, program: ast.Program) -> RogueScriptFunction:
        """
        Main entry point. Compiles a full Program AST node.
        Returns the main <script> function.
        """
        if program is None:
            return None # Parser failed
            
        # We visit all statements in the main <script> body
        try:
            # FIX: Iterate with index to find the last statement
            for i, statement in enumerate(program.statements):
                if i == len(program.statements) - 1 and isinstance(statement, ast.ExpressionStmt):
                    # Special case: last statement is an expression.
                    # Compile it but DON'T pop it. This is the script's
                    # "implicit return" value.
                    statement.expression.accept(self)
                    self._emit_byte(OpCode.OP_RETURN, statement.line)
                else:
                    # Compile all other statements normally
                    statement.accept(self)
            
            if not program.statements:
                # Empty script
                self._emit_return(program.line)
            elif not isinstance(program.statements[-1], ast.ExpressionStmt):
                # Script ends with a non-expression (var, if, etc.)
                # Add an implicit return nil.
                self._emit_return(program.line)
                
            return self.function
            
        except CompileError as e:
            # This should be caught by the VM's interpret() method
            raise e

    def _begin_scope(self):
        self.scope_depth += 1
        
    def _end_scope(self, line: int):
        self.scope_depth -= 1
        
        # Pop all local variables that just went out of scope
        count = 0
        while self.locals and self.locals[-1].depth > self.scope_depth:
            self.locals.pop()
            count += 1
        
        # Emit multiple POPs if needed
        if count > 0:
            # Simple optimization: if we just pop one, use OP_POP
            if count == 1:
                self._emit_byte(OpCode.OP_POP, line)
            else:
                # We could add an OP_POP_N <n> instruction later
                for _ in range(count):
                    self._emit_byte(OpCode.OP_POP, line)


    # --- Emitter Helpers ---

    def _emit_byte(self, byte: OpCode | int, line: int):
        self.chunk.write(byte, line)

    def _emit_bytes(self, byte1: OpCode | int, byte2: int, line: int):
        self._emit_byte(byte1, line)
        self._emit_byte(byte2, line)
        
    def _emit_jump(self, instruction: OpCode, line: int) -> int:
        """Emits a jump instruction with a 2-byte placeholder offset."""
        self._emit_byte(instruction, line)
        self._emit_byte(0xFF, line) # 0xFF as a placeholder
        self._emit_byte(0xFF, line)
        return len(self.chunk.code) - 2 # Return address of the offset

    def _patch_jump(self, offset: int):
        """Goes back and fills in a jump offset."""
        # -2 to adjust for the 2-byte offset itself
        jump = len(self.chunk.code) - offset - 2
        
        if jump > 0xFFFF: # 16-bit limit
            raise CompileError("Jump offset too large (over 65535 bytes).", 0) # Line 0?
            
        # Write the 16-bit offset
        self.chunk.code[offset] = (jump >> 8) & 0xFF
        self.chunk.code[offset + 1] = jump & 0xFF

    def _emit_loop(self, loop_start: int, line: int):
        """Emits OP_LOOP with a 2-byte offset to jump *back*."""
        self._emit_byte(OpCode.OP_LOOP, line)
        
        # +2 to account for the 2-byte offset of OP_LOOP itself
        jump = len(self.chunk.code) - loop_start + 2
        if jump > 0xFFFF:
            raise CompileError("Loop body too large.", line)
            
        self._emit_byte((jump >> 8) & 0xFF, line)
        self._emit_byte(jump & 0xFF, line)

    def _emit_constant(self, value: any, line: int):
        const_index = self.chunk.add_constant(value)
        if const_index > 255:
            # We'd need an OP_PUSH_CONST_LONG (2-byte operand)
            raise CompileError("Too many constants in one chunk.", line)
        self._emit_bytes(OpCode.OP_PUSH_CONST, const_index, line)

    def _emit_return(self, line: int):
        """Emits an implicit or explicit return."""
        self._emit_byte(OpCode.OP_NIL, line) # Implicit return nil
        self._emit_byte(OpCode.OP_RETURN, line)

    # --- Variable Helpers ---

    def _add_local(self, name: Token):
        # Check for re-definition in the *same* scope
        for local in reversed(self.locals):
            if local.depth < self.scope_depth:
                break
            if local.name.value == name.value:
                raise CompileError(f"Already a variable with this name '{name.value}' in this scope.", name.line)
                
        self.locals.append(Local(name, self.scope_depth))

    def _resolve_local(self, name: Token) -> int | None:
        """Find a local variable's stack slot index."""
        for i in range(len(self.locals) - 1, -1, -1):
            if self.locals[i].name.value == name.value:
                return i
        return None # Not found (must be global or undefined)

    def _identifier_constant(self, name: Token) -> int:
        """Adds a variable name to the constant pool."""
        const_index = self.chunk.add_constant(name.value)
        if const_index > 255:
            raise CompileError("Too many global variables.", name.line)
        return const_index

    # --- Statement Visitor Impls ---

    def visit_program_stmt(self, stmt: ast.Program):
        # This is handled by compile()
        pass 

    def visit_expression_stmt(self, stmt: ast.ExpressionStmt):
        stmt.expression.accept(self)
        # Pop the result, since it's not used
        self._emit_byte(OpCode.OP_POP, stmt.line)

    def visit_print_stmt(self, stmt: ast.PrintStmt):
        stmt.expression.accept(self)
        self._emit_byte(OpCode.OP_PRINT, stmt.line)

    def visit_var_decl_stmt(self, stmt: ast.VarDeclStmt):
        # Compile the initializer
        if stmt.initializer:
            stmt.initializer.accept(self)
        else:
            self._emit_byte(OpCode.OP_NIL, stmt.line) # Default to nil
        
        # Define the variable
        if self.scope_depth > 0:
            # It's a local variable.
            self._add_local(stmt.name)
            # The value is already on the stack, so we're done.
            return
        else:
            # It's a global variable.
            const_index = self._identifier_constant(stmt.name)
            self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, const_index, stmt.line)

    def visit_block_stmt(self, stmt: ast.BlockStmt):
        self._begin_scope()
        for statement in stmt.statements:
            statement.accept(self)
        self._end_scope(stmt.line)

    def visit_if_stmt(self, stmt: ast.IfStmt):
        # 1. Compile condition
        stmt.condition.accept(self)
        
        # 2. Emit jump-if-false. Store its offset.
        then_jump_offset = self._emit_jump(OpCode.OP_JUMP_IF_FALSE, stmt.line)
        
        # 3. Pop condition, compile 'then' block
        self._emit_byte(OpCode.OP_POP, stmt.line) # Pop condition
        stmt.then_branch.accept(self)
        
        # 4. Emit 'else' jump (unconditional)
        else_jump_offset = self._emit_jump(OpCode.OP_JUMP, stmt.line)
        
        # 5. Patch the first jump to point *here*
        self._patch_jump(then_jump_offset)
        
        # 6. Pop condition
        self._emit_byte(OpCode.OP_POP, stmt.line) # Pop condition
        
        # 7. Compile 'else' block (if it exists)
        if stmt.else_branch:
            stmt.else_branch.accept(self)
            
        # 8. Patch the 'else' jump to point *here*
        self._patch_jump(else_jump_offset)
        
    def visit_while_stmt(self, stmt: ast.WhileStmt):
        # 1. Mark the loop start (before the condition)
        loop_start = len(self.chunk.code)
        
        # 2. Compile the condition
        stmt.condition.accept(self)
        
        # 3. Emit jump-if-false
        exit_jump_offset = self._emit_jump(OpCode.OP_JUMP_IF_FALSE, stmt.line)
        
        # 4. Pop condition, compile body
        self._emit_byte(OpCode.OP_POP, stmt.line)
        stmt.body.accept(self)
        
        # 5. Emit loop-back
        self._emit_loop(loop_start, stmt.line)
        
        # 6. Patch the exit jump to point *here*
        self._patch_jump(exit_jump_offset)
        self._emit_byte(OpCode.OP_POP, stmt.line) # Pop condition

    def visit_def_stmt(self, stmt: ast.DefStmt):
        """Compiles a function *declaration*."""
        # Create a new compiler for this function
        func_compiler = Compiler(parent_compiler=self, func_type="function")
        func_compiler.function.name = stmt.name.value
        func_compiler.function.arity = len(stmt.params)
        
        # Compile the function body
        func_compiler._begin_scope()
        # Register parameters as locals
        for param in stmt.params:
            func_compiler._add_local(param)
        
        # The body is a BlockStmt, but we visit its *contents*
        for statement in stmt.body.statements:
            statement.accept(func_compiler)
            
        # Finish the function's bytecode
        func_compiler._emit_return(stmt.line)
        
        # Get the compiled function object
        function = func_compiler.function
        
        # Add this new function object to the *outer*
        # compiler's constant pool
        const_index = self.chunk.add_constant(function)
        if const_index > 255:
            raise CompileError("Too many function constants.", stmt.line)
        
        # Emit code to create the function at runtime
        self._emit_bytes(OpCode.OP_PUSH_CONST, const_index, stmt.line)

        # Define the function as a variable in the current scope
        if self.scope_depth > 0:
            self._add_local(stmt.name)
            # The function object is on the stack, just like a local
        else:
            global_index = self._identifier_constant(stmt.name)
            self._emit_bytes(OpCode.OP_DEFINE_GLOBAL, global_index, stmt.line)

    def visit_return_stmt(self, stmt: ast.ReturnStmt):
        if stmt.value:
            stmt.value.accept(self) # Compile the return value
        else:
            self._emit_byte(OpCode.OP_NIL, stmt.line) # Implicit return nil
        
        self._emit_byte(OpCode.OP_RETURN, stmt.line)
        
    # --- Expression Visitor Impls ---

    def visit_binary_expr(self, expr: ast.Binary):
        expr.left.accept(self)
        expr.right.accept(self)
        
        op = expr.operator.type
        if op == TokenType.PLUS:    self._emit_byte(OpCode.OP_ADD, expr.line)
        elif op == TokenType.MINUS: self._emit_byte(OpCode.OP_SUBTRACT, expr.line)
        elif op == TokenType.STAR:  self._emit_byte(OpCode.OP_MULTIPLY, expr.line)
        elif op == TokenType.SLASH: self._emit_byte(OpCode.OP_DIVIDE, expr.line)
        # Comparisons
        elif op == TokenType.EQUAL_EQUAL: self._emit_byte(OpCode.OP_EQUAL, expr.line)
        elif op == TokenType.BANG_EQUAL:
            self._emit_byte(OpCode.OP_EQUAL, expr.line)
            self._emit_byte(OpCode.OP_NOT, expr.line)
        elif op == TokenType.GREATER: self._emit_byte(OpCode.OP_GREATER, expr.line)
        elif op == TokenType.GREATER_EQUAL:
            self._emit_byte(OpCode.OP_LESS, expr.line)
            self._emit_byte(OpCode.OP_NOT, expr.line)
        elif op == TokenType.LESS:  self._emit_byte(OpCode.OP_LESS, expr.line)
        elif op == TokenType.LESS_EQUAL:
            self._emit_byte(OpCode.OP_GREATER, expr.line)
            self._emit_byte(OpCode.OP_NOT, expr.line)
        else:
            raise CompileError(f"Unknown binary operator '{op}'.", expr.line)

    def visit_unary_expr(self, expr: ast.Unary):
        expr.right.accept(self)
        op = expr.operator.type
        if op == TokenType.MINUS:   self._emit_byte(OpCode.OP_NEGATE, expr.line)
        elif op == TokenType.BANG:  self._emit_byte(OpCode.OP_NOT, expr.line)
        else:
            raise CompileError(f"Unknown unary operator '{op}'.", expr.line)

    def visit_literal_expr(self, expr: ast.Literal):
        val = expr.value
        if val is None: self._emit_byte(OpCode.OP_NIL, expr.line)
        elif val is True: self._emit_byte(OpCode.OP_TRUE, expr.line)
        elif val is False: self._emit_byte(OpCode.OP_FALSE, expr.line)
        else:
            self._emit_constant(expr.value, expr.line)

    def visit_grouping_expr(self, expr: ast.Grouping):
        expr.expression.accept(self)
        
    def visit_variable_expr(self, expr: ast.VariableExpr):
        """Emits code to get a variable's value."""
        # Try to find it as a local
        local_index = self._resolve_local(expr.name)
        if local_index is not None:
            self._emit_bytes(OpCode.OP_GET_LOCAL, local_index, expr.line)
        else:
            # Assume it's global
            const_index = self._identifier_constant(expr.name)
            self._emit_bytes(OpCode.OP_GET_GLOBAL, const_index, expr.line)

    def visit_assign_expr(self, expr: ast.AssignExpr):
        """Emits code to set a variable's value."""
        # Compile the value first
        expr.value.accept(self)
        
        # Try to find it as a local
        local_index = self._resolve_local(expr.name)
        if local_index is not None:
            self._emit_bytes(OpCode.OP_SET_LOCAL, local_index, expr.line)
        else:
            # Assume it's global
            const_index = self._identifier_constant(expr.name)
            self._emit_bytes(OpCode.OP_SET_GLOBAL, const_index, expr.line)
            
    def visit_logical_expr(self, expr: ast.LogicalExpr):
        """Compile 'and' or 'or' with short-circuiting."""
        op = expr.operator.type
        
        # Compile left side
        expr.left.accept(self)
        
        if op == TokenType.OR:
            # If left is TRUE, we skip the right.
            # We jump *over* the pop and the right-side code
            else_jump = self._emit_jump(OpCode.OP_JUMP_IF_FALSE, expr.line)
            end_jump = self._emit_jump(OpCode.OP_JUMP, expr.line)
            
            self._patch_jump(else_jump)
            self._emit_byte(OpCode.OP_POP, expr.line) # Pop left
            
            expr.right.accept(self)
            self._patch_jump(end_jump)
            
        elif op == TokenType.AND:
            # If left is FALSE, we skip the right.
            end_jump = self._emit_jump(OpCode.OP_JUMP_IF_FALSE, expr.line)
            
            self._emit_byte(OpCode.OP_POP, expr.line) # Pop left
            expr.right.accept(self) # Compile right
            
            self._patch_jump(end_jump)
            
    def visit_call_expr(self, expr: ast.CallExpr):
        # 1. Compile the function itself (e.g., the variable 'my_func')
        expr.callee.accept(self)
        
        # 2. Compile all arguments
        for arg in expr.arguments:
            arg.accept(self)
            
        # 3. Emit the call instruction with arity
        self._emit_bytes(OpCode.OP_CALL, len(expr.arguments), expr.line)


