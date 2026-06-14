"""JavaScript lexer - tokenizes source code into tokens."""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from project.errors import LexerError


class TokenType(Enum):
    # Keywords
    LET = auto()
    CONST = auto()
    VAR = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    FUNCTION = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    SWITCH = auto()
    CASE = auto()
    DEFAULT = auto()
    TYPEOF = auto()
    OF = auto()
    IN = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    UNDEFINED = auto()
    NEW = auto()

    # Literals
    NUMBER = auto()
    STRING = auto()
    TEMPLATE = auto()

    # Identifiers
    IDENTIFIER = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    STAR_STAR = auto()
    EQ = auto()
    EQ_EQ = auto()
    EQ_EQ_EQ = auto()
    BANG = auto()
    BANG_EQ = auto()
    BANG_EQ_EQ = auto()
    LT = auto()
    LT_EQ = auto()
    GT = auto()
    GT_EQ = auto()
    AMP_AMP = auto()
    PIPE_PIPE = auto()
    PLUS_PLUS = auto()
    MINUS_MINUS = auto()
    PLUS_EQ = auto()
    MINUS_EQ = auto()
    STAR_EQ = auto()
    SLASH_EQ = auto()
    PERCENT_EQ = auto()
    ARROW = auto()
    SPREAD = auto()

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    DOT = auto()
    COMMA = auto()
    SEMICOLON = auto()
    COLON = auto()
    QUESTION = auto()

    # Special
    EOF = auto()


KEYWORDS = {
    "let": TokenType.LET,
    "const": TokenType.CONST,
    "var": TokenType.VAR,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "function": TokenType.FUNCTION,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "switch": TokenType.SWITCH,
    "case": TokenType.CASE,
    "default": TokenType.DEFAULT,
    "typeof": TokenType.TYPEOF,
    "of": TokenType.OF,
    "in": TokenType.IN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "undefined": TokenType.UNDEFINED,
    "new": TokenType.NEW,
}


