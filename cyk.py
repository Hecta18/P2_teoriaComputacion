from __future__ import annotations

from dataclasses import dataclass, field

from gramatica import (
    INICIAL,
    PRODUCCIONES_BINARIAS,
    PRODUCCIONES_TERMINALES,
    tokenizar,
)


@dataclass
class ContadorCYK:
    comprobaciones_terminales: int = 0
    comprobaciones_binarias: int = 0
    inserciones: int = 0

    @property
    def total(self) -> int:
        return (
            self.comprobaciones_terminales
            + self.comprobaciones_binarias
            + self.inserciones
        )


@dataclass(frozen=True)
class NodoDerivacion:
    simbolo: str
    hijos: tuple["NodoDerivacion", ...] = ()
    token: str | None = None

    @property
    def es_hoja(self) -> bool:
        return not self.hijos


@dataclass(frozen=True)
class OrigenTerminal:
    token: str


@dataclass(frozen=True)
class OrigenBinario:
    k: int
    izquierdo: str
    derecho: str


Origen = OrigenTerminal | OrigenBinario


@dataclass
class ResultadoCYK:
    aceptada: bool
    tabla: list[list[set[str]]]
    origenes: dict[tuple[str, int, int], list[Origen]]
    eventos: list[str]
    contador: ContadorCYK
    tokens: list[str] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.tokens)


def _texto_celda(tokens: list[str], i: int, j: int) -> str:
    return " ".join(tokens[i:j])


def cyk(cadena: str | list[str]) -> ResultadoCYK:
    tokens = tokenizar(cadena) if isinstance(cadena, str) else list(cadena)
    n = len(tokens)
    tabla: list[list[set[str]]] = [[set() for _ in range(n + 1)] for _ in range(n + 1)]
    origenes: dict[tuple[str, int, int], list[Origen]] = {}
    eventos: list[str] = []
    contador = ContadorCYK()

    for i in range(n):
        for produccion in PRODUCCIONES_TERMINALES:
            contador.comprobaciones_terminales += 1
            if produccion.rhs[0] != tokens[i]:
                continue
            celda = tabla[i][i + 1]
            nueva = produccion.lhs not in celda
            celda.add(produccion.lhs)
            origenes.setdefault((produccion.lhs, i, i + 1), []).append(
                OrigenTerminal(tokens[i])
            )
            if nueva:
                contador.inserciones += 1
            eventos.append(
                f"[{i},{i + 1}) '{tokens[i]}' += {produccion.lhs}"
                f"    ({produccion.texto})"
            )

    for longitud in range(2, n + 1):
        for i in range(0, n - longitud + 1):
            j = i + longitud
            for k in range(i + 1, j):
                for produccion in PRODUCCIONES_BINARIAS:
                    contador.comprobaciones_binarias += 1
                    izquierdo, derecho = produccion.rhs
                    if izquierdo not in tabla[i][k] or derecho not in tabla[k][j]:
                        continue
                    celda = tabla[i][j]
                    nueva = produccion.lhs not in celda
                    celda.add(produccion.lhs)
                    origenes.setdefault((produccion.lhs, i, j), []).append(
                        OrigenBinario(k, izquierdo, derecho)
                    )
                    if nueva:
                        contador.inserciones += 1
                    eventos.append(
                        f"[{i},{j}) '{_texto_celda(tokens, i, j)}' += {produccion.lhs}"
                        f"    ({produccion.texto}; k={k}, "
                        f"{izquierdo} en [{i},{k}) y {derecho} en [{k},{j}))"
                    )

    aceptada = INICIAL in tabla[0][n] if n else False
    return ResultadoCYK(
        aceptada=aceptada,
        tabla=tabla,
        origenes=origenes,
        eventos=eventos,
        contador=contador,
        tokens=tokens,
    )


def _contar_derivaciones(resultado: ResultadoCYK) -> int:
    if not resultado.aceptada:
        return 0
    memo: dict[tuple[str, int, int], int] = {}

    def contar(simbolo: str, i: int, j: int) -> int:
        clave = (simbolo, i, j)
        if clave in memo:
            return memo[clave]
        total = 0
        for origen in resultado.origenes.get(clave, []):
            if isinstance(origen, OrigenTerminal):
                total += 1
            else:
                total += contar(origen.izquierdo, i, origen.k) * contar(
                    origen.derecho, origen.k, j
                )
        memo[clave] = total
        return total

    return contar(INICIAL, 0, resultado.n)


