"""
Custom exceptions for the RogueScript interpreter.
"""

class RogueScriptError(Exception):
    """Base class for all RogueScript errors."""
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
    
    def __str__(self):
        if self.line:
            return f"[Line {self.line}] Error: {self.message}"
        return f"Error: {self.message}"

class ParseError(RogueScriptError):
    """Raised when the parser encounters a syntax error."""
    pass

class RogueScriptRuntimeError(RogueScriptError):
    """Raised by the VM during execution."""
    pass


