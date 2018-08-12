import dataclasses
from typing import List, Optional, cast
import io
from . import token as tokenmod


class Node:
    token: tokenmod.Token

    def token_literal(self) -> Optional[str]:
        return self.token.literal


class Statement(Node):
    pass


class Expression(Node):
    pass


@dataclasses.dataclass(frozen=True)
class Program(Node):
    statements: List[Statement]

    def token_literal(self) -> Optional[str]:
        if len(self.statements) > 0:
            return self.statements[0].token_literal()
        return None

    def __str__(self) -> str:
        buffer = io.StringIO()
        for s in self.statements:
            print(s, file=buffer, end='')
        return buffer.getvalue()


@dataclasses.dataclass(frozen=True)
class Identifier(Expression):
    token: tokenmod.Token
    value: str

    def __str__(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class LetStatement(Statement):
    token: tokenmod.Token
    name: Identifier
    value: Optional[Expression]

    def __str__(self) -> str:
        buffer = io.StringIO()
        print(f"{self.token_literal()} {self.name} = ", file=buffer, end='')
        if self.value:
            print(self.value, file=buffer, end='')
        print(";", file=buffer, end='')
        return buffer.getvalue()


@dataclasses.dataclass(frozen=True)
class ReturnStatement(Statement):
    token: tokenmod.Token
    return_value: Optional[Expression]

    def __str__(self) -> str:
        buffer = io.StringIO()
        print(f"{self.token_literal()} ", file=buffer, end='')
        if self.return_value:
            print(self.return_value, file=buffer, end='')
        print(";", file=buffer)
        return buffer.getvalue()


@dataclasses.dataclass(frozen=True)
class BlockStatement(Statement):
    token: tokenmod.Token
    statements: List[Statement]

    def __str__(self) -> str:
        buffer = io.StringIO()
        for stmt in self.statements:
            print(str(stmt), file=buffer, end='')
        return buffer.getvalue()


@dataclasses.dataclass(frozen=True)
class ExpressionStatement(Statement):
    token: tokenmod.Token
    expression: Optional[Expression]

    def __str__(self) -> str:
        if self.expression is None:
            return ""
        return str(self.expression)


@dataclasses.dataclass(frozen=True)
class NullExpression(Expression):
    def token_literal(self) -> Optional[str]:
        return None

    def __str__(self) -> str:
        return "Null"


@dataclasses.dataclass(frozen=True)
class IntegerLiteral(Expression):
    token: tokenmod.Token
    value: int

    def __str__(self) -> str:
        return cast(str, self.token.literal)


@dataclasses.dataclass(frozen=True)
class PrefixExpression(Expression):
    token: tokenmod.Token
    operator: str
    right: Expression

    def __str__(self) -> str:
        return f"({self.operator}{str(self.right)})"


@dataclasses.dataclass(frozen=True)
class InfixExpression(Expression):
    token: tokenmod.Token
    left: Expression
    operator: str
    right: Expression

    def __str__(self) -> str:
        return f"({str(self.left)} {self.operator} {str(self.right)})"


@dataclasses.dataclass(frozen=True)
class Boolean(Expression):
    token: tokenmod.Token
    value: bool

    def __str__(self) -> str:
        return cast(str, self.token.literal)


@dataclasses.dataclass(frozen=True)
class IfExpression(Expression):
    token: tokenmod.Token
    condition: Expression
    consequence: BlockStatement
    alternative: Optional[BlockStatement]

    def __str__(self) -> str:
        buffer = io.StringIO()
        print(
            f"if {str(self.condition)} {str(self.consequence)}",
            file=buffer, end='')
        if self.alternative:
            print(
                f" else {str(self.alternative)}",
                file=buffer, end='')
        return buffer.getvalue()


@dataclasses.dataclass(frozen=True)
class FunctionLiteral(Expression):
    token: tokenmod.Token
    parameters: List[Identifier]
    body: BlockStatement

    def __str__(self) -> str:
        buffer = io.StringIO()
        print(
            f"{self.token_literal()} (",
            file=buffer, end='')
        for i, parameter in enumerate(self.parameters):
            if i != 0:
                print(", ", file=buffer, end="")
            print(str(parameter), file=buffer, end='')
        print(f") {str(self.body)}", file=buffer, end='')
        return buffer.getvalue()


@dataclasses.dataclass(frozen=True)
class CallExpression(Expression):
    token: tokenmod.Token
    function: Expression
    arguments: List[Expression]

    def __str__(self) -> str:
        buffer = io.StringIO()
        print(
            f"{str(self.function)}(",
            file=buffer, end='')
        for i, argument in enumerate(self.arguments):
            if i != 0:
                print(", ", file=buffer, end="")
            print(str(argument), file=buffer, end='')
        print(f")", file=buffer, end='')
        return buffer.getvalue()
