from __future__ import annotations

import argparse
import os
import sys

import cyk as modulo_cyk
import lr_pda
import pda
from gramatica import tokenizar


def leer_cadenas(ruta: str) -> list[str]:
    with open(ruta, encoding="utf-8") as archivo:
        return [
            linea.rstrip("\n\r")
            for linea in archivo
            if linea.strip() and not linea.strip().startswith("#")
        ]


def _texto_resultado(aceptada: bool, limite: bool = False) -> str:
    if limite:
        return "INDETERMINADO"
    return "ACEPTADA" if aceptada else "RECHAZADA"


def _imprimir_resumen_corto(
    nombre: str, aceptada: bool, operaciones: int, limite: bool = False
) -> None:
    print(f"  {nombre}: {_texto_resultado(aceptada, limite)} | operaciones={operaciones}")


def procesar_cadena(
    cadena: str,
    pda_construido: pda.PDA,
    tabla_lr: lr_pda.TablaSLR,
    max_configuraciones: int,
    max_derivaciones: int,
    mostrar_traza: bool,
) -> tuple[bool, bool, bool, bool]:
    tokens = tokenizar(cadena)
    print("-" * 70)
    print(f"Cadena: '{cadena}' | tokens: {len(tokens)}")
    print("-" * 70)

    resultado_pda = pda.simular_pda(
        pda_construido, tokens, max_configuraciones=max_configuraciones
    )
    if mostrar_traza:
        pda.imprimir_resultado_pda(resultado_pda, tokens)
    else:
        _imprimir_resumen_corto(
            "PDA no determinista",
            resultado_pda.aceptada,
            resultado_pda.contador.total,
            resultado_pda.limite_alcanzado,
        )

    resultado_dpda = lr_pda.simular_dpda(tabla_lr, tokens)
    if mostrar_traza:
        lr_pda.imprimir_resultado_dpda(resultado_dpda, tokens)
    else:
        _imprimir_resumen_corto(
            "PDA determinista",
            resultado_dpda.aceptada,
            resultado_dpda.contador.total,
        )

    resultado_cyk = modulo_cyk.cyk(tokens)
    if mostrar_traza:
        modulo_cyk.imprimir_resultado_cyk(
            resultado_cyk, max_derivaciones=max_derivaciones
        )
    else:
        _imprimir_resumen_corto(
            "CYK", resultado_cyk.aceptada, resultado_cyk.contador.total
        )

    return (
        resultado_pda.aceptada,
        resultado_dpda.aceptada,
        resultado_cyk.aceptada,
        resultado_pda.limite_alcanzado,
    )


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconoce frases de la gramatica G con PDA no determinista, "
        "PDA determinista LR/SLR y CYK."
    )
    parser.add_argument(
        "cadena",
        nargs="*",
        help="cadena por reconocer, por ejemplo: \"the cat eats the cake\"",
    )
    parser.add_argument(
        "--archivo",
        help="archivo con una cadena por linea; las lineas con # se ignoran",
    )
    parser.add_argument(
        "--max-configuraciones",
        type=int,
        default=2_000_000,
        help="limite de configuraciones para el PDA no determinista",
    )
    parser.add_argument(
        "--max-derivaciones",
        type=int,
        default=3,
        help="maximo de derivaciones CYK que se imprimen",
    )
    parser.add_argument(
        "--sin-traza",
        action="store_true",
        help="imprime solo resultados y conteos de operaciones",
    )
    parser.add_argument(
        "--tabla-pda",
        action="store_true",
        help="imprime la tabla completa de transiciones del PDA no determinista",
    )
    parser.add_argument(
        "--tabla-lr",
        action="store_true",
        help="imprime la tabla SLR(1) completa",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    pda_construido = pda.construir_pda_desde_gramatica()
    tabla_lr = lr_pda.construir_tabla_slr()

    print("=" * 70)
    print("Reconocimiento de cadenas del lenguaje de G")
    print("=" * 70)
    pda.imprimir_resumen_pda(pda_construido)
    lr_pda.imprimir_resumen_slr(tabla_lr)
    if args.tabla_pda:
        pda.imprimir_tabla_pda(pda_construido)
    if args.tabla_lr:
        lr_pda.imprimir_tabla_slr(tabla_lr)

    if args.archivo:
        if not os.path.isfile(args.archivo):
            print(f"Error: no existe el archivo '{args.archivo}'.")
            return 2
        cadenas = leer_cadenas(args.archivo)
    elif args.cadena:
        cadenas = [" ".join(args.cadena)]
    elif os.path.isfile("cadenas.txt"):
        cadenas = leer_cadenas("cadenas.txt")
    else:
        cadenas = ["he cooks"]

    if not cadenas:
        print("No hay cadenas por reconocer.")
        return 2

    resultados: list[tuple[str, bool, bool, bool, bool]] = []
    discrepancia = False
    for cadena in cadenas:
        resultado_pda, resultado_dpda, resultado_cyk, limite = procesar_cadena(
            cadena,
            pda_construido,
            tabla_lr,
            args.max_configuraciones,
            args.max_derivaciones,
            not args.sin_traza,
        )
        coinciden = (
            resultado_pda == resultado_dpda == resultado_cyk and not limite
        )
        discrepancia = discrepancia or not coinciden
        resultados.append(
            (cadena, resultado_pda, resultado_dpda, resultado_cyk, limite)
        )

    print("=" * 70)
    print("Resumen comparativo")
    print("=" * 70)
    print(f"  {'cadena':<45} {'NPDA':<14} {'DPDA':<10} {'CYK':<10} {'coinciden'}")
    print("  " + "-" * 94)
    for cadena, resultado_pda, resultado_dpda, resultado_cyk, limite in resultados:
        texto_pda = _texto_resultado(resultado_pda, limite)
        texto_dpda = _texto_resultado(resultado_dpda)
        texto_cyk = _texto_resultado(resultado_cyk)
        coincide = (
            resultado_pda == resultado_dpda == resultado_cyk and not limite
        )
        print(
            f"  {cadena:<45} {texto_pda:<14} {texto_dpda:<10} "
            f"{texto_cyk:<10} {'si' if coincide else 'NO'}"
        )

    if discrepancia:
        print("Atencion: hubo discrepancias entre metodos.")
        return 2
    if all(resultado_pda for _, resultado_pda, _, _, _ in resultados):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
