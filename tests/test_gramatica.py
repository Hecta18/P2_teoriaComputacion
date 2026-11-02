import unittest

import gramatica


class TestGramatica(unittest.TestCase):
    def test_cantidad_de_producciones(self):
        self.assertEqual(len(gramatica.PRODUCCIONES), 30)

    def test_esta_en_cnf(self):
        self.assertTrue(gramatica.esta_en_cnf())
        self.assertEqual(gramatica.errores_cnf(), [])

    def test_conjuntos_de_simbolos(self):
        self.assertEqual(len(gramatica.NO_TERMINALES), 8)
        self.assertEqual(len(gramatica.TERMINALES), 21)
        self.assertIn("S", gramatica.NO_TERMINALES)
        self.assertIn("the", gramatica.TERMINALES)

    def test_producciones_binarias_y_terminales(self):
        self.assertEqual(len(gramatica.PRODUCCIONES_BINARIAS), 5)
        self.assertEqual(len(gramatica.PRODUCCIONES_TERMINALES), 25)

    def test_tokenizar(self):
        self.assertEqual(gramatica.tokenizar("The Cat Eats"), ["the", "cat", "eats"])
        self.assertEqual(gramatica.tokenizar("   "), [])
        self.assertEqual(gramatica.tokenizar(""), [])

    def test_produccion_por_id(self):
        produccion = gramatica.produccion_por_id(0)
        self.assertEqual(produccion.lhs, "S")
        self.assertEqual(produccion.rhs, ("NP", "VP"))


if __name__ == "__main__":
    unittest.main()
