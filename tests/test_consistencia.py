import unittest

import cyk as modulo_cyk
import lr_pda
import pda


class TestConsistencia(unittest.TestCase):
    def setUp(self):
        self.automata = pda.construir_pda_desde_gramatica()
        self.tabla = lr_pda.construir_tabla_slr()

    def _resultados(self, frase):
        return (
            pda.simular_pda(self.automata, frase).aceptada,
            lr_pda.simular_dpda(self.tabla, frase).aceptada,
            modulo_cyk.cyk(frase).aceptada,
        )

    def test_todos_los_metodos_coinciden(self):
        casos = {
            "he cooks": True,
            "she drinks the juice": True,
            "the cat eats the cake": True,
            "the dog drinks the beer in the oven": True,
            "the cat cuts the meat with the knife": True,
            "she eats the soup with the spoon in the oven": True,
            "the cat": False,
            "eats the cake": False,
            "the cat eats cake": False,
            "he cooks the": False,
            "the cat in the oven": False,
            "cat eats the cake": False,
            "": False,
        }
        for frase, esperado in casos.items():
            with self.subTest(frase=frase):
                resultados = self._resultados(frase)
                self.assertEqual(resultados, (esperado, esperado, esperado))

    def test_operaciones_crecen_con_la_longitud(self):
        corta = "he cooks"
        larga = "he cooks in the cat in the cat in the cat"

        ops_cyk_corta = modulo_cyk.cyk(corta).contador.total
        ops_cyk_larga = modulo_cyk.cyk(larga).contador.total
        self.assertGreater(ops_cyk_larga, ops_cyk_corta)

        ops_npda_corta = pda.simular_pda(self.automata, corta).contador.total
        ops_npda_larga = pda.simular_pda(self.automata, larga).contador.total
        self.assertGreater(ops_npda_larga, ops_npda_corta)

        ops_dpda_corta = lr_pda.simular_dpda(self.tabla, corta).contador.total
        ops_dpda_larga = lr_pda.simular_dpda(self.tabla, larga).contador.total
        self.assertGreater(ops_dpda_larga, ops_dpda_corta)


if __name__ == "__main__":
    unittest.main()
