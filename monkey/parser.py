from typing import List, Dict, Optional, Callable, cast
from . import token
from . import lexer
from . import ast

PrefixParseFn = Callable[[], ast.Expression]
InfixParseFn = Callable[[ast.Expression], ast.Expression]


LOWEST = 10
EQUALS = 20
LESSGREATER = 30
SUM = 40
PRODUCT = 50
PREFIX = 60
CALL = 70

_precedances: Dict[str, int] = {
    token.EQ: EQUALS,
    token.NOT_EQ: EQUALS,
    token.LT: LESSGREATER,
    token.GT: LESSGREATER,
    token.PLUS: SUM,
    token.MINUS: SUM,
    token.SLASH: PRODUCT,
    token.ASTERISK: PRODUCT,
    token.LPAREN: CALL,
}


class Parser:
    _lexer: lexer.Lexer
    _errors: List[str]

    _cur_token: token.Token
    _peek_token: token.Token

    _prefix_parse_fns: Dict[str, PrefixParseFn]
    _infix_parse_fns: Dict[str, InfixParseFn]

    def __init__(self, lexer: lexer.Lexer) -> None:
        self._lexer = lexer
        self._cur_token = token.null()
        self._peek_token = token.null()
        self._errors = []
        self._prefix_parse_fns = {
            token.IDENT: self._parse_identifier,
            token.INT: self._parse_integer_literal,
            token.BANG: self._parse_prefix_expression,
            token.MINUS: self._parse_prefix_expression,
            token.TRUE: self._parse_boolean,
            token.FALSE: self._parse_boolean,
            token.LPAREN: self._parse_grouped_expression,
            token.IF: self._parse_if_expression,
            token.FUNCTION: self._parse_function_literal,
        }
        self._infix_parse_fns = {
            token.PLUS: self._parse_infix_expression,
            token.MINUS: self._parse_infix_expression,
            token.SLASH: self._parse_infix_expression,
            token.ASTERISK: self._parse_infix_expression,
            token.EQ: self._parse_infix_expression,
            token.NOT_EQ: self._parse_infix_expression,
            token.LT: self._parse_infix_expression,
            token.GT: self._parse_infix_expression,
            token.LPAREN: self._parse_call_expression,
        }
        self._next_token()
        self._next_token()

    def parse(self) -> ast.Program:
        statements: List[ast.Statement] = []

        while self._cur_token.type != token.EOF:
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self._next_token()
        return ast.Program(statements)

    @property
    def errors(self) -> List[str]:
        return self._errors

    def _peek_error(self, tok: str):
        tok2 = self._peek_token.type
        self._errors.append(f"expected next token to be {tok}, got {tok2} instead")

    def _next_token(self) -> None:
        self._cur_token = self._peek_token
        self._peek_token = self._lexer.next_token()

    def _parse_statement(self) -> Optional[ast.Statement]:
        if self._cur_token.type == token.LET:
            return self._parse_let_statement()
        elif self._cur_token.type == token.RETURN:
            return self._parse_return_statement()
        else:
            return self._parse_expression_statement()
        return None

    def _parse_let_statement(self) -> Optional[ast.LetStatement]:
        cur_token = self._cur_token
        if not self._expect_peek(token.IDENT):
            return None
        name = ast.Identifier(self._cur_token, cast(str, (self._cur_token.literal)))
        if not self._expect_peek(token.ASSIGN):
            return None
        self._next_token()
        value = self._parse_expression(LOWEST)
        if self._peek_token_is(token.SEMICOLON):
            self._next_token()
        return ast.LetStatement(cur_token, name, value)

    def _parse_return_statement(self) -> Optional[ast.ReturnStatement]:
        cur_token = self._cur_token
        self._next_token()
        value = self._parse_expression(LOWEST)
        if self._peek_token_is(token.SEMICOLON):
            self._next_token()
        return ast.ReturnStatement(cur_token, value)

    def _cur_token_is(self, t: str) -> bool:
        return self._cur_token.type == t

    def _peek_token_is(self, t: str) -> bool:
        return self._peek_token.type == t

    def _expect_peek(self, t: str) -> bool:
        if self._peek_token_is(t):
            self._next_token()
            return True
        else:
            self._peek_error(t)
            return False

    def _peek_precedence(self) -> int:
        return _precedances.get(self._peek_token.type, LOWEST)

    def _cur_precedence(self) -> int:
        return _precedances.get(self._cur_token.type, LOWEST)

    def _register_prefix(self, token_type: str, fn: PrefixParseFn) -> None:
        self._prefix_parse_fns[token_type] = fn

    def _register_infix(self, token_type: str, fn: InfixParseFn) -> None:
        self._infix_parse_fns[token_type] = fn

    def _parse_expression_statement(self):
        cur_token = self._cur_token
        expression = self._parse_expression(LOWEST)

        stmt = ast.ExpressionStatement(cur_token, expression)

        if self._peek_token_is(token.SEMICOLON):
            self._next_token()

        return stmt

    def _parse_expression(self, precedence: int) -> ast.Expression:
        prefix = self._prefix_parse_fns.get(self._cur_token.type)
        if prefix is None:
            self._no_prefix_parser_fn_error(self._cur_token.type)
            return ast.NullExpression()
        left_exp = prefix()
        while (
            not self._peek_token_is(token.SEMICOLON)
            and precedence < self._peek_precedence()
        ):
            infix = self._infix_parse_fns.get(self._peek_token.type)
            if infix is None:
                return left_exp
            self._next_token()
            left_exp = infix(left_exp)
        return left_exp

    def _parse_identifier(self) -> ast.Expression:
        return ast.Identifier(self._cur_token, cast(str, self._cur_token.literal))

    def _parse_integer_literal(self) -> ast.Expression:
        value = int(cast(str, self._cur_token.literal))
        return ast.IntegerLiteral(self._cur_token, value)

    def _no_prefix_parser_fn_error(self, t: str) -> None:
        err = f"no prefix parse function for {t} found"
        self._errors.append(err)

    def _parse_prefix_expression(self) -> ast.Expression:
        cur_token = self._cur_token
        self._next_token()
        right = self._parse_expression(PREFIX)
        return ast.PrefixExpression(
            cur_token, cast(str, cur_token.literal), cast(ast.Expression, right)
        )

    def _parse_infix_expression(self, left: ast.Expression) -> ast.Expression:
        cur_token = self._cur_token

        precedence = self._cur_precedence()
        self._next_token()

        return ast.InfixExpression(
            cur_token,
            left,
            cast(str, cur_token.literal),
            cast(ast.Expression, self._parse_expression(precedence)),
        )

    def _parse_grouped_expression(self) -> ast.Expression:
        self._next_token()
        exp = self._parse_expression(LOWEST)
        if not self._expect_peek(token.RPAREN):
            return ast.NullExpression()
        return exp

    def _parse_boolean(self) -> ast.Expression:
        return ast.Boolean(self._cur_token, self._cur_token_is(token.TRUE))

    def _parse_if_expression(self) -> ast.Expression:
        cur_token = self._cur_token

        if not self._expect_peek(token.LPAREN):
            return ast.NullExpression()

        self._next_token()
        cond = self._parse_expression(LOWEST)

        if not self._expect_peek(token.RPAREN):
            return ast.NullExpression()

        if not self._expect_peek(token.LBRACE):
            return ast.NullExpression()

        cnsq = self._parse_block_statement()

        alt: Optional[ast.BlockStatement] = None
        if self._peek_token_is(token.ELSE):
            self._next_token()
            if not self._expect_peek(token.LBRACE):
                return ast.NullExpression()
            alt = self._parse_block_statement()

        return ast.IfExpression(cur_token, cond, cnsq, alt)

    def _parse_block_statement(self) -> ast.BlockStatement:
        cur_token = self._cur_token
        stmts: List[ast.Statement] = []

        self._next_token()

        while not self._cur_token_is(token.RBRACE) and not self._cur_token_is(
            token.EOF
        ):
            stmt = self._parse_statement()
            if stmt:
                stmts.append(stmt)
            self._next_token()

        return ast.BlockStatement(cur_token, stmts)

    def _parse_function_literal(self) -> ast.Expression:
        cur_token = self._cur_token

        if not self._expect_peek(token.LPAREN):
            return ast.NullExpression()

        params = self._parse_function_parameters()
        if not self._expect_peek(token.LBRACE):
            return ast.NullExpression()

        body = self._parse_block_statement()

        return ast.FunctionLiteral(cur_token, params, body)

    def _parse_function_parameters(self) -> List[ast.Identifier]:
        identifiers: List[ast.Identifier] = []
        if self._peek_token_is(token.RPAREN):
            self._next_token()
            return identifiers

        self._next_token()

        ident = ast.Identifier(self._cur_token, cast(str, self._cur_token.literal))
        identifiers.append(ident)

        while self._peek_token_is(token.COMMA):
            self._next_token()
            self._next_token()
            ident = ast.Identifier(self._cur_token, cast(str, self._cur_token.literal))
            identifiers.append(ident)

        if not self._expect_peek(token.RPAREN):
            return []

        return identifiers

    def _parse_call_expression(self, func: ast.Expression) -> ast.Expression:
        cur_token = self._cur_token
        args = self._parse_call_arguments()
        return ast.CallExpression(cur_token, func, args)

    def _parse_call_arguments(self) -> List[ast.Expression]:
        args: List[ast.Expression] = []
        if self._peek_token_is(token.RPAREN):
            self._next_token()
            return args

        self._next_token()

        args.append(self._parse_expression(LOWEST))

        while self._peek_token_is(token.COMMA):
            self._next_token()
            self._next_token()
            args.append(self._parse_expression(LOWEST))

        if not self._expect_peek(token.RPAREN):
            return []

        return args
