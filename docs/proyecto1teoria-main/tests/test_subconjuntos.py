import unittest

import construccion_subconjuntos as subconjuntos
import afd_dibujo_simulacion as afd_mod
import thompson_arbol as thompson


def _nfa_simple():
    """AFN mínimo que reconoce la cadena 'a':
    0 (inicial) -a-> 1 (final)
    """
    nfa = thompson.AFN()
    nfa.estados[0] = thompson.Estado(0, es_inicial=True)
    nfa.estados[1] = thompson.Estado(1, es_final=True)
    nfa.iniciales = {0}
    nfa.finales = {1}
    nfa.agregar_transicion(0, 'a', 1)
    return nfa


class TestMove(unittest.TestCase):
    def test_move_directo(self):
        nfa = _nfa_simple()
        self.assertEqual(subconjuntos.move(set([0]), 'a', nfa), frozenset({1}))

    def test_move_inexistente(self):
        nfa = _nfa_simple()
        self.assertEqual(subconjuntos.move(set([0]), 'b', nfa), frozenset())

    def test_obtener_alfabeto(self):
        nfa = _nfa_simple()
        self.assertEqual(subconjuntos.obtener_alfabeto(nfa), ['a'])


class TestAlfabetoFiltraEpsilon(unittest.TestCase):
    def test_alfa_ignora_epsilon(self):
        nfa = _nfa_simple()
        nfa.agregar_transicion(1, thompson.EPSILON, 0)
        self.assertEqual(subconjuntos.obtener_alfabeto(nfa), ['a'])


class TestConstruirAfdPorSubconjuntos(unittest.TestCase):
    def test_reconoce_el_mismo_lenguaje(self):
        nfa = _nfa_simple()
        afd = subconjuntos.construir_afd_por_subconjuntos(nfa)
        self.assertTrue(afd_mod.simular_afd(afd, 'a'))
        self.assertFalse(afd_mod.simular_afd(afd, ''))
        self.assertFalse(afd_mod.simular_afd(afd, 'b'))


if __name__ == '__main__':
    unittest.main()