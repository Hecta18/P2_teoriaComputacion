# Construcción de un AFD a partir de un AFN mediante el algoritmo de
# construcción de subconjuntos (Dstates / Dtran).
#
# Algoritmo (pseudocódigo clásico):
#   Dstates = { ε-clausura(s0) }
#   while (haya un estado T sin marcar en Dstates):
#       marcar T
#       for (cada símbolo a del alfabeto):
#           U = ε-clausura(move(T, a))
#           if (U ∉ Dstates):
#               agregar U a Dstates sin marcar
#           Dtran[T, a] = U
#
# Cada estado del AFD es un subconjunto (frozenset) de estados del AFN.
# Como la mayoría de los AFD de este proyecto tienen δ parcial (sin estado
# trampa), las transiciones que llevan a un conjunto vacío se omiten.

from __future__ import annotations

import thompson_arbol as thompson
from construccion_directa_afd import AFD, _fmt_conjunto, _nombre_estado, imprimir_tabla_transiciones

EPSILON = thompson.EPSILON


def obtener_alfabeto(nfa: thompson.AFN) -> list[str]:
    """Símbolos del alfabeto: todas las etiquetas de transición que no son ε."""
    simbolos = {s for (_, s) in nfa.transiciones if s != EPSILON}
    return sorted(simbolos)


def move(estados: set[int] | frozenset[int], simbolo: str,
         nfa: thompson.AFN) -> frozenset[int]:
    """move(T, a): estados del AFN alcanzados desde T consumiendo 'simbolo'."""
    destinos: set[int] = set()
    for estado in estados:
        destinos.update(nfa.transiciones_desde(estado, simbolo))
    return frozenset(destinos)


def construir_afd_por_subconjuntos(nfa: thompson.AFN) -> AFD:
    """Algoritmo Dstates / Dtran: construye el AFD equivalente al AFN dado."""
    alfabeto = obtener_alfabeto(nfa)

    inicial = frozenset(thompson.epsilon_clausura(set(nfa.iniciales), nfa))
    estados: list[frozenset[int]] = []
    nombres: dict[frozenset[int], str] = {}
    transiciones: dict[tuple[frozenset[int], str], frozenset[int]] = {}
    aceptacion: set[frozenset[int]] = set()

    pendientes: list[frozenset[int]] = [inicial]
    vistos: set[frozenset[int]] = {inicial}
    estados.append(inicial)
    nombres[inicial] = _nombre_estado(0)

    while pendientes:
        t = pendientes.pop(0)
        if t.intersection(nfa.finales):
            aceptacion.add(t)

        for a in alfabeto:
            u = frozenset(thompson.epsilon_clausura(move(set(t), a, nfa), nfa))
            if not u:
                continue
            if u not in vistos:
                vistos.add(u)
                estados.append(u)
                nombres[u] = _nombre_estado(len(estados) - 1)
                pendientes.append(u)
            transiciones[(t, a)] = u

    return AFD(
        alfabeto=alfabeto,
        estados=estados,
        nombres=nombres,
        inicial=inicial,
        aceptacion=aceptacion,
        transiciones=transiciones,
    )


def imprimir_afd_subconjuntos(afd: AFD) -> None:
    """Imprime los estados (como subconjuntos del AFN) y la tabla de transiciones."""
    print("\nb) Estados del AFD (subconjuntos de estados del AFN):")
    for estado in afd.estados:
        nombre = afd.nombres[estado]
        marcas = []
        if estado == afd.inicial:
            marcas.append("inicial")
        if estado in afd.aceptacion:
            marcas.append("aceptación")
        sufijo = f"  ({', '.join(marcas)})" if marcas else ""
        print(f"  {nombre} = {_fmt_conjunto(estado)}{sufijo}")
    imprimir_tabla_transiciones(afd)