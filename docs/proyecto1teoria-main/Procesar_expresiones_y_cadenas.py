# Lee un archivo de texto con expresiones regulares y cadenas de simbolos,
# cada uno en una línea, la ejecución completa es:
#   1) tokenización + concatenación implícita (infix)
#   2) conversión a postfix (Shunting Yard, shunting_yard_regex.py)
#   3) construcción del árbol sintáctico
#   4) construcción del AFN con el algoritmo de Thompson (thompson_arbol.py)
#      y dibujo del AFN
#   5) construcción del AFD por subconjuntos (ε-clausura + move), a partir
#      del AFN (construccion_subconjuntos.py), y dibujo del AFD
#   6) minimización del AFD por subconjuntos con partición/refinamiento
#      (minimizacion_afd.py), y dibujo del AFD mínimo
#   7) construcción del AFD por construcción directa (followpos), a partir
#      del mismo árbol sintáctico (construccion_directa_afd.py), y dibujo
#   8) minimización del AFD por construcción directa (mismo módulo que el
#      paso 6), y dibujo
#   9) simulación de cada cadena contra el AFN y contra los cuatro AFD
#  10) verificación de que todos reconocen el mismo lenguaje en cada cadena

import os
import sys

import regex_tokenize
import shunting_yard_regex as shyR
import Arbol_sintactico as arbol
import thompson_arbol as thompson
import construccion_directa_afd as afd_directo
import construccion_subconjuntos as subconjuntos
import minimizacion_afd as minimo
import afd_dibujo_simulacion as afd_mod

MARCADOR_CADENAS = '# --- Cadenas ---'
RUTAS_ENTRADA = ('expresiones_y_cadenas', 'expresiones_y_cadenas.txt')


def _es_comentario(linea: str) -> bool:
    return linea.startswith('#') and linea != MARCADOR_CADENAS


def leer_expresiones_y_cadenas(ruta: str) -> tuple[list[str], list[str]]:
    """Lee el archivo y devuelve (expresiones, cadenas) en dos secciones."""
    with open(ruta, encoding='utf-8') as archivo:
        lineas_raw = archivo.readlines()

    expresiones: list[str] = []
    cadenas: list[str] = []
    seccion_cadenas = False

    for linea_raw in lineas_raw:
        linea = linea_raw.rstrip('\n\r')
        if linea.strip() == MARCADOR_CADENAS:
            seccion_cadenas = True
            continue
        if _es_comentario(linea.strip()):
            continue

        if seccion_cadenas:
            cadenas.append(linea)
        elif linea.strip():
            expresiones.append(linea.strip())

    return expresiones, cadenas


def _resolver_ruta_entrada(ruta: str | None = None) -> str:
    if ruta and os.path.isfile(ruta):
        return ruta
    for candidata in RUTAS_ENTRADA:
        if os.path.isfile(candidata):
            return candidata
    raise FileNotFoundError(
        "No se encontró el archivo de entrada. "
        f"Coloque 'expresiones_y_cadenas' o 'expresiones_y_cadenas.txt' en el directorio actual."
    )


def procesar_expresion(
    regex: str,
    indice: int,
    directorio_afns: str,
    directorio_afds: str = "AFDs",
    directorio_afds_sub: str = "AFDs_subconjuntos",
    directorio_afds_min: str = "AFDs_minimos",
    mostrar_afn: bool = True,
) -> dict:
    """Procesa una expresión regular completa:
    postfix → árbol → AFN → AFD(subconjuntos) → AFD mínimo → AFD directo
    → AFD mínimo (directo). Devuelve un dict con todos los autómatas.
    """
    print("=" * 70)
    print(f"Expresión {indice}: {regex}")
    print("-" * 70)

    tokens = regex_tokenize.tokenize(regex)
    tokens_concat = shyR.insertar_concatenacion_implicita(tokens)
    postfix = shyR.shunting_yard_regex(tokens_concat)

    print(f"Tokens               : {' '.join(tokens)}")
    print(f"Con concatenación (.): {' '.join(tokens_concat)}")
    print(f"Postfix              : {''.join(postfix)}")

    mensajes = shyR.describir_postfix(postfix)
    print("Lectura postfix (derecha -> izquierda):")
    for i, mensaje in enumerate(mensajes, 1):
        print(f"  {i}. {mensaje}")

    raiz = arbol.construir_arbol(postfix)
    print("\nÁrbol sintáctico (texto):")
    arbol.imprimir_arbol(raiz)

    recorrido = arbol.recorrido_postorden(raiz)
    print(f"\nRecorrido postorden (DFS): {' '.join(recorrido)}")

    slug = thompson._slug_desde_regex(regex)

    # --- AFN (Thompson) ---
    nfa = thompson.construir_afn_desde_arbol(raiz)
    print("\nAFN (Thompson):")
    thompson.imprimir_afn(nfa)
    thompson.dibujar_afn(nfa, f"afn_{indice:02d}_{slug}", directorio=directorio_afns)

    # --- AFD por subconjuntos (a partir del AFN) ---
    print("\nAFD (construcción por subconjuntos):")
    afd_sub = subconjuntos.construir_afd_por_subconjuntos(nfa)
    subconjuntos.imprimir_afd_subconjuntos(afd_sub)
    afd_mod.dibujar_afd(afd_sub, f"afd_sub_{indice:02d}_{slug}",
                        directorio=directorio_afds_sub)

    # --- AFD mínimo del AFD por subconjuntos ---
    print("\nAFD mínimo (partición/refinamiento) del AFD por subconjuntos:")
    afd_min_sub = minimo.minimizar_afd(afd_sub)
    afd_mod.dibujar_afd(afd_min_sub, f"afd_min_sub_{indice:02d}_{slug}",
                        directorio=directorio_afds_min)

    # --- AFD por construcción directa (vía followpos) ---
    print("\nAFD (construcción directa):")
    _, afd_directa = afd_directo.procesar_arbol_a_afd(raiz)
    afd_directo.imprimir_resultado_afd(afd_directa)
    afd_mod.dibujar_afd(afd_directa, f"afd_{indice:02d}_{slug}",
                        directorio=directorio_afds)

    # --- AFD mínimo del AFD por construcción directa ---
    print("\nAFD mínimo (partición/refinamiento) del AFD por construcción directa:")
    afd_min_directa = minimo.minimizar_afd(afd_directa)
    afd_mod.dibujar_afd(afd_min_directa, f"afd_min_{indice:02d}_{slug}",
                        directorio=directorio_afds_min)

    print()
    return {
        'nfa': nfa,
        'afd_sub': afd_sub,
        'afd_min_sub': afd_min_sub,
        'afd_directa': afd_directa,
        'afd_min_directa': afd_min_directa,
    }


