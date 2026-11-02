from __future__ import annotations

from dataclasses import dataclass

INICIAL = "S"

NO_TERMINALES = ("S", "VP", "PP", "NP", "V", "P", "N", "Det")

TERMINALES = frozenset({
    "cooks", "drinks", "eats", "cuts",
    "in", "with",
    "he", "she",
    "cat", "dog",
    "beer", "cake", "juice", "meat", "soup",
    "fork", "knife", "oven", "spoon",
    "a", "the",
})


@dataclass(frozen=True)
class Produccion:
    id: int
    lhs: str
    rhs: tuple[str, ...]

    @property
    def texto(self) -> str:
        return f"{self.lhs} -> {' '.join(self.rhs)}"


_PRODUCCIONES_CRUDAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("S", ("NP", "VP")),
    ("VP", ("VP", "PP")),
    ("VP", ("V", "NP")),
    ("VP", ("cooks",)),
    ("VP", ("drinks",)),
    ("VP", ("eats",)),
    ("VP", ("cuts",)),
    ("PP", ("P", "NP")),
    ("NP", ("Det", "N")),
    ("NP", ("he",)),
    ("NP", ("she",)),
    ("V", ("cooks",)),
    ("V", ("drinks",)),
    ("V", ("eats",)),
    ("V", ("cuts",)),
    ("P", ("in",)),
    ("P", ("with",)),
    ("N", ("cat",)),
    ("N", ("dog",)),
    ("N", ("beer",)),
    ("N", ("cake",)),
    ("N", ("juice",)),
    ("N", ("meat",)),
    ("N", ("soup",)),
    ("N", ("fork",)),
    ("N", ("knife",)),
    ("N", ("oven",)),
    ("N", ("spoon",)),
    ("Det", ("a",)),
    ("Det", ("the",)),
)

PRODUCCIONES: tuple[Produccion, ...] = tuple(
    Produccion(indice, lhs, rhs)
    for indice, (lhs, rhs) in enumerate(_PRODUCCIONES_CRUDAS)
)

PRODUCCIONES_POR_LHS: dict[str, tuple[Produccion, ...]] = {
    no_terminal: tuple(p for p in PRODUCCIONES if p.lhs == no_terminal)
    for no_terminal in NO_TERMINALES
}

PRODUCCIONES_BINARIAS: tuple[Produccion, ...] = tuple(
    p for p in PRODUCCIONES
    if len(p.rhs) == 2 and all(s in NO_TERMINALES for s in p.rhs)
)

PRODUCCIONES_TERMINALES: tuple[Produccion, ...] = tuple(
    p for p in PRODUCCIONES
    if len(p.rhs) == 1 and p.rhs[0] in TERMINALES
)


def tokenizar(cadena: str) -> list[str]:
    return cadena.strip().lower().split()


def produccion_por_id(indice: int) -> Produccion:
    return PRODUCCIONES[indice]


def errores_cnf() -> list[str]:
    errores: list[str] = []
    for produccion in PRODUCCIONES:
        if produccion.lhs not in NO_TERMINALES:
            errores.append(f"{produccion.texto}: lado izquierdo invalido")
            continue
        if len(produccion.rhs) == 1:
            if produccion.rhs[0] not in TERMINALES:
                errores.append(f"{produccion.texto}: produccion terminal invalida")
        elif len(produccion.rhs) == 2:
            if not all(simbolo in NO_TERMINALES for simbolo in produccion.rhs):
                errores.append(f"{produccion.texto}: produccion binaria invalida")
        else:
            errores.append(f"{produccion.texto}: longitud de lado derecho invalida")
    return errores


def esta_en_cnf() -> bool:
    return not errores_cnf()


def imprimir_gramatica() -> None:
    print("Gramatica G = (V, Sigma, S, P)")
    print(f"  V = {{{', '.join(NO_TERMINALES)}}}")
    print(f"  Sigma = {{{', '.join(sorted(TERMINALES))}}}")
    print(f"  S = {INICIAL}")
    print("  P:")
    for produccion in PRODUCCIONES:
        print(f"    {produccion.id:>2}. {produccion.texto}")
    errores = errores_cnf()
    if errores:
        print("  La gramatica NO esta en forma normal de Chomsky:")
        for error in errores:
            print(f"    - {error}")
    else:
        print("  La gramatica esta en forma normal de Chomsky (CNF).")


if __name__ == "__main__":
    imprimir_gramatica()
