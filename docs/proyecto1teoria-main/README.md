# proyecto1teoria

Herramienta didáctica de teoría de la computación: convierte **expresiones
regulares** en autómatas y comprueba el lenguaje reconocido contra un conjunto
de **cadenas**. El flujo completo es:

```
regex → tokens → postfix (Shunting Yard) → árbol sintáctico → AFN (Thompson)
      → AFD por subconjuntos → AFD mínimo (partición/refinamiento)
      → AFD por construcción directa → AFD mínimo (directo)
      → simulación de cadenas en los 5 autómatas → verificación
```

Los AFN y AFD se imprimen en consola y, si Graphviz + Pillow están instalados,
también se generan imágenes JPEG.

## Requisitos e instalación

- **Python 3.10 o superior** (por los type hints `int | None` y el operador `|`
  en la sintaxis de tipos).
- *(Opcional)* Para los dibujos: las librerías de Python y el binario `dot`
  de Graphviz.

```bash
pip install -r requirements.txt
```

- Graphviz (binario `dot`): descargar de <https://graphviz.org/download/> o
  instalar con el gestor de paquetes del sistema (`apt install graphviz`,
  `brew install graphviz`, etc.).
- Pillow se instala con `requirements.txt` y convierte el PNG de Graphviz a
  JPEG. Si falta, las imágenes se guardan como PNG.

Si no hay dibujos disponibles el programa **no falla**: imprime un aviso y
continúa mostrando los autómatas en consola.

## Formato del archivo de entrada

El archivo de entrada (por defecto `expresiones_y_cadenas.txt`) tiene dos
secciones separadas por el marcador `# --- Cadenas ---`:

```
# Comentarios (líneas que empiezan por '#'; el marcador de cadenas no lo es)
(a|b)*abb
(a|b)*

# --- Cadenas ---
ab
abb
ε        <- aceptado también como 'E' o línea vacía
```

- **Expresiones**: una por línea, antes del marcador. Operadores soportados:
  `|` (unión), `.` (concatenación, opcional), `*` (Kleene), `+` (positiva) y
  `?` (opcional). Agrupación con paréntesis.
- **ε (vacío)**: se escribe `E` o `ε` (también se admite `ε` directo). El
  marcador de fin `#` que necesita la construcción directa se añade
  automáticamente; **no** debe escribirse en el archivo.
- **Cadenas**: una por línea, después del marcador. La cadena vacía se indica
  con `ε`, `E` o una línea en blanco.

## Ejecución

Desde la raíz del proyecto:

```bash
python Procesar_expresiones_y_cadenas.py                 # usa expresiones_y_cadenas.txt
python Procesar_expresiones_y_cadenas.py mi_archivo.txt  # usa otro archivo
```

## Salida

La consola muestra, para **cada** expresión, el recorrido completo con sus
pasos numerados (postfix, árbol, AFN, los cuatro AFD y sus tablas de
transiciones). Al final se simulan todas las cadenas contra los 5 autómatas y
se verifica que **todos coincidan** en cada cadena.

Imágenes generadas en cuatro carpetas:

| Carpeta              | Contenido                                      |
| -------------------- | ---------------------------------------------- |
| `AFNs/`              | AFN construido con Thompson                    |
| `AFDs/`              | AFD por construcción directa (followpos)       |
| `AFDs_subconjuntos/` | AFD por subconjuntos (ε-clausura + move)       |
| `AFDs_minimos/`      | AFD mínimo de cada uno de los dos AFD anteriores |

## Pipeline detallado

1. **Tokenización** (`regex_tokenize.tokenize`): cada carácter es un token.
2. **Concatenación implícita** (`shunting_yard_regex.insertar_concatenacion_implicita`):
   inserta `.` donde faltan.
3. **Shunting Yard** (`shunting_yard_regex.shunting_yard_regex`): infix → postfix.
4. **Árbol sintáctico** (`Arbol_sintactico.construir_arbol`).
5. **AFN con Thompson** (`thompson_arbol.construir_afn_desde_arbol`).
6. **AFD por subconjuntos** (`construccion_subconjuntos.construir_afd_por_subconjuntos`):
   `Dstates = {ε-clausura(s0)}`, `U = ε-clausura(move(T, a))`.