def reconstruir_derivaciones(
    resultado: ResultadoCYK, maximo: int = 5
) -> list[NodoDerivacion]:
    if not resultado.aceptada:
        return []
    memo: dict[tuple[str, int, int], list[NodoDerivacion]] = {}

    def reconstruir(simbolo: str, i: int, j: int) -> list[NodoDerivacion]:
        clave = (simbolo, i, j)
        if clave in memo:
            return memo[clave]
        arboles: list[NodoDerivacion] = []
        for origen in resultado.origenes.get(clave, []):
            if len(arboles) >= maximo:
                break
            if isinstance(origen, OrigenTerminal):
                arboles.append(NodoDerivacion(simbolo, token=origen.token))
                continue
            for arbol_izquierdo in reconstruir(origen.izquierdo, i, origen.k):
                for arbol_derecho in reconstruir(origen.derecho, origen.k, j):
                    arboles.append(
                        NodoDerivacion(simbolo, (arbol_izquierdo, arbol_derecho))
                    )
                    if len(arboles) >= maximo:
                        break
                if len(arboles) >= maximo:
                    break
        memo[clave] = arboles
        return arboles

    return reconstruir(INICIAL, 0, resultado.n)


def derivacion_izquierda(arbol: NodoDerivacion) -> list[str]:
    reglas: list[tuple[str, tuple[str, ...]]] = []

    def recorrer(nodo: NodoDerivacion) -> None:
        if nodo.token is not None:
            reglas.append((nodo.simbolo, (nodo.token,)))
            return
        reglas.append((nodo.simbolo, tuple(hijo.simbolo for hijo in nodo.hijos)))
        for hijo in nodo.hijos:
            recorrer(hijo)

    recorrer(arbol)
    forma: list[str] = [arbol.simbolo]
    pasos = [" ".join(forma)]
    for lhs, rhs in reglas:
        indice = forma.index(lhs)
        forma = forma[:indice] + list(rhs) + forma[indice + 1:]
        pasos.append(" ".join(forma))
    return pasos


def imprimir_arbol(nodo: NodoDerivacion | None, prefijo: str = "", es_ultimo: bool = True) -> None:
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


def imprimir_tabla(resultado: ResultadoCYK) -> None:
    print("Tabla CYK:")
    if resultado.n == 0:
        print("  (cadena vacia: la gramatica no genera epsilon)")
        return
    for longitud in range(1, resultado.n + 1):
        print(f"  Longitud {longitud}:")
        for i in range(0, resultado.n - longitud + 1):
            j = i + longitud
            contenido = resultado.tabla[i][j]
            texto = "{" + ", ".join(sorted(contenido)) + "}" if contenido else "{}"
            print(f"    [{i},{j}) '{_texto_celda(resultado.tokens, i, j)}' -> {texto}")


def imprimir_resultado_cyk(resultado: ResultadoCYK, max_derivaciones: int = 3) -> None:
    print("CYK:")
    print("  Pasos de llenado:")
    if resultado.eventos:
        for evento in resultado.eventos:
            print(f"    {evento}")
    else:
        print("    (sin coincidencias)")
    imprimir_tabla(resultado)
    if resultado.aceptada:
        print("  Resultado: ACEPTADA")
        total = _contar_derivaciones(resultado)
        print(f"  Derivaciones encontradas: {total}")
        arboles = reconstruir_derivaciones(resultado, maximo=max_derivaciones)
        for indice, arbol in enumerate(arboles, 1):
            print(f"  Arbol {indice}:")
            imprimir_arbol(arbol, prefijo="  ")
            print("  Derivacion por la izquierda:")
            pasos = derivacion_izquierda(arbol)
            print(f"    {pasos[0]}")
            for paso in pasos[1:]:
                print(f"    => {paso}")
    else:
        print("  Resultado: RECHAZADA")
    print(
        "  Operaciones: "
        f"total={resultado.contador.total}, "
        f"terminales={resultado.contador.comprobaciones_terminales}, "
        f"binarias={resultado.contador.comprobaciones_binarias}, "
        f"inserciones={resultado.contador.inserciones}"
    )


def main(cadena: str) -> int:
    resultado = cyk(cadena)
    imprimir_resultado_cyk(resultado)
    return 0 if resultado.aceptada else 1


if __name__ == "__main__":
    import sys

    entrada = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "he cooks"
    raise SystemExit(main(entrada))
