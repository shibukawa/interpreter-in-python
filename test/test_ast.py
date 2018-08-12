import unittest
from monkey import token
from monkey import ast


class TestString(unittest.TestCase):
    def test_string(self):
        let = ast.LetStatement(
            token.Token(token.LET, "let"),
            ast.Identifier(
                token.Token(token.IDENT, "myVar"), "myVar"),
            ast.Identifier(
                token.Token(token.IDENT, "anotherVar"), "anotherVar")
        )
        program = ast.Program([let])
        self.assertEqual(str(program), "let myVar = anotherVar;")
