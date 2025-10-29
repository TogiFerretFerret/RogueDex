"""
Defines the instruction set (OpCodes) and the
Chunk class that stores bytecode and constants.
"""

from enum import IntEnum # Use IntEnum for direct byte conversion
from dataclasses import dataclass, field

class OpCode(IntEnum):
    """The set of instructions our VM understands."""
    
    # --- Stack Operations ---
    OP_PUSH_CONST = 0   # Push a value from the constant pool.
    OP_NIL = 1
    OP_TRUE = 2
    OP_FALSE = 3
    OP_POP = 4            # Pop the top value from the stack.
    
    # --- Variable Operations ---
    OP_DEFINE_GLOBAL = 5
    OP_GET_GLOBAL = 6
    OP_SET_GLOBAL = 7
    OP_GET_LOCAL = 8
    OP_SET_LOCAL = 9
    
    # --- Binary Arithmetic & Comparison ---
    OP_ADD = 10
    OP_SUBTRACT = 11
    OP_MULTIPLY = 12
    OP_DIVIDE = 13
    OP_EQUAL = 14         # ==
    OP_GREATER = 15       # >
    OP_LESS = 16          # <
    
    # --- Unary ---
    OP_NEGATE = 17        # e.g., -5
    OP_NOT = 18           # e.g., !True

    # --- Control Flow ---
    OP_JUMP = 19            # Unconditional jump
    OP_JUMP_IF_FALSE = 20   # Jump if top of stack is falsy
    OP_LOOP = 21            # Unconditional jump *backwards*
    
    # --- Functions & Statements ---
    OP_CALL = 22
    OP_RETURN = 23
    OP_PRINT = 24


@dataclass
class Chunk:
    """
    A container for a sequence of bytecode instructions.
    It also stores the constant values (e.g., numbers, strings)
    that the bytecode refers to.
    """
    name: str = "<script>" # For debugging
    code: bytearray = field(default_factory=bytearray)
    constants: list[any] = field(default_factory=list)
    lines: list[int] = field(default_factory=list)

    def write(self, byte: OpCode | int, line: int):
        """Appends a byte (or OpCode) to the chunk."""
        self.code.append(int(byte))
        self.lines.append(line)

    def add_constant(self, value: any) -> int:
        """
        Adds a value to the constant pool.
        Returns the index of that value.
        """
        self.constants.append(value)
        # Return the index of the constant we just added
        return len(self.constants) - 1


