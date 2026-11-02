# Construcción directa de un AFD a partir del árbol sintáctico de una
# expresión regular (fase 2 del laboratorio).
#
# Pipeline:
#   1) Extender la regex con el marcador de fin '#' (concatenación raíz . #).
#   2) Numerar posiciones (DFS) en hojas del alfabeto y '#'.
#   3) Computar nullable, firstpos y lastpos en cada nodo.
#   4) Computar followpos para cada posición.
#   5) Construir el AFD (Dstates / Dtran) usando followpos.
#
# El marcador '#' se añade automáticamente; no debe aparecer en el archivo
# de entrada. Las hojas ε no reciben posición.

from __future__ import annotations

from dataclasses import dataclass, field

from Arbol_sintactico import EPSILON, MARCADOR_FIN, NodoSintactico


def extender_con_marcador(raiz: NodoSintactico) -> NodoSintactico:
    """Devuelve el árbol de la expresión regular extendida: raiz . #."""
    return NodoSintactico('.', raiz, NodoSintactico(MARCADOR_FIN))


def numerar_posiciones(nodo: NodoSintactico,
                        contador: list[int] | None = None,
                        simbolo_por_pos: dict[int, str] | None = None
                        ) -> dict[int, str]:
    """Numera en DFS las hojas que no son ε. Devuelve posición → símbolo."""
    if contador is None:
        contador = [1]
    if simbolo_por_pos is None:
        simbolo_por_pos = {}

    if nodo.es_hoja():
        if nodo.valor != EPSILON:
            nodo.posicion = contador[0]
            simbolo_por_pos[nodo.posicion] = nodo.valor
            contador[0] += 1
        else:
            nodo.posicion = None
        return simbolo_por_pos

    if nodo.izquierda is not None:
        numerar_posiciones(nodo.izquierda, contador, simbolo_por_pos)
    if nodo.derecha is not None:
        numerar_posiciones(nodo.derecha, contador, simbolo_por_pos)
    return simbolo_por_pos


def computar_nullable_first_last(nodo: NodoSintactico) -> None:
    """Calcula nullable, firstpos y lastpos bottom-up sobre el árbol."""
    if nodo.es_hoja():
        if nodo.valor == EPSILON:
            nodo.nullable = True
            nodo.firstpos = set()
            nodo.lastpos = set()
        else:
            nodo.nullable = False
            nodo.firstpos = {nodo.posicion}
            nodo.lastpos = {nodo.posicion}
        return

    if nodo.valor == '|':
        computar_nullable_first_last(nodo.izquierda)
        computar_nullable_first_last(nodo.derecha)
        c1, c2 = nodo.izquierda, nodo.derecha
        nodo.nullable = c1.nullable or c2.nullable
        nodo.firstpos = c1.firstpos | c2.firstpos
        nodo.lastpos = c1.lastpos | c2.lastpos
        return

    if nodo.valor == '.':
        computar_nullable_first_last(nodo.izquierda)
        computar_nullable_first_last(nodo.derecha)
        c1, c2 = nodo.izquierda, nodo.derecha
        nodo.nullable = c1.nullable and c2.nullable
        if c1.nullable:
            nodo.firstpos = c1.firstpos | c2.firstpos
        else:
            nodo.firstpos = set(c1.firstpos)
        if c2.nullable:
            nodo.lastpos = c1.lastpos | c2.lastpos
        else:
            nodo.lastpos = set(c2.lastpos)
        return

    if nodo.valor == '*':
        computar_nullable_first_last(nodo.izquierda)
        c1 = nodo.izquierda
        nodo.nullable = True
        nodo.firstpos = set(c1.firstpos)
        nodo.lastpos = set(c1.lastpos)
        return

    raise ValueError(f"Operador no soportado en el árbol: {nodo.valor!r}")


def computar_followpos(nodo: NodoSintactico,
                       followpos: dict[int, set[int]] | None = None
                       ) -> dict[int, set[int]]:
    """Calcula followpos recorriendo concatenaciones y cerraduras Kleene."""
    if followpos is None:
        followpos = {}

    if nodo.es_hoja():
        if nodo.posicion is not None and nodo.posicion not in followpos:
            followpos[nodo.posicion] = set()
        return followpos

    if nodo.izquierda is not None:
        computar_followpos(nodo.izquierda, followpos)
    if nodo.derecha is not None:
        computar_followpos(nodo.derecha, followpos)

    if nodo.valor == '.':
        c1, c2 = nodo.izquierda, nodo.derecha
        for i in c1.lastpos:
            followpos.setdefault(i, set()).update(c2.firstpos)
    elif nodo.valor == '*':
        c1 = nodo.izquierda
        for i in c1.lastpos:
            followpos.setdefault(i, set()).update(c1.firstpos)

    return followpos


@dataclass
class AFD:
    """AFD obtenido por construcción directa."""

    alfabeto: list[str]
    estados: list[frozenset[int]]
    nombres: dict[frozenset[int], str]
    inicial: frozenset[int]
    aceptacion: set[frozenset[int]]
    transiciones: dict[tuple[frozenset[int], str], frozenset[int]] = field(
        default_factory=dict
    )
    simbolo_por_pos: dict[int, str] = field(default_factory=dict)
    followpos: dict[int, set[int]] = field(default_factory=dict)
    posicion_marcador: int | None = None


def _nombre_estado(indice: int) -> str:
    """Etiqueta A, B, ... Z, A1, B1, ..."""
    if indice < 26:
        return chr(ord('A') + indice)
    return f"{chr(ord('A') + (indice % 26))}{indice // 26}"