7. **AFD mínimo** (`minimizacion_afd.minimizar_afd`): partición/refinamiento.
8. **AFD por construcción directa** (`construccion_directa_afd.procesar_arbol_a_afd`):
   posiciones, followpos, Dstates/Dtran.
9. **Minimización del AFD directo** (mismo módulo del paso 7).
10. **Simulación** (`thompson_arbol.simular` y `afd_dibujo_simulacion.simular_afd`)
    y comparación de resultados.

## Estructura del proyecto

| Archivo                                  | Responsabilidad                                                            | Funciones clave                                        |
| ---------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------ |
| `Procesar_expresiones_y_cadenas.py`      | Orquestador: lee el archivo, encadena todo el pipeline y verifica           | `procesar_expresion`, `procesar_archivo`                |
| `regex_tokenize.py`                      | Tokenización de la regex (un token por carácter)                            | `tokenize`                                             |
| `shunting_yard_regex.py`                 | Concatenación implícita + infix → postfix                                   | `insertar_concatenacion_implicita`, `shunting_yard_regex` |
| `Arbol_sintactico.py`                    | Árbol sintáctico desde postfix (+ expansión de `+` y `?`)                   | `construir_arbol`, `imprimir_arbol`                     |
| `thompson_arbol.py`                      | AFN de Thompson, clausura-ε, simulación y dibujo del AFN                    | `construir_afn_desde_arbol`, `epsilon_clausura`, `simular` |
| `construccion_directa_afd.py`            | AFD por construcción directa (followpos) + impresión de tablas              | `procesar_arbol_a_afd`, `construir_afd`, `imprimir_*`   |
| `construccion_subconjuntos.py`           | **AFD por subconjuntos** a partir del AFN (`Dstates`/`Dtran`)               | `construir_afd_por_subconjuntos`, `move`, `obtener_alfabeto` |
| `minimizacion_afd.py`                    | **Minimización** del AFD por partición/refinamiento (equivale a Hopcroft)   | `minimizar_afd`                                        |
| `afd_dibujo_simulacion.py`               | Simulación del AFD, dibujo del AFD y comparación AFN/AFD                    | `simular_afd`, `simular_afd_con_traza`, `dibujar_afd`   |
| `tests/`                                 | Pruebas unitarias de las funciones simples                                  | `python -m unittest discover -s tests -t . -v`          |
| `expresiones_y_cadenas.txt`              | Archivo de entrada de ejemplo                                               | —                                                      |

Para leer el código de una etapa concreta, busque en la tabla de arriba la
fila correspondiente: cada archivo es autocontenido y se importa solo desde el
orquestador (`Procesar_expresiones_y_cadenas.py`), por lo que se puede estudiar
de forma aislada.

## Pruebas

Las pruebas unitarias cubren **funciones simples** (tokenización, Shunting
Yard, ε-clausura, `move`, y la minimización sobre AFD pequeños), sin tocar I/O
ni dibujos.

```bash
python -m unittest discover -s tests -t . -v
```

## Notas técnicas

- **ε-clausura y AFD por subconjuntos**: cada estado del AFD es un
  `frozenset` de estados del AFN; el estado inicial es `ε-clausura(estados
  iniciales del AFN)` y un subconjunto es de aceptación si contiene algún
  estado final del AFN.
- **δ parcial**: los AFD de este proyecto omite las transiciones que van al
  "estado muerto" (no hay estado trampa explícito), igual que un AFD parcial.
  La simulación rechaza la cadena en cuanto falta una transición.
- **Minimización**: `minimizacion_afd.minimizar_afd` usa **partición/
  refinamiento** (Moore), que da exactamente el mismo AFD mínimo que el
  algoritmo de Hopcroft con mucho menos código. Internamente añade un estado
  muerto para completar δ; al final lo elimina (salvo que lo contenga el estado
  inicial).
- **Documentación de los autómatas**: los estados del AFD se etiquetan
  `A, B, C, ..., A1, B1, ...` (`construccion_directa_afd._nombre_estado`), lo
  que permite seguir la traza de la simulación en consola.

  **Link del video** : https://youtu.be/ev5UUJJdRog 