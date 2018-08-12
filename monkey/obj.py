from typing import Dict, Tuple, List, Optional, cast
import dataclasses
import io
from . import ast

INTEGER_OBJ = "INTEGER"
BOOLEAN_OBJ = "BOOLEAN"
NULL_OBJ = "NULL"
RETURN_VALUE_OBJ = "RETURN_VALUE"
ERROR_OBJ = "ERROR"
FUNCTION_OBJ = "FUNCTION"


class Object:
    def type(self) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class Integer(Object):
    value: int

    def type(self) -> str:
        return INTEGER_OBJ

    def __str__(self) -> str:
        return str(self.value)


@dataclasses.dataclass(frozen=True)
class Boolean(Object):
    value: bool

    def type(self) -> str:
        return BOOLEAN_OBJ

    def __str__(self) -> str:
        return "true" if self.value else "false"


class Null(Object):
    def type(self) -> str:
        return NULL_OBJ

    def __str__(self) -> str:
        return "null"


@dataclasses.dataclass(frozen=True)
class ReturnValue(Object):
    value: Object

    def type(self) -> str:
        return RETURN_VALUE_OBJ

    def __str__(self) -> str:
        return str(self.value)


@dataclasses.dataclass(frozen=True)
class Error(Object):
    message: str

    def type(self) -> str:
        return ERROR_OBJ

    def __str__(self) -> str:
        return f"ERROR: {self.message}"


TRUE = Boolean(True)
FALSE = Boolean(False)
NULL = Null()


class Environment:
    _store: Dict[str, Object]
    _outer: Optional["Environment"]

    def __init__(self):
        self._store = {}
        self._outer = None

    def get(self, name: str) -> Tuple[Object, bool]:
        ok = name in self._store
        if not ok and self._outer:
            outer = cast("Environment", self._outer)
            return outer.get(name)
        obj = self._store.get(name, NULL)
        return (obj, ok)

    def set(self, name: str, val: Object) -> Object:
        self._store[name] = val
        return val

    def new_enclosed_environment(self) -> "Environment":
        env = Environment()
        env._outer = self
        return env


@dataclasses.dataclass(frozen=True)
class Function(Object):
    parameters: List[ast.Identifier]
    body: ast.BlockStatement
    env: Environment

    def type(self) -> str:
        return FUNCTION_OBJ

    def __str__(self) -> str:
        buffer = io.StringIO()
        print(
            f"fn(",
            file=buffer, end='')
        for i, parameter in enumerate(self.parameters):
            if i != 0:
                print(", ", file=buffer, end="")
            print(str(parameter), file=buffer, end='')
        print(") {\n%s\n}" % str(self.body), file=buffer, end='')
        return buffer.getvalue()
