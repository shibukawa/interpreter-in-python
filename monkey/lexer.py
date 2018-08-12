import re
import typing
from . import token


class Lexer:
    _input: str
    _position: int
    _read_position: int
    _ch: typing.Optional[str]

    def __init__(self, input: str) -> None:
        self._input = input
        self._position = 0
        self._read_position = 0
        self._ch = None
        self._read_char()

    def next_token(self) -> token.Token:
        self._skip_whitespace()

        if self._ch == "=":
            if self._peek_char() == "=":
                ch = self._ch
                self._read_char()
                tok = token.Token(token.EQ, ch + self._ch)
            else:
                tok = token.Token(token.ASSIGN, self._ch)
        elif self._ch == ";":
            tok = token.Token(token.SEMICOLON, self._ch)
        elif self._ch == "(":
            tok = token.Token(token.LPAREN, self._ch)
        elif self._ch == ")":
            tok = token.Token(token.RPAREN, self._ch)
        elif self._ch == "{":
            tok = token.Token(token.LBRACE, self._ch)
        elif self._ch == "}":
            tok = token.Token(token.RBRACE, self._ch)
        elif self._ch == ",":
            tok = token.Token(token.COMMA, self._ch)
        elif self._ch == "+":
            tok = token.Token(token.PLUS, self._ch)
        elif self._ch == "-":
            tok = token.Token(token.MINUS, self._ch)
        elif self._ch == "!":
            if self._peek_char() == "=":
                ch = self._ch
                self._read_char()
                tok = token.Token(token.NOT_EQ, ch + self._ch)
            else:
                tok = token.Token(token.BANG, self._ch)
        elif self._ch == "/":
            tok = token.Token(token.SLASH, self._ch)
        elif self._ch == "*":
            tok = token.Token(token.ASTERISK, self._ch)
        elif self._ch == "<":
            tok = token.Token(token.LT, self._ch)
        elif self._ch == ">":
            tok = token.Token(token.GT, self._ch)
        elif self._ch is None:
            tok = token.Token(token.EOF, None)
        else:
            if is_letter(self._ch):
                literal = self._read_identifier()
                return token.Token(token.lookup_ident(literal), literal)
            elif is_digit(self._ch):
                literal = self._read_identifier()
                return token.Token(token.INT, self._read_number())
            else:
                tok = token.Token(token.ILLEGAL, self._ch)
        self._read_char()
        return tok
    
    def _read_char(self) -> None:
        if self._read_position >= len(self._input):
            self._ch = None
        else:
            self._ch = self._input[self._read_position]
        self._position = self._read_position
        self._read_position += 1
    
    def _peek_char(self) -> typing.Optional[str]:
        if self._read_position >= len(self._input):
            return None
        else:
            return self._input[self._read_position]
    
    def _read_identifier(self) -> str:
        pos = self._position
        while is_letter(self._ch):
            self._read_char()
        return self._input[pos:self._position]
    
    def _read_number(self) -> str:
        pos = self._position
        while is_digit(self._ch):
            self._read_char()
        return self._input[pos:self._position]

    def _skip_whitespace(self) -> None:
        while self._ch is not None and self._ch in " \r\n\t":
            self._read_char()


letter_pattern = re.compile(r"[a-zA-Z_]")


def is_letter(ch: typing.Optional[str]) -> bool:
    if ch is None:
        return False
    return bool(letter_pattern.match(ch))


def is_digit(ch: typing.Optional[str]) -> bool:
    if ch is None:
        return False
    return ch in "0123456789"
