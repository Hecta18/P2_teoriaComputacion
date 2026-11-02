import unittest

from construccion_directa_afd import AFD, _nombre_estado
import minimizacion_afd as minimo
import afd_dibujo_simulacion as afd_mod


def _afd_desde_tabla(alfabeto, n_estados, inicial_idx, aceptacion_idx,
                     tabla):
    """Construye un AFD a partir de una tabla de transiciones
    tabla[i][j] = índice del estado destino o None si no hay transición.
    """
    estados = [frozenset({i}) for i in range(n_estados)]
    nombres = {s: _nombre_estado(i) for i, s in enumerate(estados)}
    inicial = frozenset({inicial_idx})
    aceptacion = {estados[i] for i in aceptacion_idx}
    transiciones = {}
    for i, fila in enumerate(tabla):
        for j, destino in enumerate(fila):
            if destino is not None:
                transiciones[(estados[i], alfabeto[j])] = estados[destino]
    return AFD(
        alfabeto=alfabeto,
        estados=estados,
        nombres=nombres,
        inicial=inicial,
        aceptacion=aceptacion,
        transiciones=transiciones,
    )


def _lenguaje(afd, cadenas):
    return tuple(afd_mod.simular_afd(afd, c) for c in cadenas)


class TestMinimizacionAfd(unittest.TestCase):
    def test_fusiona_estados_equivalentes(self):
        # a*: 0 y 1 son equivalentes (ambos aceptantes, δ idéntica). Las
        # transiciones con 'b' faltan (δ parcial), así que el refinamiento
        # añade un estado muerto que se fusiona con el estado trampa 2 y se
        # descarta, dejando un único estado.
        afd = _afd_desde_tabla(
            alfabeto=['a', 'b'],
            n_estados=3,
            inicial_idx=0,
            aceptacion_idx=[0, 1],
            tabla=[
                [1, None],  # 0
                [1, None],  # 1
                [2, 2],     # 2 (trampa)
            ],
        )
        afd_min = minimo.minimizar_afd(afd, imprimir=False)
        self.assertEqual(len(afd_min.estados), 1)

        cadenas = ['', 'a', 'aa', 'b', 'ab', 'aab']
        esperado = _lenguaje(afd, cadenas)
        self.assertEqual(_lenguaje(afd_min, cadenas), esperado)

    def test_afd_total_con_estado_trampa_conserva_el_trampa(self):
        # a* con δ completa: el trampa es un estado real, se conserva.
        afd = _afd_desde_tabla(
            alfabeto=['a', 'b'],
            n_estados=3,
            inicial_idx=0,
            aceptacion_idx=[0, 1],
            tabla=[
                [1, 2],  # 0
                [1, 2],  # 1
                [2, 2],  # 2 (trampa)
            ],
        )
        afd_min = minimo.minimizar_afd(afd, imprimir=False)
        self.assertEqual(len(afd_min.estados), 2)

        cadenas = ['', 'a', 'aa', 'b', 'ab', 'aab']
        esperado = _lenguaje(afd, cadenas)
        self.assertEqual(_lenguaje(afd_min, cadenas), esperado)

    def test_afd_ya_minimo_no_cambia(self):
        # Cadenas sobre {a, b} que terminan en 'a'.
        afd = _afd_desde_tabla(
            alfabeto=['a', 'b'],
            n_estados=2,
            inicial_idx=0,
            aceptacion_idx=[1],
            tabla=[
                [1, 0],   # 0
                [1, 0],   # 1
            ],
        )
        afd_min = minimo.minimizar_afd(afd, imprimir=False)
        self.assertEqual(len(afd_min.estados), 2)

        cadenas = ['', 'a', 'b', 'aa', 'ab', 'ba', 'bb', 'aba']
        esperado = _lenguaje(afd, cadenas)
        self.assertEqual(_lenguaje(afd_min, cadenas), esperado)

    def test_estado_inicial_equivalente_al_muerto_se_conserva(self):
        # Lenguaje vacío: inicial no aceptante que solo va a sí mismo.
        afd = _afd_desde_tabla(
            alfabeto=['a', 'b'],
            n_estados=1,
            inicial_idx=0,
            aceptacion_idx=[],
            tabla=[[0, 0]],
        )
        afd_min = minimo.minimizar_afd(afd, imprimir=False)
        self.assertEqual(len(afd_min.estados), 1)
        self.assertEqual(_lenguaje(afd_min, ['', 'a', 'b', 'aba']), (False, False, False, False))


if __name__ == '__main__':
    unittest.main()