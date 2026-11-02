from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from gramatica import (
    INICIAL,
    PRODUCCIONES,
    PRODUCCIONES_POR_LHS,
    TERMINALES,
    tokenizar,
)

Z0 = "Z0"
Q0 = "q0"
Q1 = "q1"
Q2 = "q2"

Transicion = tuple[str, tuple[str, ...]]


@dataclass
class PDA:
    estados: tuple[str, ...]
    alfabeto_entrada: frozenset[str]
    alfabeto_pila: frozenset[str]
    inicial: str
    simbolo_inicial_pila: str
    aceptacion: frozenset[str]
    transiciones: dict[tuple[str, str | None, str], list[Transicion]] = field(
        default_factory=dict
    )

    def agregar_transicion(
        self,
        estado: str,
        simbolo_entrada: str | None,
        tope: str,
        nuevo_estado: str,
        empujar: tuple[str, ...],
    ) -> None:
        clave = (estado, simbolo_entrada, tope)
        self.transiciones.setdefault(clave, []).append((nuevo_estado, empujar))

    def transiciones_para(
        self, estado: str, simbolo_entrada: str | None, tope: str
    ) -> list[Transicion]:
        return list(self.transiciones.get((estado, simbolo_entrada, tope), []))


@dataclass(frozen=True)
class Configuracion:
    estado: str
    posicion: int
    pila: tuple[str, ...]


@dataclass
class ContadorPDA:
    transiciones_evaluadas: int = 0
    operaciones_pila: int = 0
    comparaciones_simbolo: int = 0
    configuraciones_procesadas: int = 0

    @property
    def total(self) -> int:
        return (
            self.transiciones_evaluadas
            + self.operaciones_pila
            + self.comparaciones_simbolo
        )


@dataclass
class ResultadoPDA:
    aceptada: bool
    camino: list[tuple[Configuracion, str]]
    contador: ContadorPDA
    configuraciones_visitadas: int
    limite_alcanzado: bool = False


def construir_pda_desde_gramatica() -> PDA:
    alfabeto_pila = frozenset(
        set(TERMINALES)
        | {produccion.lhs for produccion in PRODUCCIONES}
        | {Z0}
    )
    pda = PDA(
        estados=(Q0, Q1, Q2),
        alfabeto_entrada=frozenset(TERMINALES),
        alfabeto_pila=alfabeto_pila,
        inicial=Q0,
        simbolo_inicial_pila=Z0,
        aceptacion=frozenset({Q2}),
    )

    pda.agregar_transicion(Q0, None, Z0, Q1, (INICIAL, Z0))

    for produccion in PRODUCCIONES:
        pda.agregar_transicion(Q1, None, produccion.lhs, Q1, produccion.rhs)

    for terminal in sorted(TERMINALES):
        pda.agregar_transicion(Q1, terminal, terminal, Q1, ())

    pda.agregar_transicion(Q1, None, Z0, Q2, (Z0,))
    return pda


def _aplicar_transicion(pila: tuple[str, ...], empujar: tuple[str, ...]) -> tuple[str, ...]:
    return pila[:-1] + tuple(reversed(empujar))


def _simbolos_pila_sin_fondo(pila: tuple[str, ...]) -> int:
    return sum(1 for simbolo in pila if simbolo != Z0)


def _etiqueta_transicion(
    pda_estado: str,
    tope: str,
    nuevo_estado: str,
    empujar: tuple[str, ...],
    simbolo_entrada: str | None,
) -> str:
    if nuevo_estado == Q2:
        return "aceptar"
    if simbolo_entrada is not None:
        return f"consumir '{simbolo_entrada}'"
    if pda_estado == Q0:
        return f"iniciar con {INICIAL}"
    return f"expandir {tope} -> {' '.join(empujar)}"


def simular_pda(
    pda: PDA,
    cadena: str | list[str],
    max_configuraciones: int = 2_000_000,
) -> ResultadoPDA:
    tokens = tokenizar(cadena) if isinstance(cadena, str) else list(cadena)
    n = len(tokens)
    inicial = Configuracion(pda.inicial, 0, (pda.simbolo_inicial_pila,))
    contador = ContadorPDA()
    cola: deque[Configuracion] = deque([inicial])
    visitados: set[Configuracion] = {inicial}
    padres: dict[Configuracion, tuple[Configuracion | None, str]] = {
        inicial: (None, "inicio")
    }
    primer_callejon: Configuracion | None = None
    limite_alcanzado = False

    while cola:
        if len(visitados) >= max_configuraciones:
            limite_alcanzado = True
            break

        actual = cola.popleft()
        contador.configuraciones_procesadas += 1

        if actual.estado in pda.aceptacion and actual.posicion == n:
            camino = _reconstruir_camino(actual, padres, tokens)
            return ResultadoPDA(
                aceptada=True,
                camino=camino,
                contador=contador,
                configuraciones_visitadas=len(visitados),
                limite_alcanzado=False,
            )

        tope = actual.pila[-1]
        sucesores: list[tuple[Configuracion, str]] = []

        for nuevo_estado, empujar in pda.transiciones_para(actual.estado, None, tope):
            contador.transiciones_evaluadas += 1
            nueva_pila = _aplicar_transicion(actual.pila, empujar)
            contador.operaciones_pila += max(1, len(empujar))
            sucesor = Configuracion(nuevo_estado, actual.posicion, nueva_pila)
            etiqueta = _etiqueta_transicion(
                actual.estado, tope, nuevo_estado, empujar, None
            )
            sucesores.append((sucesor, etiqueta))

        if actual.posicion < n:
            simbolo = tokens[actual.posicion]
            for nuevo_estado, empujar in pda.transiciones_para(
                actual.estado, simbolo, tope
            ):
                contador.transiciones_evaluadas += 1
                contador.comparaciones_simbolo += 1
                nueva_pila = _aplicar_transicion(actual.pila, empujar)
                contador.operaciones_pila += max(1, len(empujar))
                sucesor = Configuracion(nuevo_estado, actual.posicion + 1, nueva_pila)
                etiqueta = _etiqueta_transicion(
                    actual.estado, tope, nuevo_estado, empujar, simbolo
                )
                sucesores.append((sucesor, etiqueta))

        if not sucesores and actual.estado != Q2 and primer_callejon is None:
            primer_callejon = actual

        for sucesor, etiqueta in sucesores:
            if sucesor.posicion > n:
                continue
            restantes = n - sucesor.posicion
            if (
                sucesor.estado != Q2
                and _simbolos_pila_sin_fondo(sucesor.pila) > restantes
            ):
                continue
            if sucesor in visitados:
                continue
            visitados.add(sucesor)
            padres[sucesor] = (actual, etiqueta)
            cola.append(sucesor)

    objetivo = primer_callejon or inicial
    camino = _reconstruir_camino(objetivo, padres, tokens)
    return ResultadoPDA(
        aceptada=False,
        camino=camino,
        contador=contador,
        configuraciones_visitadas=len(visitados),
        limite_alcanzado=limite_alcanzado,
    )


