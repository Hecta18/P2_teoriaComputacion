from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from gramatica import (
    INICIAL,
    NO_TERMINALES,
    PRODUCCIONES,
    TERMINALES,
    Produccion,
    tokenizar,
)

FIN_ENTRADA = "$"
AUMENTADO = "S'"

Item = tuple[int, int]
Accion = tuple[str, int]


@dataclass(frozen=True)
class ProduccionLR:
    id: int
    lhs: str
    rhs: tuple[str, ...]
    original: bool

    @property
    def texto(self) -> str:
        if not self.rhs:
            return f"{self.lhs} -> epsilon"
        return f"{self.lhs} -> {' '.join(self.rhs)}"


PRODUCCIONES_LR: tuple[ProduccionLR, ...] = (
    ProduccionLR(0, AUMENTADO, (INICIAL,), False),
) + tuple(
    ProduccionLR(produccion.id + 1, produccion.lhs, produccion.rhs, True)
    for produccion in PRODUCCIONES
)

PRODUCCIONES_LR_POR_LHS: dict[str, tuple[ProduccionLR, ...]] = {
    no_terminal: tuple(p for p in PRODUCCIONES_LR if p.lhs == no_terminal)
    for no_terminal in (*NO_TERMINALES, AUMENTADO)
}


@dataclass(frozen=True)
class NodoParseo:
    simbolo: str
    hijos: tuple["NodoParseo", ...] = ()
    token: str | None = None

    @property
    def es_hoja(self) -> bool:
        return not self.hijos


@dataclass
class TablaSLR:
    estados: list[frozenset[Item]]
    transiciones: dict[tuple[int, str], int]
    acciones: dict[tuple[int, str], Accion]
    gotos: dict[tuple[int, str], int]
    first: dict[str, set[str]]
    follow: dict[str, set[str]]
    conflictos: list[str] = field(default_factory=list)


@dataclass
class ContadorDPDA:
    acciones: int = 0
    shifts: int = 0
    reducciones: int = 0

    @property
    def total(self) -> int:
        return self.acciones


@dataclass
class ResultadoDPDA:
    aceptada: bool
    camino: list[tuple[tuple[int, ...], int, str]]
    arbol: NodoParseo | None
    contador: ContadorDPDA
    producciones: list[ProduccionLR]


def _first_y_follow() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    first: dict[str, set[str]] = {no_terminal: set() for no_terminal in NO_TERMINALES}
    nullable: dict[str, bool] = {no_terminal: False for no_terminal in NO_TERMINALES}

    cambio = True
    while cambio:
        cambio = False
        for produccion in PRODUCCIONES:
            if len(produccion.rhs) == 1 and produccion.rhs[0] in TERMINALES:
                if produccion.rhs[0] not in first[produccion.lhs]:
                    first[produccion.lhs].add(produccion.rhs[0])
                    cambio = True
                continue

            todos_anulables = True
            for simbolo in produccion.rhs:
                if simbolo in TERMINALES:
                    if simbolo not in first[produccion.lhs]:
                        first[produccion.lhs].add(simbolo)
                        cambio = True
                    todos_anulables = False
                    break
                antes = len(first[produccion.lhs])
                first[produccion.lhs].update(first[simbolo])
                if len(first[produccion.lhs]) != antes:
                    cambio = True
                if not nullable[simbolo]:
                    todos_anulables = False
                    break
            if todos_anulables and not nullable[produccion.lhs]:
                nullable[produccion.lhs] = True
                cambio = True

    follow: dict[str, set[str]] = {no_terminal: set() for no_terminal in NO_TERMINALES}
    follow[INICIAL].add(FIN_ENTRADA)

    cambio = True
    while cambio:
        cambio = False
        for produccion in PRODUCCIONES:
            for indice, simbolo in enumerate(produccion.rhs):
                if simbolo not in NO_TERMINALES:
                    continue
                sufijo = produccion.rhs[indice + 1:]
                primeros, sufijo_anulable = _first_de_secuencia(sufijo, first, nullable)
                antes = len(follow[simbolo])
                follow[simbolo].update(primeros)
                if sufijo_anulable:
                    follow[simbolo].update(follow[produccion.lhs])
                if len(follow[simbolo]) != antes:
                    cambio = True

    return first, follow


def _first_de_secuencia(
    secuencia: tuple[str, ...],
    first: dict[str, set[str]],
    nullable: dict[str, bool],
) -> tuple[set[str], bool]:
    resultado: set[str] = set()
    if not secuencia:
        return resultado, True
    for simbolo in secuencia:
        if simbolo in TERMINALES:
            resultado.add(simbolo)
            return resultado, False
        resultado.update(first[simbolo])
        if not nullable[simbolo]:
            return resultado, False
    return resultado, True


