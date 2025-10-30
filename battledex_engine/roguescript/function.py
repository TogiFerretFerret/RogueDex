"""
New file to break circular dependencies.

Defines the data containers for user-defined functions
(RogueScriptFunction) and native Python functions (NativeFunction).
"""

from dataclasses import dataclass, field
from .bytecode import Chunk

@dataclass
class RogueScriptFunction:
    """A user-defined function compiled to bytecode."""
    name: str
    arity: int # Number of parameters
    chunk: Chunk = field(default_factory=Chunk)
    
    def __repr__(self):
        return f"<fn {self.name}>"

@dataclass
class NativeFunction:
    """A wrapper for a Python function exposed to the VM."""
    name: str
    callable: callable
    
    def __repr__(self):
        return f"<native fn {self.name}>"

