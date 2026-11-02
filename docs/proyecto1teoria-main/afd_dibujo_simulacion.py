# Módulo nuevo: simulación y dibujo del AFD obtenido por construcción
# directa (construccion_directa_afd.py), más una función de comparación
# contra la simulación del AFN (thompson_arbol.py).
#
# Está dividido en 4 partes independientes:
#   PARTE 1 — Simulación del AFD
#   PARTE 2 — Dibujo del AFD (Graphviz + Pillow, igual estilo que el AFN)
#   PARTE 3 — Comparación AFN vs AFD para una lista de cadenas
#   PARTE 4 — Función de conveniencia que hace todo el trabajo de la fase 2
#             para una expresión ya procesada (árbol -> AFD -> dibujo)
#
# No modifica ningún archivo existente; solo se importa desde ellos.

from __future__ import annotations

import os
import shutil
import tempfile

from construccion_directa_afd import AFD, MARCADOR_FIN, procesar_arbol_a_afd
import thompson_arbol as thompson

ESTADO_ERROR = "ERROR"  # etiqueta interna para "sin transición" (cadena rechazada)


# ---------------------------------------------------------------------------
# PARTE 1 — Simulación del AFD
# ---------------------------------------------------------------------------

def simular_afd(afd: AFD, cadena: str) -> bool:
    """Simula el AFD sobre una cadena de símbolos del alfabeto.

    A diferencia del AFN, el AFD no tiene transiciones-ε ni ambigüedad:
    en cada paso hay a lo sumo un estado siguiente. Si algún símbolo no
    tiene transición definida desde el estado actual, la cadena se
    rechaza de inmediato (no hay "estado trampa" explícito).
    """
    estado_actual = afd.inicial

    for simbolo in cadena:
        destino = afd.transiciones.get((estado_actual, simbolo))
        if destino is None:
            return False
        estado_actual = destino

    return estado_actual in afd.aceptacion


def simular_afd_con_traza(afd: AFD, cadena: str) -> tuple[bool, list[str]]:
    """Igual que simular_afd, pero además devuelve la traza de estados
    visitados (usando los nombres A, B, C... de afd.nombres) para poder
    imprimir el recorrido paso a paso."""
    estado_actual = afd.inicial
    traza = [afd.nombres.get(estado_actual, "?")]

    for simbolo in cadena:
        destino = afd.transiciones.get((estado_actual, simbolo))
        if destino is None:
            traza.append(ESTADO_ERROR)
            return False, traza
        estado_actual = destino
        traza.append(afd.nombres.get(estado_actual, "?"))

    return estado_actual in afd.aceptacion, traza


def imprimir_simulacion_afd(afd: AFD, cadena: str) -> bool:
    """Simula y ademas imprime la traza en formato 'A --a--> B --b--> C'."""
    cadena_norm = thompson.normalizar_cadena(cadena)
    aceptada, traza = simular_afd_con_traza(afd, cadena_norm)

    if cadena_norm == "":
        recorrido = traza[0]
    else:
        partes = [traza[0]]
        for simbolo, siguiente in zip(cadena_norm, traza[1:]):
            partes.append(f"--{simbolo}--> {siguiente}")
        recorrido = " ".join(partes)

    cadena_display = cadena_norm if cadena_norm else "ε"
    resultado = "aceptada" if aceptada else "rechazada"
    print(f"  Cadena: {cadena_display:<10} | Traza: {recorrido:<30} | {resultado}")
    return aceptada


# ---------------------------------------------------------------------------
# PARTE 2 — Dibujo del AFD
# ---------------------------------------------------------------------------

