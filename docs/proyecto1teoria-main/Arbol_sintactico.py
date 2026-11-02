# Construcción del árbol sintáctico de una expresión regular a
# partir de su forma postfix (generada por shunting_yard_regex.py).
#
# Convenciones:
#   - ε (épsilon) se escribe como el carácter 'ε' o, como alternativa ASCII,
#     la letra mayúscula 'E' (ver ALIAS_EPSILON).
#   - '+' y '?' NO aparecen como nodos en el árbol final: se expanden al
#     construirlo, según las equivalencias clásicas:
#         p+  ≡  p . p*      (una o más repeticiones)
#         p?  ≡  (p | ε)     (cero o una repetición)
#     Por eso el árbol resultante solo contiene los operadores '.', '|', '*'
#     y hojas (símbolos del alfabeto o ε).

import os

EPSILON = 'ε'
ALIAS_EPSILON = 'E'
MARCADOR_FIN = '#'

OPERADORES_BINARIOS = {'.', '|'}


class NodoSintactico:
    """Nodo del árbol sintáctico de una expresión regular.

    - Hoja (símbolo del alfabeto, ε o '#'): izquierda = derecha = None.
    - Nodo unario ('*'): solo usa 'izquierda'.
    - Nodo binario ('.' o '|'): usa 'izquierda' y 'derecha'.

    Campos opcionales para construcción directa de AFD (fase 2):
    - posicion: número de posición en hojas del alfabeto / '#'.
    - nullable, firstpos, lastpos: atributos computados bottom-up.
    """

    def __init__(self, valor: str, izquierda: "NodoSintactico | None" = None,
                 derecha: "NodoSintactico | None" = None):
        self.valor = valor
        self.izquierda = izquierda
        self.derecha = derecha
        self.posicion: int | None = None
        self.nullable: bool | None = None
        self.firstpos: set[int] = set()
        self.lastpos: set[int] = set()

    def es_hoja(self) -> bool:
        return self.izquierda is None and self.derecha is None

    def etiqueta(self) -> str:
        """Etiqueta para imprimir/dibujar; incluye posición si existe."""
        if self.posicion is not None:
            return f"{self.valor}:{self.posicion}"
        return str(self.valor)

    def __repr__(self) -> str:  # útil para depuración
        if self.posicion is not None:
            return f"NodoSintactico({self.valor!r}, pos={self.posicion})"
        return f"NodoSintactico({self.valor!r})"


def _normalizar_operando(token: str) -> str:
    """Aplica la convención ALIAS_EPSILON → EPSILON a un operando."""
    return EPSILON if token == ALIAS_EPSILON else token


def _clonar(nodo: NodoSintactico) -> NodoSintactico:
    """Copia profunda de un subárbol (para no compartir nodos entre ramas)."""
    if nodo is None:
        return None
    return NodoSintactico(nodo.valor, _clonar(nodo.izquierda), _clonar(nodo.derecha))


def construir_arbol(postfix: list[str]) -> NodoSintactico:
    """Construye el árbol sintáctico a partir de una lista postfix.

    Recorre el postfix de izquierda a derecha apilando hojas y, al
    encontrar un operador, desapila sus operandos y arma el subárbol
    correspondiente. '+' y '?' se expanden en el momento según las
    equivalencias documentadas arriba.
    """
    pila: list[NodoSintactico] = []

    for token in postfix:
        if token in OPERADORES_BINARIOS:
            if len(pila) < 2:
                raise ValueError(f"Postfix inválido: faltan operandos para '{token}'")
            derecha = pila.pop()
            izquierda = pila.pop()
            pila.append(NodoSintactico(token, izquierda, derecha))

        elif token == '*':
            if not pila:
                raise ValueError("Postfix inválido: falta operando para '*'")
            hijo = pila.pop()
            pila.append(NodoSintactico('*', hijo))

        elif token == '+':
            # p+  ≡  p . p*   (se duplica el subárbol: original + copia bajo '*')
            if not pila:
                raise ValueError("Postfix inválido: falta operando para '+'")
            hijo = pila.pop()
            copia = _clonar(hijo)
            estrella = NodoSintactico('*', copia)
            pila.append(NodoSintactico('.', hijo, estrella))

        elif token == '?':
            # p?  ≡  (p | ε)
            if not pila:
                raise ValueError("Postfix inválido: falta operando para '?'")
            hijo = pila.pop()
            hoja_epsilon = NodoSintactico(EPSILON)
            pila.append(NodoSintactico('|', hijo, hoja_epsilon))

        else:
            pila.append(NodoSintactico(_normalizar_operando(token)))

    if len(pila) != 1:
        raise ValueError("Postfix inválido: no se redujo a un único árbol")
    return pila.pop()


def imprimir_arbol(nodo: NodoSintactico, prefijo: str = "", es_ultimo: bool = True) -> None:
    """Imprime el árbol en consola con conectores tipo 'tree' de Unix."""
    conector = "└── " if es_ultimo else "├── "
    print(prefijo + conector + nodo.etiqueta())
    hijos = [h for h in (nodo.izquierda, nodo.derecha) if h is not None]
    nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
    for i, hijo in enumerate(hijos):
        imprimir_arbol(hijo, nuevo_prefijo, i == len(hijos) - 1)


def recorrido_postorden(nodo: NodoSintactico) -> list[str]:
    """Recorrido en profundidad postorden (izquierda, derecha, raíz)."""
    if nodo is None:
        return []
    resultado: list[str] = []
    if nodo.izquierda is not None:
        resultado.extend(recorrido_postorden(nodo.izquierda))
    if nodo.derecha is not None:
        resultado.extend(recorrido_postorden(nodo.derecha))
    resultado.append(nodo.etiqueta())
    return resultado
