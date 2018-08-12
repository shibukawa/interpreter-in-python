import unittest
from typing import cast, Any
from monkey import parser
from monkey import lexer
from monkey import ast


class TestParser(unittest.TestCase):
    def check_parser_errors(self, p: parser.Parser):
        for msg in p.errors:
            print(msg)
        self.assertEqual(len(p.errors), 0)

    def test_let_statements(self):
        tests = [
            ("let x = 5;", "x", 5),
            ("let y = true;", "y", True),
            ("let foobar = y;", "foobar", "y"),
        ]
        for input, expected_ident, expected_value in tests:
            with self.subTest(input):
                lex = lexer.Lexer(input)
                psr = parser.Parser(lex)
                program = psr.parse()
                self.check_parser_errors(psr)

                self.assertEqual(len(program.statements), 1)
                stmt = program.statements[0]
                self.assertEqual(stmt.token_literal(), "let")
                self.assertIsInstance(stmt, ast.LetStatement)
                let_stmt = cast(ast.LetStatement, stmt)
                self.assert_identifier(let_stmt.name, expected_ident)
                self.assert_literal_expression(
                    let_stmt.value, expected_value)

    def test_return_statements(self):
        tests = [
            ("return 5;", 5),
            ("return true;", True),
            ("return foobar;", "foobar")
        ]
        for input, expected_value in tests:
            with self.subTest(input):
                lex = lexer.Lexer(input)
                psr = parser.Parser(lex)
                program = psr.parse()
                self.check_parser_errors(psr)

                self.assertEqual(len(program.statements), 1)
                stmt = program.statements[0]
                self.assertIsInstance(stmt, ast.ReturnStatement)
                self.assertEqual(stmt.token_literal(), "return")
                ret_stmt = cast(ast.ReturnStatement, stmt)
                self.assert_literal_expression(
                    ret_stmt.return_value, expected_value)

    def test_identifier_expression(self):
        input = "foobar;"

        lex = lexer.Lexer(input)
        psr = parser.Parser(lex)
        program = psr.parse()
        self.check_parser_errors(psr)

        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(program.statements[0], ast.ExpressionStatement)
        stmt = cast(ast.ExpressionStatement, program.statements[0])
        self.assert_identifier(stmt.expression, "foobar")

    def test_integer_literal(self):
        input = "5;"

        lex = lexer.Lexer(input)
        psr = parser.Parser(lex)
        program = psr.parse()
        self.check_parser_errors(psr)

        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(program.statements[0], ast.ExpressionStatement)
        stmt = cast(ast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt.expression, ast.IntegerLiteral)
        ident = cast(ast.IntegerLiteral, stmt.expression)
        self.assertEqual(ident.value, 5)
        self.assertEqual(ident.token_literal(), "5")

    def test_parse_prefix_expression(self):
        prefixTests = [
            ("!5;", "!", 5),
            ("-15;", "-", 15),
            ("!true;", "!", True),
            ("!false;", "!", False),
        ]
        for input, operator, value in prefixTests:
            with self.subTest(input):
                lex = lexer.Lexer(input)
                psr = parser.Parser(lex)
                program = psr.parse()
                self.check_parser_errors(psr)

                self.assertEqual(len(program.statements), 1)
                self.assertIsInstance(
                    program.statements[0], ast.ExpressionStatement)
                stmt = cast(ast.ExpressionStatement, program.statements[0])
                self.assertIsInstance(
                    stmt.expression, ast.PrefixExpression)
                exp = cast(ast.PrefixExpression, stmt.expression)
                self.assertEqual(exp.operator, operator)
                self.assert_literal_expression(exp.right, value)
    
    def test_parse_infix_expression(self):
        infixTests = [
            ("5 + 5;", 5, "+", 5),
            ("5 - 5;", 5, "-", 5),
            ("5 * 5;", 5, "*", 5),
            ("5 / 5;", 5, "/", 5),
            ("5 > 5;", 5, ">", 5),
            ("5 < 5;", 5, "<", 5),
            ("5 == 5;", 5, "==", 5),
            ("5 != 5;", 5, "!=", 5),
            ("true == true;", True, "==", True),
            ("true != false;", True, "!=", False),
            ("false == false;", False, "==", False)
        ]
        for input, left, operator, right in infixTests:
            with self.subTest(input):
                lex = lexer.Lexer(input)
                psr = parser.Parser(lex)
                program = psr.parse()
                self.check_parser_errors(psr)

                self.assertEqual(len(program.statements), 1)
                self.assertIsInstance(
                    program.statements[0], ast.ExpressionStatement)
                stmt = cast(ast.ExpressionStatement, program.statements[0])
                self.assert_infix_expression(
                    stmt.expression, left, operator, right)

    def assert_infix_expression(
            self, exp: ast.Expression, left: Any, operator: str, right: Any):
        self.assertIsInstance(exp, ast.InfixExpression)
        opexp = cast(ast.InfixExpression, exp)
        self.assert_literal_expression(opexp.left, left)
        self.assertEqual(opexp.operator, operator)
        self.assert_literal_expression(opexp.right, right)

    def test_operator_precedence_parsing(self):
        tests = [
            ("-a * b", "((-a) * b)"),
            ("!-a", "(!(-a))"),
            ("a + b + c", "((a + b) + c)"),
            ("a + b - c", "((a + b) - c)"),
            ("a * b * c", "((a * b) * c)"),
            ("a * b / c", "((a * b) / c)"),
            ("a + b / c", "(a + (b / c))"),
            ("a + b * c + d / e - f", "(((a + (b * c)) + (d / e)) - f)"),
            ("3 + 4; -5 * 5", "(3 + 4)((-5) * 5)"),
            ("5 > 4 == 3 < 4", "((5 > 4) == (3 < 4))"),
            ("5 < 4 != 3 > 4", "((5 < 4) != (3 > 4))"),
            ("3 + 4 * 5 == 3 * 1 + 4 * 5",
             "((3 + (4 * 5)) == ((3 * 1) + (4 * 5)))"),
            ("true", "true"),
            ("false", "false"),
            ("3 > 5 == false", "((3 > 5) == false)"),
            ("3 < 5 == true", "((3 < 5) == true)"),
            ("1 + (2 + 3) + 4", "((1 + (2 + 3)) + 4)"),
            ("(5 + 5) * 2", "((5 + 5) * 2)"),
            ("2 / (5 + 5)", "(2 / (5 + 5))"),
            ("-(5 + 5)", "(-(5 + 5))"),
            ("!(true == true)", "(!(true == true))"),
            ("a + add(b * c) + d", "((a + add((b * c))) + d)"),
            ("add(a, b, 1, 2 * 3, 4 + 5, add(6, 7 * 8))",
             "add(a, b, 1, (2 * 3), (4 + 5), add(6, (7 * 8)))"),
            ("add(a + b + c * d / f + g)",
             "add((((a + b) + ((c * d) / f)) + g))")
        ]
        for input, expected in tests:
            with self.subTest(input):
                lex = lexer.Lexer(input)
                psr = parser.Parser(lex)
                program = psr.parse()
                self.check_parser_errors(psr)

                self.assertEqual(str(program), expected)

    def _test_integer_lileral(self, exp: ast.Expression, value: int):
        self.assertIsInstance(exp, ast.IntegerLiteral)
        ident = cast(ast.IntegerLiteral, exp)
        self.assertEqual(ident.value, value)
        self.assertEqual(ident.token_literal(), str(value))

    def assert_identifier(self, exp: ast.Expression, value: str):
        self.assertIsInstance(exp, ast.Identifier)
        ident = cast(ast.Identifier, exp)
        self.assertEqual(ident.value, value)
        self.assertEqual(ident.token_literal(), value)

    def _test_boolean_lileral(self, exp: ast.Expression, value: bool):
        self.assertIsInstance(exp, ast.Boolean)
        ident = cast(ast.Boolean, exp)
        self.assertEqual(ident.value, value)
        self.assertEqual(ident.token_literal(), str(value).lower())

    def assert_literal_expression(
            self, exp: ast.Expression, expected: Any):
        if isinstance(expected, str):
            self.assert_identifier(exp, cast(str, expected))
        elif isinstance(expected, bool):
            self._test_boolean_lileral(exp, cast(bool, expected))
        elif isinstance(expected, int):
            self._test_integer_lileral(exp, cast(int, expected))
        else:
            self.fail(f"type of ext not handled. got={type(expected)}")

    def test_boolean_expression(self):
        tests = [
            ("true;", "true", True),
            ("false;", "false", False)
        ]

        for input, literal, value in tests:
            with self.subTest(input):
                lex = lexer.Lexer(input)
                psr = parser.Parser(lex)
                program = psr.parse()
                self.check_parser_errors(psr)

                self.assertEqual(len(program.statements), 1)
                self.assertIsInstance(
                    program.statements[0], ast.ExpressionStatement)
                stmt = cast(ast.ExpressionStatement, program.statements[0])
                self.assertIsInstance(stmt.expression, ast.Boolean)
                boolean = cast(ast.Boolean, stmt.expression)
                self.assertEqual(boolean.value, value)
                self.assertEqual(boolean.token_literal(), literal)

    def test_if_expression(self):
        tests = [
            ("if (x < y) { x }", ("x", "<", "y"), "x", None),
            ("if (x < y) { x } else { y }", ("x", "<", "y"), "x", "y")
        ]

        for input, cond, consequence, alternative in tests:
            with self.subTest(input):
                lex = lexer.Lexer(input)
                psr = parser.Parser(lex)
                program = psr.parse()
                self.check_parser_errors(psr)

                self.assertEqual(len(program.statements), 1)
                self.assertIsInstance(
                    program.statements[0], ast.ExpressionStatement)
                stmt = cast(ast.ExpressionStatement, program.statements[0])

                self.assertIsInstance(stmt.expression, ast.IfExpression)
                ifexp = cast(ast.IfExpression, stmt.expression)
                self.assert_infix_expression(ifexp.condition, *cond)

                self.assertEqual(len(ifexp.consequence.statements), 1)
                self.assertIsInstance(
                    ifexp.consequence.statements[0], ast.ExpressionStatement)
                cnsq = cast(
                    ast.ExpressionStatement, ifexp.consequence.statements[0])
                self.assert_identifier(cnsq.expression, consequence)

                if alternative:
                    self.assertEqual(len(ifexp.alternative.statements), 1)
                    self.assertIsInstance(
                        ifexp.alternative.statements[0],
                        ast.ExpressionStatement)
                    alt = cast(
                        ast.ExpressionStatement,
                        ifexp.alternative.statements[0])
                    self.assert_identifier(alt.expression, alternative)

    def test_function_literal_parsing(self):
        input = "fn(x, y) { x + y; }"

        lex = lexer.Lexer(input)
        psr = parser.Parser(lex)
        program = psr.parse()
        self.check_parser_errors(psr)

        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(
            program.statements[0], ast.ExpressionStatement)
        stmt = cast(ast.ExpressionStatement, program.statements[0])

        self.assertIsInstance(stmt.expression, ast.FunctionLiteral)
        func = cast(ast.FunctionLiteral, stmt.expression)
        self.assertEqual(len(func.parameters), 2)
        self.assert_literal_expression(func.parameters[0], "x")
        self.assert_literal_expression(func.parameters[1], "y")

        self.assertEqual(len(func.body.statements), 1)
        self.assertIsInstance(func.body.statements[0], ast.ExpressionStatement)
        body = cast(ast.ExpressionStatement, func.body.statements[0])
        self.assert_infix_expression(body.expression, "x", "+", "y")

    def test_function_parameter_parsing(self):
        tests = [
            ("fn() {}", []),
            ("fn(x) {}", ["x"]),
            ("fn(x, y, z) {}", ["x", "y", "z"])
        ]
        for input, expectedparmas in tests:
            self.subTest(input)

            lex = lexer.Lexer(input)
            psr = parser.Parser(lex)
            program = psr.parse()
            self.check_parser_errors(psr)

            self.assertEqual(len(program.statements), 1)
            self.assertIsInstance(
                program.statements[0], ast.ExpressionStatement)
            stmt = cast(ast.ExpressionStatement, program.statements[0])
            self.assertIsInstance(stmt.expression, ast.FunctionLiteral)
            func = cast(ast.FunctionLiteral, stmt.expression)

            self.assertEqual(len(func.parameters), len(expectedparmas))
            for param, expectedparam in zip(func.parameters, expectedparmas):
                self.assert_literal_expression(param, expectedparam)

    def test_call_expression_parsing(self):
        input = "add(1, 2 * 3, 4 + 5)"

        lex = lexer.Lexer(input)
        psr = parser.Parser(lex)
        program = psr.parse()
        self.check_parser_errors(psr)

        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(
            program.statements[0], ast.ExpressionStatement)
        stmt = cast(ast.ExpressionStatement, program.statements[0])
        self.assertIsInstance(stmt.expression, ast.CallExpression)
        call = cast(ast.CallExpression, stmt.expression)

        self.assert_identifier(call.function, "add")

        self.assertEqual(len(call.arguments), 3)

        self.assert_literal_expression(call.arguments[0], 1)
        self.assert_infix_expression(call.arguments[1], 2, "*", 3)
        self.assert_infix_expression(call.arguments[2], 4, "+", 5)