def dibujar_afd(afd: AFD, nombre_base: str, directorio: str = "AFDs") -> str | None:
    """Renderiza el AFD como JPEG con Graphviz + Pillow.

    Mismo estilo visual que thompson_arbol.dibujar_afn:
    - Estados de aceptación: doble círculo.
    - Estado inicial: flecha entrante desde un nodo invisible.
    - Una arista por símbolo del alfabeto (el marcador '#' no debe
      aparecer como símbolo de transición; solo se usa para detectar
      aceptación en construccion_directa_afd.py).
    """
    try:
        import graphviz
    except ImportError:
        print("  (Aviso: instale 'graphviz' con 'pip install graphviz'. "
              "Se omite el dibujo del AFD.)")
        return None

    if shutil.which('dot') is None:
        print("  (Aviso: el ejecutable 'dot' de Graphviz no esta en PATH. "
              "Instale Graphviz desde https://graphviz.org/download/ "
              "y asegurese de que 'dot' este disponible. Se omite el dibujo.)")
        return None

    dig = graphviz.Digraph(format='png')
    dig.attr(rankdir='LR', fontsize='10')

    # Nodo invisible que apunta al estado inicial (misma convención visual
    # que suele usarse para AFN/AFD: una flecha "de la nada" hacia el inicio).
    dig.node('__inicio__', label='', shape='none', width='0', height='0')

    for estado in afd.estados:
        nombre = afd.nombres[estado]
        attrs: dict[str, str] = {}
        if estado in afd.aceptacion:
            attrs['shape'] = 'doublecircle'
        dig.node(nombre, label=nombre, **attrs)

    dig.edge('__inicio__', afd.nombres[afd.inicial])

    for (origen, simbolo), destino in sorted(
        afd.transiciones.items(), key=lambda item: (afd.nombres[item[0][0]], item[0][1])
    ):
        dig.edge(afd.nombres[origen], afd.nombres[destino], label=simbolo)

    os.makedirs(directorio, exist_ok=True)
    ruta_base = os.path.join(directorio, nombre_base)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = dig.render(
                filename='afd_temp',
                directory=tmpdir,
                cleanup=True,
            )
            try:
                from PIL import Image
                jpg_path = f"{ruta_base}.jpg"
                with Image.open(png_path) as img:
                    rgb = img.convert('RGB')
                    rgb.save(jpg_path, 'JPEG', quality=90)
                print(f"  AFD guardado en: {jpg_path}")
                return jpg_path
            except ImportError:
                fallback = f"{ruta_base}.png"
                shutil.copy2(png_path, fallback)
                print(f"  (Aviso: Pillow no disponible; AFD guardado como PNG: {fallback})")
                return fallback
    except Exception as exc:
        print(f"  (Aviso: no se pudo renderizar el AFD: {exc})")
        return None


# ---------------------------------------------------------------------------
# PARTE 3 — Comparación AFN vs AFD para una lista de cadenas
# ---------------------------------------------------------------------------

def comparar_afn_afd(nfa: thompson.AFN, afd: AFD, cadenas: list[str]) -> bool:
    """Simula cada cadena en el AFN y en el AFD y verifica que coincidan.

    Devuelve True si TODAS las cadenas dieron el mismo resultado en
    ambos autómatas (lo cual es lo esperado, ya que el AFD reconoce el
    mismo lenguaje que el AFN). Imprime una tabla comparativa.
    """
    print("\nComparación AFN (Thompson) vs AFD (construcción directa):")
    print(f"  {'cadena':<10} {'AFN':<10} {'AFD':<10} {'coinciden'}")
    todo_coincide = True

    for cadena_raw in cadenas:
        cadena = thompson.normalizar_cadena(cadena_raw)
        acepta_afn = thompson.simular(nfa, cadena)
        acepta_afd = simular_afd(afd, cadena)
        coincide = acepta_afn == acepta_afd
        todo_coincide = todo_coincide and coincide

        cadena_display = cadena if cadena else 'ε'
        r_afn = 'yes' if acepta_afn else 'no'
        r_afd = 'yes' if acepta_afd else 'no'
        marca = 'sí' if coincide else 'NO ***'
        print(f"  {cadena_display:<10} {r_afn:<10} {r_afd:<10} {marca}")

    return todo_coincide


# ---------------------------------------------------------------------------
# PARTE 4 — Función de conveniencia: árbol -> AFD -> dibujo, en un paso
# ---------------------------------------------------------------------------

def construir_y_dibujar_afd(raiz, nombre_base: str, directorio: str = "AFDs") -> AFD:
    """A partir de la raíz del árbol sintáctico (sin extender con '#'):
    construye el AFD por construcción directa, imprime sus tablas
    (posiciones, followpos, estados, transiciones) y lo dibuja.

    Devuelve el objeto AFD ya construido, listo para simular_afd().
    """
    from construccion_directa_afd import imprimir_resultado_afd

    _, afd = procesar_arbol_a_afd(raiz)
    imprimir_resultado_afd(afd)
    dibujar_afd(afd, nombre_base, directorio=directorio)
    return afd