# Construcción de AFN mediante el algoritmo de Thompson (recorrido postorden
# del árbol sintáctico), simulación con clausura-ε, e impresión/renderizado.

from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field

import Arbol_sintactico as arbol

EPSILON = arbol.EPSILON


@dataclass
class Estado:
    id: int
    es_inicial: bool = False
    es_final: bool = False


@dataclass
class AFN:
    estados: dict[int, Estado] = field(default_factory=dict)
    iniciales: set[int] = field(default_factory=set)
    finales: set[int] = field(default_factory=set)
    transiciones: dict[tuple[int, str], set[int]] = field(default_factory=dict)

    def agregar_transicion(self, origen: int, simbolo: str, destino: int) -> None:
        clave = (origen, simbolo)
        if clave not in self.transiciones:
            self.transiciones[clave] = set()
        self.transiciones[clave].add(destino)

    def transiciones_desde(self, estado: int, simbolo: str) -> set[int]:
        return set(self.transiciones.get((estado, simbolo), set()))


@dataclass
class _Fragmento:
    inicio: int
    finales: set[int]


class _ConstructorThompson:
    """Genera un AFN completo con IDs de estado únicos."""

    def __init__(self) -> None:
        self.nfa = AFN()
        self._contador = 0

    def _nuevo_estado(self) -> int:
        estado_id = self._contador
        self._contador += 1
        self.nfa.estados[estado_id] = Estado(estado_id)
        return estado_id

    def _epsilon(self, origen: int, destino: int) -> None:
        self.nfa.agregar_transicion(origen, EPSILON, destino)

    def construir(self, nodo: arbol.NodoSintactico) -> _Fragmento:
        if nodo.es_hoja():
            inicio = self._nuevo_estado()
            fin = self._nuevo_estado()
            self.nfa.agregar_transicion(inicio, nodo.valor, fin)
            return _Fragmento(inicio, {fin})

        if nodo.valor == '*':
            interno = self.construir(nodo.izquierda)
            inicio = self._nuevo_estado()
            fin = self._nuevo_estado()
            self._epsilon(inicio, interno.inicio)
            self._epsilon(inicio, fin)
            for estado_fin in interno.finales:
                self._epsilon(estado_fin, fin)
                self._epsilon(estado_fin, interno.inicio)
            return _Fragmento(inicio, {fin})

        izquierda = self.construir(nodo.izquierda)
        derecha = self.construir(nodo.derecha)

        if nodo.valor == '.':
            for estado_fin in izquierda.finales:
                self._epsilon(estado_fin, derecha.inicio)
            return _Fragmento(izquierda.inicio, set(derecha.finales))

        if nodo.valor == '|':
            inicio = self._nuevo_estado()
            fin = self._nuevo_estado()
            self._epsilon(inicio, izquierda.inicio)
            self._epsilon(inicio, derecha.inicio)
            for estado_fin in izquierda.finales:
                self._epsilon(estado_fin, fin)
            for estado_fin in derecha.finales:
                self._epsilon(estado_fin, fin)
            return _Fragmento(inicio, {fin})

        raise ValueError(f"Operador no soportado en el árbol: {nodo.valor!r}")


def construir_afn_desde_arbol(raiz: arbol.NodoSintactico) -> AFN:
    """Construye un AFN aplicando Thompson en postorden sobre el árbol."""
    constructor = _ConstructorThompson()
    fragmento = constructor.construir(raiz)
    nfa = constructor.nfa
    nfa.iniciales = {fragmento.inicio}
    nfa.finales = set(fragmento.finales)
    for estado_id in nfa.iniciales:
        nfa.estados[estado_id].es_inicial = True
    for estado_id in nfa.finales:
        nfa.estados[estado_id].es_final = True
    return nfa


def epsilon_clausura(estados: set[int], nfa: AFN) -> set[int]:
    """Clausura-ε de un conjunto de estados."""
    pila = list(estados)
    clausura = set(estados)
    while pila:
        actual = pila.pop()
        for destino in nfa.transiciones_desde(actual, EPSILON):
            if destino not in clausura:
                clausura.add(destino)
                pila.append(destino)
    return clausura


