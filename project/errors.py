"""Error types for the JavaScript interpreter."""


class JSError(Exception):
    """Base error for all interpreter errors."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format())

    def format(self) -> str:
        if self.line:
            return f"Error at line {self.line}, column {self.column}: {self.message}"
        return f"Error: {self.message}"


class LexerError(JSError):
    """Lexical analysis error."""


class ParserError(JSError):
    """Syntax parsing error."""


class RuntimeError(JSError):
    """Runtime execution error."""


class ReturnSignal(Exception):
    """Internal control flow for return statements."""

    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    """Internal control flow for break statements."""


class ContinueSignal(Exception):
    """Internal control flow for continue statements."""
