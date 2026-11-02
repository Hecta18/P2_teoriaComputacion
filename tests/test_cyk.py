import unittest

import cyk as modulo_cyk


def _tokens_de_arbol(nodo):
    if nodo.token is not None:
        return [nodo.token]
    resultado = []
    for hijo in nodo.hijos:
        resultado.extend(_tokens_de_arbol(hijo))
    return resultado


class TestCYK(unittest.TestCase):
    def test_acepta_frases_validas(self):
        frases = [
            "he cooks",
            "the cat eats the cake",
            "the dog drinks the beer in the oven",
            "she cuts the meat with the knife",
        ]
        for frase in frases:
            with self.subTest(frase=frase):
                resultado = modulo_cyk.cyk(frase)
                self.assertTrue(resultado.aceptada)
                self.assertIn("S", resultado.tabla[0][resultado.n])
                self.assertGreater(resultado.contador.total, 0)
                self.assertTrue(resultado.eventos)

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
                resultado = modulo_cyk.cyk(frase)
                self.assertFalse(resultado.aceptada)

    def test_una_derivacion_para_frases_simples(self):
        frases = [
            "he cooks",
            "the cat eats the cake",
            "the cat eats the cake in the oven with the fork",
        ]
        for frase in frases:
            with self.subTest(frase=frase):
                resultado = modulo_cyk.cyk(frase)
                self.assertEqual(modulo_cyk._contar_derivaciones(resultado), 1)

    def test_derivacion_izquierda(self):
        resultado = modulo_cyk.cyk("he cooks")
        arboles = modulo_cyk.reconstruir_derivaciones(resultado, maximo=1)
        self.assertEqual(len(arboles), 1)
        pasos = modulo_cyk.derivacion_izquierda(arboles[0])
        self.assertEqual(pasos[0], "S")
        self.assertEqual(pasos[-1], "he cooks")
        self.assertEqual(_tokens_de_arbol(arboles[0]), ["he", "cooks"])

    def test_arbol_conserva_los_tokens(self):
        frase = "the cat drinks the juice with the spoon"
        resultado = modulo_cyk.cyk(frase)
        arboles = modulo_cyk.reconstruir_derivaciones(resultado, maximo=1)
        self.assertEqual(_tokens_de_arbol(arboles[0]), frase.split())

    def test_limite_de_arboles(self):
        resultado = modulo_cyk.cyk("the cat eats the cake in the oven")
        arboles = modulo_cyk.reconstruir_derivaciones(resultado, maximo=1)
        self.assertEqual(len(arboles), 1)


if __name__ == "__main__":
    unittest.main()
