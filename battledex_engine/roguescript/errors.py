"""
Central definitions for all custom errors in RogueScript.
"""

class RogueScriptError(Exception):
    """Base class for all errors in the interpreter."""
    def __init__(self, message, line):
        super().__init__(message)
        self.line = line

    def __str__(self):
        message = super().__str__()
        return f"[Line {self.line}] Error: {message}"

class ParseError(RogueScriptError):
    """Error raised by the Parser."""
    def __init__(self, message, line):
        super().__init__(message, line)

class CompileError(RogueScriptError):
    """Error raised by the Compiler."""
    def __init__(self, message, line):
        super().__init__(message, line)

class RogueScriptRuntimeError(RogueScriptError):
    """Error raised by the VM during execution."""
    def __init__(self, message, line):
        super().__init__(message, line)


