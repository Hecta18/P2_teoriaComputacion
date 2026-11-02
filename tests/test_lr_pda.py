import unittest

import lr_pda


def _tokens_de_arbol(nodo):
    if nodo.token is not None:
        return [nodo.token]
    resultado = []
    for hijo in nodo.hijos:
        resultado.extend(_tokens_de_arbol(hijo))
    return resultado


class TestPDADeterminista(unittest.TestCase):
    def setUp(self):
        self.tabla = lr_pda.construir_tabla_slr()

    def test_tabla_sin_conflictos(self):
        self.assertEqual(self.tabla.conflictos, [])
        self.assertEqual(len(self.tabla.estados), 32)

    def test_acepta_frases_validas(self):
        frases = [
            "he cooks",
            "the cat eats the cake",
            "the dog drinks the beer in the oven",
            "she cuts the meat with the knife",
        ]
        for frase in frases:
            with self.subTest(frase=frase):
                resultado = lr_pda.simular_dpda(self.tabla, frase)
                self.assertTrue(resultado.aceptada)
                arbol = resultado.arbol
                self.assertIsNotNone(arbol)
                assert arbol is not None
                self.assertEqual(arbol.simbolo, "S")
                self.assertEqual(
                    _tokens_de_arbol(arbol),
                    frase.split(),
                )

    def test_rechaza_frases_invalidas(self):
        frases = [
            "",
            "the cat",
            "eats the cake",
            "the cat eats cake",
            "he cooks the",
            "cat eats the cake",
        ]
        for frase in frases:
            with self.subTest(frase=frase):
                resultado = lr_pda.simular_dpda(self.tabla, frase)
                self.assertFalse(resultado.aceptada)
                self.assertIsNone(resultado.arbol)

    def test_ultima_accion_es_accept(self):
        resultado = lr_pda.simular_dpda(self.tabla, "he cooks")
        self.assertTrue(resultado.aceptada)
        self.assertEqual(resultado.camino[-1][2], "accept")

    def test_conteo_lineal(self):
        for frase in ("he cooks", "the cat eats the cake"):
            resultado = lr_pda.simular_dpda(self.tabla, frase)
            n = len(frase.split())
            self.assertLessEqual(resultado.contador.total, 5 * n)

    def test_primero_y_follow(self):
        self.assertEqual(self.tabla.first["S"], {"the", "a", "he", "she"})
        self.assertEqual(self.tabla.follow["S"], {"$"})
        self.assertIn("in", self.tabla.follow["VP"])
        self.assertIn("with", self.tabla.follow["VP"])
        self.assertIn("the", self.tabla.follow["V"])


if __name__ == "__main__":
    unittest.main()
