import typing
import dataclasses


@dataclasses.dataclass(frozen=True)
class Token:
    type: str
    literal: typing.Union[str, None]


ILLEGAL = "ILLEGAL"
EOF = "EOF"

# identifier
IDENT = "IDENT"
INT = "INT"

# operator
ASSIGN = "="
PLUS = "+"
MINUS = "-"
BANG = "!"
ASTERISK = "*"
SLASH = "/"

LT = "<"
GT = ">"

EQ = "=="
NOT_EQ = "!="

# delimiter
COMMA = ","
SEMICOLON = ";"

LPAREN = "("
RPAREN = ")"
LBRACE = "{"
RBRACE = "}"

# keywords
FUNCTION = "FUNCTION"
LET = "LET"
TRUE = "TRUE"
FALSE = "FALSE"
IF = "IF"
ELSE = "ELSE"
RETURN = "RETURN"

_keywords = {
    "fn": FUNCTION,
    "let": LET,
    "true": TRUE,
    "false": FALSE,
    "if": IF,
    "else": ELSE,
    "return": RETURN
}


def lookup_ident(ident):
    return _keywords.get(ident, IDENT)


def null() -> Token:
    return Token(ILLEGAL, "")