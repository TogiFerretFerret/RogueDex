"""
Custom exceptions for the RogueScript interpreter.
"""

class RogueScriptError(Exception):
    """Base class for all RogueScript errors."""
    def __init__(self, message, line):
        super().__init__(f"[Line {line}] {message}")
        self.line = line

class ParseError(RogueScriptError):
    """Raised when the parser encounters a syntax error."""
    pass