def _cerradura(items: set[Item]) -> frozenset[Item]:
    resultado = set(items)
    pendientes = list(items)
    while pendientes:
        produccion_id, punto = pendientes.pop()
        produccion = PRODUCCIONES_LR[produccion_id]
        if punto >= len(produccion.rhs):
            continue
        simbolo = produccion.rhs[punto]
        if simbolo not in NO_TERMINALES:
            continue
        for nueva in PRODUCCIONES_LR_POR_LHS[simbolo]:
            item = (nueva.id, 0)
            if item not in resultado:
                resultado.add(item)
                pendientes.append(item)
    return frozenset(resultado)


def _goto(items: frozenset[Item], simbolo: str) -> frozenset[Item]:
    movidos = {
        (produccion_id, punto + 1)
        for produccion_id, punto in items
        if punto < len(PRODUCCIONES_LR[produccion_id].rhs)
        and PRODUCCIONES_LR[produccion_id].rhs[punto] == simbolo
    }
    if not movidos:
        return frozenset()
    return _cerradura(movidos)


def _construir_estados() -> tuple[
    list[frozenset[Item]], dict[tuple[int, str], int]
]:
    inicial = _cerradura({(0, 0)})
    estados: list[frozenset[Item]] = [inicial]
    indices: dict[frozenset[Item], int] = {inicial: 0}
    transiciones: dict[tuple[int, str], int] = {}
    pendientes: deque[int] = deque([0])

    while pendientes:
        indice = pendientes.popleft()
        simbolos: set[str] = set()
        for produccion_id, punto in estados[indice]:
            produccion = PRODUCCIONES_LR[produccion_id]
            if punto < len(produccion.rhs):
                simbolos.add(produccion.rhs[punto])
        for simbolo in sorted(simbolos):
            destino = _goto(estados[indice], simbolo)
            if not destino:
                continue
            if destino not in indices:
                indices[destino] = len(estados)
                estados.append(destino)
                pendientes.append(indices[destino])
            transiciones[(indice, simbolo)] = indices[destino]

    return estados, transiciones


def construir_tabla_slr() -> TablaSLR:
    first, follow = _first_y_follow()
    estados, transiciones = _construir_estados()
    acciones: dict[tuple[int, str], Accion] = {}
    gotos: dict[tuple[int, str], int] = {}
    conflictos: list[str] = []

    def registrar(estado: int, simbolo: str, accion: Accion) -> None:
        clave = (estado, simbolo)
        if clave in acciones and acciones[clave] != accion:
            conflictos.append(
                f"Conflicto en estado {estado} con '{simbolo}': "
                f"{acciones[clave]} vs {accion}"
            )
            return
        acciones[clave] = accion

    for (estado, simbolo), destino in transiciones.items():
        if simbolo in TERMINALES:
            registrar(estado, simbolo, ("shift", destino))
        elif simbolo in NO_TERMINALES:
            gotos[(estado, simbolo)] = destino

    for estado, items in enumerate(estados):
        for produccion_id, punto in items:
            produccion = PRODUCCIONES_LR[produccion_id]
            if punto < len(produccion.rhs):
                continue
            if produccion.id == 0:
                registrar(estado, FIN_ENTRADA, ("accept", 0))
            else:
                for terminal in sorted(follow[produccion.lhs]):
                    registrar(estado, terminal, ("reduce", produccion.id))

    return TablaSLR(
        estados=estados,
        transiciones=transiciones,
        acciones=acciones,
        gotos=gotos,
        first=first,
        follow=follow,
        conflictos=conflictos,
    )


def _texto_accion(accion: Accion) -> str:
    tipo, valor = accion
    if tipo == "shift":
        return f"shift {valor}"
    if tipo == "reduce":
        return f"reduce {PRODUCCIONES_LR[valor].texto}"
    return "accept"


