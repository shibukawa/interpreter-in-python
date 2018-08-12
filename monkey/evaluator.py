from typing import cast, Optional, Tuple, List
from . import obj as objmod
from . import ast
from .obj import NULL, TRUE, FALSE


def eval(node: ast.Node, env: objmod.Environment) -> objmod.Object:
    if isinstance(node, ast.Program):
        program = cast(ast.Program, node)
        return _eval_program(program, env)
    elif isinstance(node, ast.ExpressionStatement):
        expr = cast(ast.ExpressionStatement, node)
        return eval(cast(ast.Node, expr.expression), env)
    elif isinstance(node, ast.IntegerLiteral):
        return objmod.Integer(node.value)
    elif isinstance(node, ast.Boolean):
        return _native_to_boolean_object(node.value)
    elif isinstance(node, ast.PrefixExpression):
        prefixexpr = cast(ast.PrefixExpression, node)
        right = eval(prefixexpr.right, env)
        if _is_error(right):
            return right
        return _eval_prefix_expression(prefixexpr.operator, right)
    elif isinstance(node, ast.InfixExpression):
        infixexpr = cast(ast.InfixExpression, node)
        left = eval(infixexpr.left, env)
        if _is_error(left):
            return left
        right = eval(infixexpr.right, env)
        if _is_error(right):
            return right
        return _eval_infix_expression(left, infixexpr.operator, right)
    elif isinstance(node, ast.BlockStatement):
        block = cast(ast.BlockStatement, node)
        return _eval_block_statements(block, env)
    elif isinstance(node, ast.IfExpression):
        ifexp = cast(ast.IfExpression, node)
        return _eval_if_expression(ifexp, env)
    elif isinstance(node, ast.ReturnStatement):
        ret = cast(ast.ReturnStatement, node)
        val = eval(cast(ast.Expression, ret.return_value), env)
        if _is_error(val):
            return val
        return objmod.ReturnValue(val)
    elif isinstance(node, ast.LetStatement):
        letstmt = cast(ast.LetStatement, node)
        val = eval(cast(ast.Node, letstmt.value), env)
        if _is_error(val):
            return val
        env.set(node.name.value, val)
    elif isinstance(node, ast.Identifier):
        ident = cast(ast.Identifier, node)
        val, ok = env.get(ident.value)
        if not ok:
            return objmod.Error(f"identifier not found: {ident.value}")
        return val
    elif isinstance(node, ast.FunctionLiteral):
        fn = cast(ast.FunctionLiteral, node)
        return objmod.Function(fn.parameters, fn.body, env)
    elif isinstance(node, ast.CallExpression):
        callexp = cast(ast.CallExpression, node)
        func = eval(callexp.function, env)
        if _is_error(func):
            return func
        args, err = _eval_expression(callexp.arguments, env)
        if err is not NULL:
            return cast(objmod.Object, err)
        return _apply_function(func, args)
    return NULL


def _eval_program(program: ast.Program, env: objmod.Environment) -> objmod.Object:
    result: objmod.Object = NULL

    for stmt in program.statements:
        result = eval(stmt, env)
        if isinstance(result, objmod.ReturnValue):
            retval = cast(objmod.ReturnValue, result)
            return retval.value
        elif isinstance(result, objmod.Error):
            return result

    return result


def _eval_block_statements(
    block: ast.BlockStatement, env: objmod.Environment
) -> objmod.Object:
    result: objmod.Object = NULL

    for stmt in block.statements:
        result = eval(stmt, env)
        rt = result.type()
        if rt == objmod.RETURN_VALUE_OBJ or rt == objmod.ERROR_OBJ:
            return result
    return result


def _is_error(obj: objmod.Object) -> bool:
    return obj.type() == objmod.ERROR_OBJ


def _eval_prefix_expression(op: str, right: objmod.Object) -> objmod.Object:
    if op == "!":
        return _eval_bang_operator_expression(right)
    elif op == "-":
        return _eval_minux_prefix_operator_expression(right)
    else:
        return objmod.Error(f"unknown operator: {op}{right.type()}")


