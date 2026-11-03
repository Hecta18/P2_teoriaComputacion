# Proyecto 2 - Teoria de la Computacion

Reconocimiento de cadenas del lenguaje generado por gramatica libre de contexto del proyecto. Se implementan tres reconocedores:

1. PDA no determinista obtenido por la conversion formal CFG -> PDA.
2. PDA determinista LR/SLR construido a partir de la tabla de parseo.
3. Algoritmo CYK para gramaticas en forma normal de Chomsky.

Todas las salidas de los reconocedores se imprimen por consola.

## Requisitos

- Python 3.10 o superior.
- No se requieren librerias externas.

## Uso

Reconocer una cadena:

```bash
python reconocer.py "the cat eats the cake in the oven"
```

Reconocer todas las cadenas de un archivo:

```bash
python reconocer.py --archivo cadenas.txt
```

Opciones:

```text
--max-configuraciones N   limite de configuraciones del PDA no determinista
--max-derivaciones N      maximo de derivaciones CYK que se imprimen
--sin-traza               imprime solo resultados y conteos de operaciones
--tabla-pda               imprime la tabla completa del PDA no determinista
--tabla-lr                imprime la tabla SLR(1)
```

Tambien se pueden ejecutar los metodos por separado:

```bash
python pda.py "the cat eats the cake"
python lr_pda.py "the cat eats the cake"
python cyk.py "the cat eats the cake"
```

## Analisis de crecimiento

```bash
python analisis_crecimiento.py
python analisis_crecimiento.py --max-k 25
```

El programa genera cadenas de la forma:

```text
he cooks
he cooks in the cat
he cooks in the cat in the cat
...
```

Se imprime por consola el conteo de operaciones, los ratios y el ajuste asintotico empirico.

## Pruebas

```bash
python -m unittest discover -s tests -t . -v
```

## Docker

Construir y ejecutar con las cadenas de ejemplo:

```bash
docker compose up --build
```

Ejecutar una cadena especifica:

```bash
docker compose run --rm proyecto2 python reconocer.py "the cat eats the cake"
```

Ejecutar las pruebas:

```bash
docker compose run --rm proyecto2 python -m unittest discover -s tests -t . -v
```

Ejecutar el analisis de crecimiento:

```bash
docker compose run --rm proyecto2 python analisis_crecimiento.py --max-k 25
```

## Estructura

```text
gramatica.py              Gramatica G, simbolos, tokenizacion y validacion CNF
pda.py                    PDA no determinista, conversion CFG -> PDA y simulacion
lr_pda.py                 Tabla SLR(1), PDA determinista y arbol de parseo
cyk.py                    CYK, tabla, retroapuntadores, arbol y derivacion
reconocer.py              Ejecuta los tres metodos y compara resultados
analisis_crecimiento.py   Conteo de operaciones y ajuste empirico
cadenas.txt               Cadenas de ejemplo
tests/                    Pruebas unitarias
Proyecto2.pdf             Documento final
Dockerfile
docker-compose.yml
```

## Documentacion

El PDF contiene: definicion de la gramatica, conversion a PDA, construccion LR/SLR, algoritmo CYK, ejemplos con trazas, analisis de complejidad y comparacion de desempeño.

## Video

https://youtu.be/nvBbqriTp1Q?si=XU5tsiRpJjer2rAi