def procesar_archivo(ruta: str | None = None, directorio_afns: str = "AFNs",
                     directorio_afds: str = "AFDs",
                     directorio_afds_sub: str = "AFDs_subconjuntos",
                     directorio_afds_min: str = "AFDs_minimos",
                     mostrar_afn: bool = True) -> None:
    """Procesa expresiones regulares y simula todas las cadenas contra todos
    los autómatas (AFN + 4 AFD), verificando que coincidan."""
    ruta = _resolver_ruta_entrada(ruta)
    expresiones, cadenas = leer_expresiones_y_cadenas(ruta)

    if not expresiones:
        print(f"El archivo '{ruta}' no contiene expresiones regulares.")
        return

    if not cadenas:
        print(f"Advertencia: el archivo '{ruta}' no contiene cadenas en la sección "
              f"'{MARCADOR_CADENAS}'.")

    for directorio in (directorio_afns, directorio_afds,
                       directorio_afds_sub, directorio_afds_min):
        os.makedirs(directorio, exist_ok=True)

    automatas: list[dict] = []
    expresiones_ok: list[str] = []
    for i, regex in enumerate(expresiones, 1):
        try:
            automatas.append(procesar_expresion(
                regex, i, directorio_afns,
                directorio_afds=directorio_afds,
                directorio_afds_sub=directorio_afds_sub,
                directorio_afds_min=directorio_afds_min,
                mostrar_afn=mostrar_afn,
            ))
            expresiones_ok.append(regex)
        except ValueError as exc:
            print(f"Error en expresión {i} ({regex!r}): {exc}")
            print()

    if not automatas:
        print("No se construyó ningún AFN/AFD válido.")
        return

    if not cadenas:
        return

    print("=" * 70)
    print("Simulación (todas las cadenas × AFN, AFD subconjuntos, "
          "AFD mínimos y AFD directos):")
    print("-" * 70)

    columnas = [
        ('afd_sub', 'AFD-sub'),
        ('afd_min_sub', 'AFD-min(sub)'),
        ('afd_directa', 'AFD-directo'),
        ('afd_min_directa', 'AFD-min(dir)'),
    ]

    todo_coincide = True
    minimos_iguales = True
    for i, (regex, res) in enumerate(zip(expresiones_ok, automatas), 1):
        nfa = res['nfa']
        print(f"\nExpresión {i} ({regex})")
        encabezado = "    cadena     AFN" + "".join(
            f"  {etiqueta:^12}" for _, etiqueta in columnas
        )
        print(encabezado)
        print("  " + "-" * (len(encabezado) - 2))

        if len(res['afd_min_sub'].estados) != len(res['afd_min_directa'].estados):
            minimos_iguales = False

        for cadena_raw in cadenas:
            cadena = thompson.normalizar_cadena(cadena_raw)
            resultados = [thompson.simular(nfa, cadena)] + [
                afd_mod.simular_afd(res[clave], cadena) for clave, _ in columnas
            ]
            coincide = all(r == resultados[0] for r in resultados)
            todo_coincide = todo_coincide and coincide

            cadena_display = cadena if cadena else 'ε'
            fila = f"    {cadena_display:<9}"
            for r in resultados:
                fila += f"  {'yes' if r else 'no':^12}"
            fila += "   " + ("OK" if coincide else "<-- DIFIEREN!")
            print(fila)

    print("-" * 70)
    if todo_coincide:
        print("OK: AFN y los cuatro AFD coincidieron en todas las cadenas.")
    else:
        print("ATENCIÓN: hubo discrepancias entre autómatas (revisar arriba).")

    if minimos_iguales:
        print("Nota: ambos AFD mínimos tienen el mismo número de estados "
              "(mismo lenguaje).")
    else:
        print("Ojo: los AFD mínimos tienen distinto número de estados; "
              "revise la minimización.")


if __name__ == "__main__":
    ruta_arg = sys.argv[1] if len(sys.argv) > 1 else None
    procesar_archivo(ruta_arg)