def _eval_bang_operator_expression(right: objmod.Object) -> objmod.Object:
    if right is TRUE:
        return FALSE
    if right is FALSE:
        return TRUE
    if right is NULL:
        return TRUE
    else:
        return FALSE


def _eval_minux_prefix_operator_expression(right: objmod.Object) -> objmod.Object:
    if right.type() == objmod.INTEGER_OBJ:
        intobj = cast(objmod.Integer, right)
        return objmod.Integer(-intobj.value)
    else:
        return objmod.Error(f"unknown operator: -{right.type()}")


def _native_to_boolean_object(input: bool):
    return TRUE if input else FALSE


def _eval_infix_expression(
    left: objmod.Object, op: str, right: objmod.Object
) -> objmod.Object:
    if left.type() == objmod.INTEGER_OBJ and right.type() == objmod.INTEGER_OBJ:
        return _eval_integer_infix_expression(left, op, right)
    elif op == "==":
        return _native_to_boolean_object(left is right)
    elif op == "!=":
        return _native_to_boolean_object(left is not right)
    elif left.type() != right.type():
        return objmod.Error(f"type mismatch: {left.type()} {op} {right.type()}")
    else:
        return objmod.Error(f"unknown operator: {left.type()} {op} {right.type()}")


def _eval_integer_infix_expression(
    left: objmod.Object, op: str, right: objmod.Object
) -> objmod.Object:
    leftval = cast(objmod.Integer, left).value
    rightval = cast(objmod.Integer, right).value
    if op == "+":
        return objmod.Integer(leftval + rightval)
    elif op == "-":
        return objmod.Integer(leftval - rightval)
    elif op == "*":
        return objmod.Integer(leftval * rightval)
    elif op == "/":
        return objmod.Integer(leftval // rightval)
    elif op == "==":
        return _native_to_boolean_object(leftval == rightval)
    elif op == "!=":
        return _native_to_boolean_object(leftval != rightval)
    elif op == "<":
        return _native_to_boolean_object(leftval < rightval)
    elif op == ">":
        return _native_to_boolean_object(leftval > rightval)
    else:
        return objmod.Error(f"unknown operator: {left.type()} {op} {right.type()}")


def _eval_if_expression(
    ifexp: ast.IfExpression, env: objmod.Environment
) -> objmod.Object:
    condition = eval(ifexp.condition, env)
    if _is_error(condition):
        return condition
    if _is_truthy(condition):
        return eval(ifexp.consequence, env)
    elif ifexp.alternative:
        return eval(ifexp.alternative, env)
    else:
        return NULL


def _eval_expression(
    exps: List[ast.Expression], env: objmod.Environment
) -> Tuple[List[objmod.Object], Optional[objmod.Object]]:
    result: List[objmod.Object] = []

    for exp in exps:
        evaluated = eval(exp, env)
        if _is_error(evaluated):
            return ([], evaluated)
        result.append(evaluated)
    return (result, NULL)


def _apply_function(fn: objmod.Object, args: List[objmod.Object]):
    if not isinstance(fn, objmod.Function):
        return objmod.Error(f"not a function: {fn.type()}")
    extended_env = _extend_function_env(fn, args)
    evaluated = eval(fn.body, extended_env)
    return _unwrap_return_value(evaluated)


def _extend_function_env(
    fn: objmod.Function, args: List[objmod.Object]
) -> objmod.Environment:
    env = fn.env.new_enclosed_environment()

    for param, arg in zip(fn.parameters, args):
        env.set(param.value, arg)
    return env


def _unwrap_return_value(obj: objmod.Object) -> objmod.Object:
    if isinstance(obj, objmod.ReturnValue):
        retval = cast(objmod.ReturnValue, obj)
        return retval.value
    return obj


def _is_truthy(obj: objmod.Object) -> bool:
    if obj is NULL:
        return False
    elif obj is TRUE:
        return True
    elif obj is FALSE:
        return False
    else:
        return True
