import unittest
from typing import cast
from monkey import lexer
from monkey import obj as objmod
from monkey import parser
from monkey import evaluator


class TestEvaluator(unittest.TestCase):
    def test_eval_integer_expression(self):
        tests = [
            ("5", 5),
            ("10", 10),
            ("-5", -5),
            ("-10", -10),
            ("5 + 5 + 5 + 5 - 10", 10),
            ("2 * 2 * 2 * 2 * 2", 32),
            ("-50 + 100 + -50", 0),
            ("5 * 2 + 10", 20),
            ("5 + 2 * 10", 25),
            ("20 + 2 * -10", 0),
            ("50 / 2 * 2 + 10", 60),
            ("2 * (5 + 10)", 30),
            ("3 * 3 * 3 + 10", 37),
            ("3 * (3 * 3) + 10", 37),
            ("(5 + 10 * 2 + 15 / 3) * 2 + -10", 50),
        ]
        for input, expected in tests:
            with self.subTest(input):
                evaluated = self._eval(input)
                self.assert_integer_object(evaluated, expected)

    def _eval(self, input: str) -> objmod.Object:
        psr = parser.Parser(lexer.Lexer(input))
        program = psr.parse()
        env = objmod.Environment()

        return evaluator.eval(program, env)

    def assert_integer_object(self, obj: objmod.Object, expected: int):
        self.assertIsInstance(obj, objmod.Integer)
        result = cast(objmod.Integer, obj)
        self.assertEqual(result.value, expected)

    def test_eval_boolean_expression(self):
        tests = [
            ("true", True),
            ("false", False),
            ("1 < 2", True),
            ("1 > 2", False),
            ("1 < 1", False),
            ("1 > 1", False),
            ("1 == 1", True),
            ("1 != 1", False),
            ("1 == 2", False),
            ("1 != 2", True),
            ("true == true", True),
            ("false == false", True),
            ("true == false", False),
            ("true != false", True),
            ("false != true", True),
            ("(1 < 2) == true", True),
            ("(1 < 2) == false", False),
            ("(1 > 2) == true", False),
            ("(1 > 2) == false", True),
        ]
        for input, expected in tests:
            with self.subTest(input):
                evaluated = self._eval(input)
                self.assert_boolean_object(evaluated, expected)

    def assert_boolean_object(self, obj: objmod.Object, expected: bool):
        self.assertIsInstance(obj, objmod.Boolean)
        result = cast(objmod.Boolean, obj)
        self.assertEqual(result.value, expected)

    def test_bang_operator(self):
        tests = [
            ("!true", False),
            ("!false", True),
            ("!5", False),
            ("!!true", True),
            ("!!false", False),
            ("!!5", True),
        ]
        for input, expected in tests:
            with self.subTest(input):
                evaluated = self._eval(input)
                self.assert_boolean_object(evaluated, expected)

    def test_if_else_expression(self):
        tests = [
            ("if (true) { 10 }", 10),
            ("if (false) { 10 }", None),
            ("if (1) { 10 }", 10),
            ("if (1 < 2) { 10 }", 10),
            ("if (1 > 2) { 10 }", None),
            ("if (1 > 2) { 10 } else { 20 }", 20),
            ("if (1 < 2) { 10 } else { 20 }", 10),
        ]
        for input, expected in tests:
            with self.subTest(input):
                evaluated = self._eval(input)
                if isinstance(expected, int):
                    self.assert_integer_object(evaluated, expected)
                else:
                    self.assertIs(evaluated, evaluator.NULL)

    def test_return_statements(self):
        tests = [
            ("return 10;", 10),
            ("return 10; 9", 10),
            ("return 2 * 5; 9", 10),
            ("9; return 10; 9", 10),
            (
                """
            if (10 > 1) {
                if (10 > 1) {
                    return 10;
                }
                return 1;
            }""",
                10,
            ),
        ]
        for input, expected in tests:
            with self.subTest(input):
                evaluated = self._eval(input)
                self.assert_integer_object(evaluated, expected)

    def test_error_handling(self):
        tests = [
            ("5 + true;", "type mismatch: INTEGER + BOOLEAN"),
            ("5 + true; 5;", "type mismatch: INTEGER + BOOLEAN"),
            ("-true", "unknown operator: -BOOLEAN"),
            ("true + false;", "unknown operator: BOOLEAN + BOOLEAN"),
            ("5; true + false; 5", "unknown operator: BOOLEAN + BOOLEAN"),
            ("if (10 > 1) { true + false; }", "unknown operator: BOOLEAN + BOOLEAN"),
            (
                """
                if (10 > 1) {
                    if (10 > 1) {
                        return true + false; 
                    }
                    return 1;
                }
                """,
                "unknown operator: BOOLEAN + BOOLEAN",
            ),
            ("foobar", "identifier not found: foobar")
        ]
        for input, expected_message in tests:
            with self.subTest(input):
                evaluated = self._eval(input)
                self.assertIsInstance(evaluated, objmod.Error)
                err_obj = cast(objmod.Error, evaluated)
                self.assertEqual(err_obj.message, expected_message)

    def test_let_statements(self):
        tests = [
            ("let a = 5; a;", 5),
            ("let a = 5 * 5; a;", 25),
            ("let a = 5; let b = a; b;", 5),
            ("let a = 5; let b = a; let c = a + b + 5; c;", 15),
        ]
        for input, expected in tests:
            with self.subTest(input):
                evaluated = self._eval(input)
                if isinstance(expected, int):
                    self.assert_integer_object(evaluated, expected)
                else:
                    self.assertIs(evaluated, evaluator.NULL)

    def test_function_object(self):
        input = "fn(x) { x + 2; };"
        evaluated = self._eval(input)
        self.assertIsInstance(evaluated, objmod.Function)
        fn = cast(objmod.Function, evaluated)
        self.assertEqual(len(fn.parameters), 1)
        self.assertEqual(str(fn.parameters[0]), "x")
        self.assertEqual(str(fn.body), "(x + 2)")

    def test_function_application(self):
        tests = [
            ("let identity = fn(x) { x; }; identity(5);", 5),
            ("let identity = fn(x) { return x; }; identity(5);", 5),
            ("let double = fn(x) { x * 2; }; double(5);", 10),
            ("let add = fn(x, y) { return x + y; }; add(5, 5);", 10),
            ("let add = fn(x, y) { return x + y; }; add(5 + 5, add(5, 5));", 20),
            ("fn(x) { x; }(5);", 5),
        ]
        for input, expected in tests:
            with self.subTest(input):
                evaluated = self._eval(input)
                self.assert_integer_object(evaluated, expected)