def simular_dpda(
    tabla: TablaSLR,
    cadena: str | list[str],
) -> ResultadoDPDA:
    tokens = tokenizar(cadena) if isinstance(cadena, str) else list(cadena)
    entrada = tokens + [FIN_ENTRADA]
    pila_estados: list[int] = [0]
    valores: list[NodoParseo] = []
    contador = ContadorDPDA()
    camino: list[tuple[tuple[int, ...], int, str]] = []
    producciones_usadas: list[ProduccionLR] = []
    max_pasos = 100 + 20 * max(1, len(tokens))
    posicion = 0

    for _ in range(max_pasos):
        estado = pila_estados[-1]
        simbolo = entrada[posicion] if posicion < len(entrada) else FIN_ENTRADA
        clave = (estado, simbolo)
        accion = tabla.acciones.get(clave)
        if accion is None:
            camino.append((tuple(pila_estados), posicion, f"error con '{simbolo}'"))
            contador.acciones += 1
            return ResultadoDPDA(
                aceptada=False,
                camino=camino,
                arbol=None,
                contador=contador,
                producciones=producciones_usadas,
            )

        camino.append((tuple(pila_estados), posicion, _texto_accion(accion)))
        tipo, valor = accion

        if tipo == "shift":
            pila_estados.append(valor)
            valores.append(NodoParseo(simbolo, token=simbolo))
            posicion += 1
            contador.shifts += 1
            contador.acciones += 1
            continue

        if tipo == "reduce":
            produccion = PRODUCCIONES_LR[valor]
            cantidad = len(produccion.rhs)
            hijos = tuple(valores[len(valores) - cantidad:]) if cantidad else ()
            if cantidad:
                del valores[len(valores) - cantidad:]
                del pila_estados[len(pila_estados) - cantidad:]
            nodo = NodoParseo(produccion.lhs, hijos=hijos)
            valores.append(nodo)
            destino = tabla.gotos.get((pila_estados[-1], produccion.lhs))
            if destino is None:
                camino.append((tuple(pila_estados), posicion, "error de goto"))
                contador.acciones += 1
                return ResultadoDPDA(
                    aceptada=False,
                    camino=camino,
                    arbol=None,
                    contador=contador,
                    producciones=producciones_usadas,
                )
            pila_estados.append(destino)
            producciones_usadas.append(produccion)
            contador.reducciones += 1
            contador.acciones += 1
            continue

        contador.acciones += 1
        arbol = valores[-1] if valores else None
        return ResultadoDPDA(
            aceptada=True,
            camino=camino,
            arbol=arbol,
            contador=contador,
            producciones=producciones_usadas,
        )

    camino.append((tuple(pila_estados), posicion, "error: demasiados pasos"))
    contador.acciones += 1
    return ResultadoDPDA(
        aceptada=False,
        camino=camino,
        arbol=None,
        contador=contador,
        producciones=producciones_usadas,
    )


def imprimir_arbol(nodo: NodoParseo | None, prefijo: str = "", es_ultimo: bool = True) -> None:
    if nodo is None:
        print("  (sin arbol)")
        return
    conector = "└── " if es_ultimo else "├── "
    etiqueta = nodo.simbolo
    if nodo.token is not None:
        etiqueta = f"{nodo.simbolo} ({nodo.token})"
    print(prefijo + conector + etiqueta)
    nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
    for indice, hijo in enumerate(nodo.hijos):
        imprimir_arbol(hijo, nuevo_prefijo, indice == len(nodo.hijos) - 1)


def imprimir_resultado_dpda(resultado: ResultadoDPDA, tokens: list[str]) -> None:
    print("PDA determinista LR/SLR:")
    for pila, posicion, accion in resultado.camino:
        restante = " ".join(tokens[posicion:])
        if not restante:
            restante = "epsilon"
        pila_texto = " ".join(str(estado) for estado in pila)
        print(f"  Pila: {pila_texto:<18} Entrada: {restante:<28} Accion: {accion}")
    if resultado.aceptada:
        print("  Resultado: ACEPTADA")
        print("  Arbol de parseo:")
        imprimir_arbol(resultado.arbol, prefijo="  ")
    else:
        print("  Resultado: RECHAZADA")
    print(
        "  Operaciones: "
        f"total={resultado.contador.total}, "
        f"shifts={resultado.contador.shifts}, "
        f"reducciones={resultado.contador.reducciones}"
    )


def imprimir_resumen_slr(tabla: TablaSLR) -> None:
    print("PDA determinista LR/SLR:")
    print(f"  Estados LR(0): {len(tabla.estados)}")
    print(f"  Acciones: {len(tabla.acciones)}")
    print(f"  Gotos: {len(tabla.gotos)}")
    if tabla.conflictos:
        print("  Conflictos detectados:")
        for conflicto in tabla.conflictos:
            print(f"    - {conflicto}")
    else:
        print("  Sin conflictos: la tabla SLR(1) es determinista.")


def imprimir_tabla_slr(tabla: TablaSLR) -> None:
    print("Tabla SLR(1):")
    print("  Acciones:")
    for (estado, simbolo), accion in sorted(tabla.acciones.items()):
        print(f"    accion[{estado}, {simbolo}] = {_texto_accion(accion)}")
    print("  Gotos:")
    for (estado, simbolo), destino in sorted(tabla.gotos.items()):
        print(f"    goto[{estado}, {simbolo}] = {destino}")


def main(cadena: str) -> int:
    tabla = construir_tabla_slr()
    imprimir_resumen_slr(tabla)
    tokens = tokenizar(cadena)
    resultado = simular_dpda(tabla, tokens)
    imprimir_resultado_dpda(resultado, tokens)
    return 0 if resultado.aceptada else 1


if __name__ == "__main__":
    import sys

    entrada = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "he cooks"
    raise SystemExit(main(entrada))