def simular(nfa: AFN, cadena: str) -> bool:
    """Simula el AFN sobre una cadena. Devuelve True si es aceptada."""
    estados = epsilon_clausura(set(nfa.iniciales), nfa)
    for simbolo in cadena:
        siguientes: set[int] = set()
        for estado in estados:
            siguientes.update(nfa.transiciones_desde(estado, simbolo))
        estados = epsilon_clausura(siguientes, nfa)
        if not estados:
            return False
    return bool(estados & nfa.finales)


def normalizar_cadena(cadena: str) -> str:
    """Normaliza una cadena de entrada: E/ε/vacío -> cadena vacía."""
    cadena = cadena.strip()
    if cadena in ('', EPSILON, arbol.ALIAS_EPSILON):
        return ''
    return cadena


def imprimir_afn(nfa: AFN) -> None:
    """Imprime estados, iniciales, finales y transiciones del AFN."""
    print(f"  Estados ({len(nfa.estados)}): {sorted(nfa.estados.keys())}")
    print(f"  Iniciales: {sorted(nfa.iniciales)}")
    print(f"  Finales: {sorted(nfa.finales)}")
    print("  Transiciones:")
    for (origen, simbolo), destinos in sorted(nfa.transiciones.items()):
        dest_str = ', '.join(str(d) for d in sorted(destinos))
        etiqueta = 'e' if simbolo == EPSILON else simbolo
        print(f"    {origen} --{etiqueta}--> {dest_str}")


def _slug_desde_regex(regex: str, max_len: int = 20) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', regex)
    slug = slug.strip('-').lower()
    if not slug:
        slug = 'regex'
    return slug[:max_len]


def dibujar_afn(nfa: AFN, nombre_base: str, directorio: str = "AFNs") -> str | None:
    """Renderiza el AFN como JPEG con Graphviz + Pillow. Devuelve la ruta o None."""
    try:
        import graphviz
    except ImportError:
        print("  (Aviso: instale 'graphviz' con 'pip install graphviz'. "
              "Se omite el dibujo del AFN.)")
        return None

    if shutil.which('dot') is None:
        print("  (Aviso: el ejecutable 'dot' de Graphviz no esta en PATH. "
              "Instale Graphviz desde https://graphviz.org/download/ "
              "y asegurese de que 'dot' este disponible. Se omite el dibujo.)")
        return None

    dig = graphviz.Digraph(format='png')
    dig.attr(rankdir='LR', fontsize='10')

    for estado_id, estado in sorted(nfa.estados.items()):
        attrs: dict[str, str] = {}
        if estado.es_final:
            attrs['shape'] = 'doublecircle'
        dig.node(str(estado_id), label=str(estado_id), **attrs)

    for (origen, simbolo), destinos in sorted(nfa.transiciones.items()):
        etiqueta = 'e' if simbolo == EPSILON else simbolo
        for destino in sorted(destinos):
            dig.edge(str(origen), str(destino), label=etiqueta)

    os.makedirs(directorio, exist_ok=True)
    ruta_base = os.path.join(directorio, nombre_base)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = dig.render(
                filename='afn_temp',
                directory=tmpdir,
                cleanup=True,
            )
            try:
                from PIL import Image
                jpg_path = f"{ruta_base}.jpg"
                with Image.open(png_path) as img:
                    rgb = img.convert('RGB')
                    rgb.save(jpg_path, 'JPEG', quality=90)
                print(f"  AFN guardado en: {jpg_path}")
                return jpg_path
            except ImportError:
                fallback = f"{ruta_base}.png"
                shutil.copy2(png_path, fallback)
                print(f"  (Aviso: Pillow no disponible; AFN guardado como PNG: {fallback})")
                return fallback
    except Exception as exc:
        print(f"  (Aviso: no se pudo renderizar el AFN: {exc})")
        return None