@dataclass
class Token:
    type: TokenType
    value: any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class Lexer:
    """Tokenize JavaScript source code."""

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        while self.pos < self.length:
            self._skip_whitespace()
            if self.pos >= self.length:
                break
            self._skip_comment()
            if self.pos >= self.length:
                break
            if self._peek() in " \t\n\r":
                continue
            tok = self._next_token()
            if tok:
                self.tokens.append(tok)
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx >= self.length:
            return "\0"
        return self.source[idx]

    def _advance(self, count: int = 1) -> str:
        ch = self.source[self.pos : self.pos + count]
        for c in ch:
            if c == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        self.pos += count
        return ch

    def _make_token(self, tt: TokenType, value) -> Token:
        return Token(tt, value, self.line, self.column)

    def _skip_whitespace(self):
        while self.pos < self.length and self._peek() in " \t\n\r":
            self._advance()

    def _skip_comment(self):
        if self._peek() == "/" and self._peek(1) == "/":
            while self.pos < self.length and self._peek() != "\n":
                self._advance()
        elif self._peek() == "/" and self._peek(1) == "*":
            self._advance(2)
            while self.pos < self.length:
                if self._peek() == "*" and self._peek(1) == "/":
                    self._advance(2)
                    return
                self._advance()
            raise LexerError("Unterminated block comment", self.line, self.column)

    def _next_token(self) -> Optional[Token]:
        start_line = self.line
        start_col = self.column
        ch = self._peek()

        # String literals
        if ch in ('"', "'"):
            return self._read_string(ch)
        if ch == "`":
            return self._read_template()

        # Numbers
        if ch.isdigit() or (ch == "." and self._peek(1).isdigit()):
            return self._read_number()

        # Identifiers and keywords
        if ch.isalpha() or ch == "_" or ch == "$":
            return self._read_identifier()

        # Three-char operators
        three = self.source[self.pos : self.pos + 3]
        if three == "===":
            self._advance(3)
            return Token(TokenType.EQ_EQ_EQ, "===", start_line, start_col)
        if three == "!==":
            self._advance(3)
            return Token(TokenType.BANG_EQ_EQ, "!==", start_line, start_col)

        # Two-char operators
        two = self.source[self.pos : self.pos + 2]
        two_map = {
            "==": TokenType.EQ_EQ,
            "!=": TokenType.BANG_EQ,
            "<=": TokenType.LT_EQ,
            ">=": TokenType.GT_EQ,
            "&&": TokenType.AMP_AMP,
            "||": TokenType.PIPE_PIPE,
            "++": TokenType.PLUS_PLUS,
            "--": TokenType.MINUS_MINUS,
            "+=": TokenType.PLUS_EQ,
            "-=": TokenType.MINUS_EQ,
            "*=": TokenType.STAR_EQ,
            "/=": TokenType.SLASH_EQ,
            "%=": TokenType.PERCENT_EQ,
            "**": TokenType.STAR_STAR,
            "=>": TokenType.ARROW,
            "...": None,  # handled separately
        }
        if two in two_map and two != "...":
            self._advance(2)
            return Token(two_map[two], two, start_line, start_col)

        if three == "...":
            self._advance(3)
            return Token(TokenType.SPREAD, "...", start_line, start_col)

        # Single-char tokens
        single_map = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "=": TokenType.EQ,
            "!": TokenType.BANG,
            "<": TokenType.LT,
            ">": TokenType.GT,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ".": TokenType.DOT,
            ",": TokenType.COMMA,
            ";": TokenType.SEMICOLON,
            ":": TokenType.COLON,
            "?": TokenType.QUESTION,
        }
        if ch in single_map:
            self._advance()
            return Token(single_map[ch], ch, start_line, start_col)

        raise LexerError(f"Unexpected character '{ch}'", start_line, start_col)

    def _read_string(self, quote: str) -> Token:
        start_line = self.line
        start_col = self.column
        self._advance()  # opening quote
        chars = []
        while self.pos < self.length:
            ch = self._peek()
            if ch == quote:
                self._advance()
                return Token(TokenType.STRING, "".join(chars), start_line, start_col)
            if ch == "\\":
                self._advance()
                esc = self._peek()
                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "\\": "\\",
                    "'": "'",
                    '"': '"',
                }
                chars.append(escape_map.get(esc, esc))
                self._advance()
            elif ch == "\n":
                raise LexerError("Unterminated string literal", start_line, start_col)
            else:
                chars.append(ch)
                self._advance()
        raise LexerError("Unterminated string literal", start_line, start_col)

    def _read_template(self) -> Token:
        start_line = self.line
        start_col = self.column
        self._advance()  # opening backtick
        chars = []
        while self.pos < self.length:
            ch = self._peek()
            if ch == "`":
                self._advance()
                return Token(TokenType.TEMPLATE, "".join(chars), start_line, start_col)
            if ch == "\\":
                self._advance()
                esc = self._peek()
                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "`": "`",
                    "\\": "\\",
                    "$": "$",
                }
                chars.append(escape_map.get(esc, esc))
                self._advance()
            else:
                chars.append(ch)
                self._advance()
        raise LexerError("Unterminated template literal", start_line, start_col)

    def _read_number(self) -> Token:
        start_line = self.line
        start_col = self.column
        start = self.pos
        if self._peek() == "0" and self._peek(1) in "xX":
            self._advance(2)
            while self.pos < self.length and self._peek() in "0123456789abcdefABCDEF":
                self._advance()
            num_str = self.source[start : self.pos]
            return Token(TokenType.NUMBER, int(num_str, 16), start_line, start_col)

        has_dot = False
        while self.pos < self.length:
            ch = self._peek()
            if ch.isdigit():
                self._advance()
            elif ch == "." and not has_dot:
                has_dot = True
                self._advance()
            else:
                break
        num_str = self.source[start : self.pos]
        value = float(num_str) if "." in num_str else int(num_str)
        return Token(TokenType.NUMBER, value, start_line, start_col)

    def _read_identifier(self) -> Token:
        start_line = self.line
        start_col = self.column
        start = self.pos
        while self.pos < self.length:
            ch = self._peek()
            if ch.isalnum() or ch in "_$":
                self._advance()
            else:
                break
        name = self.source[start : self.pos]
        if name in KEYWORDS:
            return Token(KEYWORDS[name], name, start_line, start_col)
        return Token(TokenType.IDENTIFIER, name, start_line, start_col)
