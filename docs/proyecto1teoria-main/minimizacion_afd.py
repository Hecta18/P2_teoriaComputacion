# Minimización de un AFD mediante partición/refinamiento de estados.
#
# Idea: dos estados son equivalentes si se comportan igual ante cualquier
# entrada. Para encontrarlos:
#   1) Partimos de una partición inicial con dos clases: aceptación
#      y no aceptación.
#   2) En cada ronda, cada estado tiene una "firma":
#        (color propio, [color del destino para cada símbolo del alfabeto])
#      y los estados con la misma firma se fusionan en el mismo color.
#   3) Cuando la partición ya no cambia, los estados con el mismo color son
#      equivalentes y forman un único estado del AFD mínimo.
#
# Este método (partición/refinamiento o "Moore") produce exactamente el mismo
# AFD mínimo que el algoritmo de Hopcroft, con un código mucho más corto.
#
# Si el AFD tiene δ parcial (sin estado trampa), se añade internamente un
# estado "muerto" no aceptante que se auto-transiciona con todos los símbolos,
# para que δ quede completa durante el refinamiento. Al final, esa clase
# (y los estados equivalentes a ella) se elimina del resultado salvo que sea
# el estado inicial.

from __future__ import annotations

from construccion_directa_afd import AFD, _fmt_conjunto, _nombre_estado, imprimir_estados, imprimir_tabla_transiciones

ESTADO_MUERTO = None  # representación interna del estado trampa


def minimizar_afd(afd: AFD, imprimir: bool = True) -> AFD:
    """Devuelve el AFD mínimo equivalente a 'afd' (partición/refinamiento)."""
    alfabeto = afd.alfabeto
    estados_origen = list(afd.estados)
    inicial = afd.inicial
    aceptacion = afd.aceptacion

    # 1) δ total: si falta alguna transición, añadir el estado muerto.
    hay_muerto = bool(alfabeto) and any(
        afd.transiciones.get((e, a)) is None
        for e in estados_origen
        for a in alfabeto
    )
    ids = estados_origen + ([ESTADO_MUERTO] if hay_muerto else [])

    def delta(e, a):
        if e is ESTADO_MUERTO:
            return ESTADO_MUERTO
        return afd.transiciones.get((e, a), ESTADO_MUERTO)

    def es_aceptante(e):
        return e is not ESTADO_MUERTO and e in aceptacion

    # 2) Partición inicial: aceptación vs no aceptación.
    color = {e: 1 if es_aceptante(e) else 0 for e in ids}

    # 3) Refinamiento por firma hasta que la partición sea estable.
    while True:
        firma_color: dict[tuple, int] = {}
        nuevo: dict = {}
        for e in ids:
            firma = (color[e], tuple(color[delta(e, a)] for a in alfabeto))
            if firma not in firma_color:
                firma_color[firma] = len(firma_color)
            nuevo[e] = firma_color[firma]
        if all(nuevo[e] == color[e] for e in ids):
            break
        color = nuevo

    # 4) Clases de equivalencia: estados con el mismo color.
    clases: dict[int, list] = {}
    for e in ids:
        clases.setdefault(color[e], []).append(e)

    if imprimir:
        _imprimir_clases(clases, color_muerto=color.get(ESTADO_MUERTO))

    # 5) Descartar el estado muerto (y sus equivalentes) salvo que contenga
    #    al estado inicial (entonces es el "estado error" del AFD mínimo).
    descartadas: set[int] = set()
    if ESTADO_MUERTO in color and color[ESTADO_MUERTO] != color[inicial]:
        descartadas.add(color[ESTADO_MUERTO])

    # 6) Construir el AFD mínimo con un estado por clase.
    renumerado: dict[int, int] = {}
    estados_nuevos: list[frozenset[int]] = []
    nombres: dict[frozenset[int], str] = {}
    aceptacion_nueva: set[frozenset[int]] = set()

    for c in sorted(clases):
        if c in descartadas:
            continue
        idx = len(estados_nuevos)
        renumerado[c] = idx
        nuevo_estado = frozenset({idx})
        estados_nuevos.append(nuevo_estado)
        nombres[nuevo_estado] = _nombre_estado(idx)
        if any(es_aceptante(e) for e in clases[c]):
            aceptacion_nueva.add(nuevo_estado)

    inicial_nuevo = frozenset({renumerado[color[inicial]]})

    transiciones_nuevas: dict[tuple[frozenset[int], str], frozenset[int]] = {}
    for c, idx in renumerado.items():
        representante = next(e for e in clases[c] if e is not ESTADO_MUERTO)
        origen = frozenset({idx})
        for a in alfabeto:
            destino = delta(representante, a)
            if destino is ESTADO_MUERTO:
                continue
            dc = color[destino]
            if dc in descartadas:
                continue
            transiciones_nuevas[(origen, a)] = frozenset({renumerado[dc]})

    afd_minimo = AFD(
        alfabeto=alfabeto,
        estados=estados_nuevos,
        nombres=nombres,
        inicial=inicial_nuevo,
        aceptacion=aceptacion_nueva,
        transiciones=transiciones_nuevas,
    )

    if imprimir:
        imprimir_estados(afd_minimo)
        imprimir_tabla_transiciones(afd_minimo)

    return afd_minimo


def _imprimir_clases(clases: dict[int, list], color_muerto) -> None:
    """Imprime las clases de equivalencia del AFD original."""
    print("\nc) Clases de equivalencia (estados del AFD original):")
    for c in sorted(clases):
        miembros = []
        for m in clases[c]:
            if m is ESTADO_MUERTO:
                miembros.append("∅ (muerto)")
            else:
                miembros.append(_fmt_conjunto(m))
        etiqueta = "  (estado muerto)" if color_muerto == c else ""
        print(f"  clase {c}: {{{', '.join(miembros)}}}{etiqueta}")