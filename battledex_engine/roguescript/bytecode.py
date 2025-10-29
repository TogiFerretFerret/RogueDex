"""
Defines the instruction set (OpCodes) and the
Chunk class that stores bytecode and constants.
"""

from enum import Enum, auto
from dataclasses import dataclass, field

class OpCode(Enum):
    """The set of instructions our VM understands."""
    OP_RETURN = auto()       # Return from the current function/script.
    OP_PUSH_CONST = auto()   # Push a value from the constant pool.
    
    # Binary Arithmetic
    OP_ADD = auto()
    OP_SUBTRACT = auto()
    OP_MULTIPLY = auto()
    OP_DIVIDE = auto()
    
    # Unary
    OP_NEGATE = auto()       # e.g., -5
    OP_NOT = auto()          # e.g., !True

@dataclass
class Chunk:
    """
    A container for a sequence of bytecode instructions.
    It also stores the constant values (e.g., numbers, strings)
    that the bytecode refers to.
    """
    code: bytearray = field(default_factory=bytearray)
    constants: list[any] = field(default_factory=list)
    lines: list[int] = field(default_factory=list)

    def write(self, byte: OpCode | int, line: int):
        """Appends a byte (or OpCode) to the chunk."""
        if isinstance(byte, OpCode):
            self.code.append(byte.value)
        else:
            self.code.append(byte)
        self.lines.append(line)

    def add_constant(self, value: any) -> int:
        """
        Adds a value to the constant pool.
        Returns the index of that value.
        """
        self.constants.append(value)
        # Return the index of the constant we just added
        return len(self.constants) - 1

