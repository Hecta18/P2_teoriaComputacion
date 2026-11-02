import unittest

import regex_tokenize


class TestTokenize(unittest.TestCase):
    def test_ignora_espacios(self):
        self.assertEqual(regex_tokenize.tokenize('a | b'), ['a', '|', 'b'])

    def test_tokens_un_caracter(self):
        self.assertEqual(
            regex_tokenize.tokenize('(ab)*'),
            ['(', 'a', 'b', ')', '*'],
        )

    def test_cadena_vacia(self):
        self.assertEqual(regex_tokenize.tokenize('  '), [])


if __name__ == '__main__':
    unittest.main()