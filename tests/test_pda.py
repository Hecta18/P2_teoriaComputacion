import unittest

import pda


class TestPDANoDeterminista(unittest.TestCase):
    def setUp(self):
        self.automata = pda.construir_pda_desde_gramatica()

    def test_definicion_basica(self):
        self.assertEqual(self.automata.inicial, pda.Q0)
        self.assertEqual(self.automata.simbolo_inicial_pila, pda.Z0)
        self.assertIn(pda.Q2, self.automata.aceptacion)
        self.assertIn("S", self.automata.alfabeto_pila)
        self.assertIn("cat", self.automata.alfabeto_pila)
        self.assertIn("cat", self.automata.alfabeto_entrada)

    def test_acepta_frases_validas(self):
        frases = [
            "he cooks",
            "the cat eats the cake",
            "the dog drinks the beer in the oven",
            "she cuts the meat with the knife",
        ]
        for frase in frases:
            with self.subTest(frase=frase):
                resultado = pda.simular_pda(self.automata, frase)
                self.assertTrue(resultado.aceptada)
                self.assertGreater(resultado.contador.total, 0)

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
                resultado = pda.simular_pda(self.automata, frase)
                self.assertFalse(resultado.aceptada)

    def test_camino_aceptado_termina_en_q2(self):
        resultado = pda.simular_pda(self.automata, "he cooks")
        self.assertTrue(resultado.aceptada)
        self.assertEqual(resultado.camino[0][0].estado, pda.Q0)
        self.assertEqual(resultado.camino[-1][0].estado, pda.Q2)
        self.assertEqual(resultado.camino[-1][0].posicion, 2)

    def test_formato_de_configuracion(self):
        configuracion = pda.Configuracion(pda.Q1, 1, (pda.Z0, "VP", "NP"))
        texto = pda.formatear_configuracion(configuracion, ["he", "cooks"])
        self.assertIn("(q1, cooks, NP VP Z0)", texto)

    def test_limite_de_configuraciones(self):
        resultado = pda.simular_pda(
            self.automata, "the cat eats the cake in the oven", max_configuraciones=1
        )
        self.assertFalse(resultado.aceptada)
        self.assertTrue(resultado.limite_alcanzado)


if __name__ == "__main__":
    unittest.main()
