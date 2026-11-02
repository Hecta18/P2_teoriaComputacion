import unittest

import shunting_yard_regex as shy


class TestConcatenacionImplicita(unittest.TestCase):
    def test_letra_letra(self):
        self.assertEqual(shy.insertar_concatenacion_implicita(['a', 'b']),
                         ['a', '.', 'b'])

    def test_letra_parentesis(self):
        self.assertEqual(shy.insertar_concatenacion_implicita(['a', '(']),
                         ['a', '.', '('])

    def test_cierre_parentesis(self):
        self.assertEqual(shy.insertar_concatenacion_implicita([')', '(']),
                         [')', '.', '('])

    def test_estrella_letra(self):
        self.assertEqual(shy.insertar_concatenacion_implicita(['*', 'a']),
                         ['*', '.', 'a'])

    def test_explicito_no_duplica(self):
        self.assertEqual(shy.insertar_concatenacion_implicita(['a', '.', 'b']),
                         ['a', '.', 'b'])

    def test_cerradura_paren(self):
        self.assertEqual(shy.insertar_concatenacion_implicita(['*', '(']),
                         ['*', '.', '('])


class TestShuntingYard(unittest.TestCase):
    def test_abb(self):
        self.assertEqual(shy.expresion_a_postfix('(a|b)*abb'),
                         ['a', 'b', '|', '*', 'a', '.', 'b', '.', 'b', '.'])

    def test_union_concatenacion(self):
        self.assertEqual(shy.expresion_a_postfix('ab|cd'),
                         ['a', 'b', '.', 'c', 'd', '.', '|'])

    def test_parentesis_desbalanceados_faltante(self):
        with self.assertRaises(ValueError):
            shy.expresion_a_postfix('(a|b')

    def test_parentesis_desbalanceados_sobrante(self):
        with self.assertRaises(ValueError):
            shy.expresion_a_postfix('a|b)')


if __name__ == '__main__':
    unittest.main()