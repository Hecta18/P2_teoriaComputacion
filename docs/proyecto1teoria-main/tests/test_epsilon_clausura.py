import unittest

import thompson_arbol as thompson


def _nfa_ejemplo():
    """AFN pequeño con transiciones ε:
    0 -e-> 1, 0 -e-> 2, 1 -a-> 3, 2 -e-> 3, 3 -e-> 4
    """
    nfa = thompson.AFN()
    for i in range(5):
        nfa.estados[i] = thompson.Estado(i)
    nfa.agregar_transicion(0, thompson.EPSILON, 1)
    nfa.agregar_transicion(0, thompson.EPSILON, 2)
    nfa.agregar_transicion(1, 'a', 3)
    nfa.agregar_transicion(2, thompson.EPSILON, 3)
    nfa.agregar_transicion(3, thompson.EPSILON, 4)
    return nfa


class TestEpsilonClausura(unittest.TestCase):
    def test_clausura_encadena(self):
        nfa = _nfa_ejemplo()
        self.assertEqual(thompson.epsilon_clausura({0}, nfa), {0, 1, 2, 3, 4})

    def test_clausura_sin_transiciones(self):
        nfa = _nfa_ejemplo()
        self.assertEqual(thompson.epsilon_clausura({4}, nfa), {4})

    def test_clausura_no_consume_simbolos(self):
        nfa = _nfa_ejemplo()
        # Desde 1 solo se llega a 1 (la 'a' no es transición ε).
        self.assertEqual(thompson.epsilon_clausura({1}, nfa), {1})


if __name__ == '__main__':
    unittest.main()