def _reconstruir_camino(
    objetivo: Configuracion,
    padres: dict[Configuracion, tuple[Configuracion | None, str]],
    tokens: list[str],
) -> list[tuple[Configuracion, str]]:
    pasos: list[tuple[Configuracion, str]] = []
    actual: Configuracion | None = objetivo
    while actual is not None:
        padre, etiqueta = padres[actual]
        pasos.append((actual, etiqueta))
        actual = padre
    pasos.reverse()
    return pasos


def formatear_configuracion(configuracion: Configuracion, tokens: list[str]) -> str:
    restante = " ".join(tokens[configuracion.posicion:])
    if not restante:
        restante = "epsilon"
    pila = " ".join(reversed(configuracion.pila))
    return f"({configuracion.estado}, {restante}, {pila})"


def imprimir_resultado_pda(resultado: ResultadoPDA, tokens: list[str]) -> None:
    print("PDA no determinista (conversion CFG -> PDA):")
    for indice, (configuracion, etiqueta) in enumerate(resultado.camino):
        texto = formatear_configuracion(configuracion, tokens)
        if indice == 0:
            print(f"  {texto}")
        else:
            print(f"  |- {texto}    [{etiqueta}]")
    if resultado.aceptada:
        print("  Resultado: ACEPTADA")
    elif resultado.limite_alcanzado:
        print("  Resultado: INDETERMINADO (se alcanzo el limite de configuraciones)")
    else:
        print("  Resultado: RECHAZADA")
    print(
        "  Operaciones: "
        f"total={resultado.contador.total}, "
        f"transiciones={resultado.contador.transiciones_evaluadas}, "
        f"pila={resultado.contador.operaciones_pila}, "
        f"comparaciones={resultado.contador.comparaciones_simbolo}, "
        f"configuraciones={resultado.configuraciones_visitadas}"
    )


def imprimir_resumen_pda(pda: PDA) -> None:
    print("Definicion del PDA:")
    print(f"  Estados: {', '.join(pda.estados)}")
    print(f"  Estado inicial: {pda.inicial}")
    print(f"  Estados de aceptacion: {', '.join(sorted(pda.aceptacion))}")
    print(f"  Simbolo inicial de pila: {pda.simbolo_inicial_pila}")
    print(f"  Alfabeto de entrada: {{{', '.join(sorted(pda.alfabeto_entrada))}}}")
    print(f"  Alfabeto de pila: {{{', '.join(sorted(pda.alfabeto_pila))}}}")
    print("  Transiciones por produccion:")
    for lhs, producciones in PRODUCCIONES_POR_LHS.items():
        destinos = []
        for produccion in producciones:
            destinos.append(f"{produccion.texto}")
        print(f"    δ({Q1}, epsilon, {lhs}) -> q1 empujando: {' | '.join(destinos)}")
    print(f"    δ({Q0}, epsilon, {Z0}) -> q1 empujando {INICIAL} {Z0}")
    print(f"    δ({Q1}, a, a) -> q1 para cada terminal a")
    print(f"    δ({Q1}, epsilon, {Z0}) -> q2")


def imprimir_tabla_pda(pda: PDA) -> None:
    print("Tabla completa de transiciones del PDA:")
    for (estado, simbolo, tope), destinos in sorted(
        pda.transiciones.items(),
        key=lambda item: (item[0][0], item[0][1] or "", item[0][2]),
    ):
        entrada = "epsilon" if simbolo is None else simbolo
        for nuevo_estado, empujar in destinos:
            pila = " ".join(empujar) if empujar else "epsilon"
            print(
                f"  δ({estado}, {entrada}, {tope}) = "
                f"({nuevo_estado}, {pila})"
            )


def main(cadena: str) -> int:
    pda = construir_pda_desde_gramatica()
    imprimir_resumen_pda(pda)
    tokens = tokenizar(cadena)
    resultado = simular_pda(pda, tokens)
    imprimir_resultado_pda(resultado, tokens)
    return 0 if resultado.aceptada else 1


if __name__ == "__main__":
    import sys

    entrada = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "he cooks"
    raise SystemExit(main(entrada))