def construir_afd(raiz_ext: NodoSintactico,
                  simbolo_por_pos: dict[int, str],
                  followpos: dict[int, set[int]]) -> AFD:
    """Algoritmo de construcción directa (Dstates / Dtran) vía followpos."""
    alfabeto = sorted({
        s for s in simbolo_por_pos.values() if s != MARCADOR_FIN
    })
    posicion_marcador = next(
        (p for p, s in simbolo_por_pos.items() if s == MARCADOR_FIN),
        None,
    )

    inicial = frozenset(raiz_ext.firstpos)
    estados: list[frozenset[int]] = []
    nombres: dict[frozenset[int], str] = {}
    transiciones: dict[tuple[frozenset[int], str], frozenset[int]] = {}
    aceptacion: set[frozenset[int]] = set()

    if not inicial:
        # Regex que solo genera ε: estado vacío (acepta si # está en firstpos,
        # lo cual no ocurre salvo casos degenerados). Se deja un estado vacío.
        inicial = frozenset()

    pendientes: list[frozenset[int]] = [inicial]
    vistos: set[frozenset[int]] = {inicial}
    estados.append(inicial)
    nombres[inicial] = _nombre_estado(0)

    while pendientes:
        s = pendientes.pop(0)
        if posicion_marcador is not None and posicion_marcador in s:
            aceptacion.add(s)

        for x in alfabeto:
            posiciones_x = {
                p for p in s if simbolo_por_pos.get(p) == x
            }
            t_set: set[int] = set()
            for p in posiciones_x:
                t_set.update(followpos.get(p, set()))
            t = frozenset(t_set)

            if not t:
                continue

            if t not in vistos:
                vistos.add(t)
                estados.append(t)
                nombres[t] = _nombre_estado(len(estados) - 1)
                pendientes.append(t)
            transiciones[(s, x)] = t

    return AFD(
        alfabeto=alfabeto,
        estados=estados,
        nombres=nombres,
        inicial=inicial,
        aceptacion=aceptacion,
        transiciones=transiciones,
        simbolo_por_pos=simbolo_por_pos,
        followpos=followpos,
        posicion_marcador=posicion_marcador,
    )


def procesar_arbol_a_afd(raiz: NodoSintactico) -> tuple[NodoSintactico, AFD]:
    """Extiende, numera, computa atributos y construye el AFD desde 'raiz'."""
    raiz_ext = extender_con_marcador(raiz)
    simbolo_por_pos = numerar_posiciones(raiz_ext)
    computar_nullable_first_last(raiz_ext)
    followpos = computar_followpos(raiz_ext)
    # Asegurar claves para todas las posiciones (p. ej. # con followpos vacío).
    for p in simbolo_por_pos:
        followpos.setdefault(p, set())
    afd = construir_afd(raiz_ext, simbolo_por_pos, followpos)
    return raiz_ext, afd


def _fmt_conjunto(valores: set[int] | frozenset[int]) -> str:
    if not valores:
        return "∅"
    return "{" + ",".join(str(v) for v in sorted(valores)) + "}"


def imprimir_posiciones(simbolo_por_pos: dict[int, str]) -> None:
    print("\nPosiciones numeradas (hojas del alfabeto y '#'):")
    for pos in sorted(simbolo_por_pos):
        print(f"  {pos} → {simbolo_por_pos[pos]}")


def imprimir_followpos(followpos: dict[int, set[int]]) -> None:
    print("\nfollowpos:")
    print(f"  {'pos':>4}  followpos")
    print(f"  {'----':>4}  ---------")
    for pos in sorted(followpos):
        print(f"  {pos:>4}  {_fmt_conjunto(followpos[pos])}")


def imprimir_estados(afd: AFD) -> None:
    print("\nb) Estados del AFD y posiciones que los conforman:")
    for estado in afd.estados:
        nombre = afd.nombres[estado]
        marca = []
        if estado == afd.inicial:
            marca.append("inicial")
        if estado in afd.aceptacion:
            marca.append("aceptación")
        sufijo = f"  ({', '.join(marca)})" if marca else ""
        print(f"  {nombre} = {_fmt_conjunto(estado)}{sufijo}")


def imprimir_tabla_transiciones(afd: AFD) -> None:
    print("\na) Tabla de transiciones del AFD:")
    if not afd.alfabeto:
        print("  (alfabeto vacío)")
        return

    col_estado = max(6, max(len(afd.nombres[e]) for e in afd.estados))
    cols = {x: max(3, len(x)) for x in afd.alfabeto}
    encabezado = f"  {'estado':<{col_estado}}" + "".join(
        f"  {x:^{cols[x]}}" for x in afd.alfabeto
    )
    print(encabezado)
    print("  " + "-" * (len(encabezado) - 2))

    for estado in afd.estados:
        nombre = afd.nombres[estado]
        if estado == afd.inicial and estado in afd.aceptacion:
            etiqueta = f"->*{nombre}"
        elif estado == afd.inicial:
            etiqueta = f"->{nombre}"
        elif estado in afd.aceptacion:
            etiqueta = f"*{nombre}"
        else:
            etiqueta = nombre
        fila = f"  {etiqueta:<{col_estado}}"
        for x in afd.alfabeto:
            destino = afd.transiciones.get((estado, x))
            celda = afd.nombres[destino] if destino is not None else "—"
            fila += f"  {celda:^{cols[x]}}"
        print(fila)


def imprimir_resultado_afd(afd: AFD) -> None:
    """Imprime tablas auxiliares y los resultados a) y b) del enunciado."""
    imprimir_posiciones(afd.simbolo_por_pos)
    imprimir_followpos(afd.followpos)
    imprimir_estados(afd)
    imprimir_tabla_transiciones(afd)
