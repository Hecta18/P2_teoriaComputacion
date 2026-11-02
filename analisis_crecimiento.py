from __future__ import annotations

import argparse
import math

import cyk as modulo_cyk
import lr_pda
import pda
from gramatica import tokenizar


def cadenas_de_crecimiento(max_k: int) -> list[tuple[int, str]]:
    base = "he cooks"
    sufijo = " in the cat"
    cadenas: list[tuple[int, str]] = []
    for k in range(max_k + 1):
        cadena = base + sufijo * k
        cadenas.append((k, cadena))
    return cadenas


def ajuste_log_log(puntos: list[tuple[int, int]]) -> tuple[float, float, float]:
    puntos_validos = [(n, operaciones) for n, operaciones in puntos if n > 0 and operaciones > 0]
    if len(puntos_validos) < 2:
        return 0.0, 0.0, 0.0
    xs = [math.log(n) for n, _ in puntos_validos]
    ys = [math.log(operaciones) for _, operaciones in puntos_validos]
    media_x = sum(xs) / len(xs)
    media_y = sum(ys) / len(ys)
    numerador = sum((x - media_x) * (y - media_y) for x, y in zip(xs, ys))
    denominador = sum((x - media_x) ** 2 for x in xs)
    pendiente = numerador / denominador if denominador else 0.0
    intercepto = media_y - pendiente * media_x
    predicciones = [intercepto + pendiente * x for x in xs]
    ss_res = sum((y - pred) ** 2 for y, pred in zip(ys, predicciones))
    ss_tot = sum((y - media_y) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return pendiente, math.exp(intercepto), r2


def pendiente_local(puntos: list[tuple[int, int]]) -> float:
    validos = [(n, operaciones) for n, operaciones in puntos if n > 0 and operaciones > 0]
    if len(validos) < 2:
        return 0.0
    (n1, ops1), (n2, ops2) = validos[-2], validos[-1]
    return math.log(ops2 / ops1) / math.log(n2 / n1)


def ajuste_exponencial(puntos: list[tuple[int, int]]) -> tuple[float, float, float]:
    puntos_validos = [(n, operaciones) for n, operaciones in puntos if n > 0 and operaciones > 0]
    if len(puntos_validos) < 2:
        return 0.0, 0.0, 0.0
    xs = [float(n) for n, _ in puntos_validos]
    ys = [math.log(operaciones) for _, operaciones in puntos_validos]
    media_x = sum(xs) / len(xs)
    media_y = sum(ys) / len(ys)
    numerador = sum((x - media_x) * (y - media_y) for x, y in zip(xs, ys))
    denominador = sum((x - media_x) ** 2 for x in xs)
    pendiente = numerador / denominador if denominador else 0.0
    intercepto = media_y - pendiente * media_x
    predicciones = [intercepto + pendiente * x for x in xs]
    ss_res = sum((y - pred) ** 2 for y, pred in zip(ys, predicciones))
    ss_tot = sum((y - media_y) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return math.exp(pendiente), math.exp(intercepto), r2


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mide operaciones de NPDA, DPDA y CYK para cadenas de longitud creciente."
    )
    parser.add_argument(
        "--max-k",
        type=int,
        default=12,
        help="cantidad de sufijos 'in the cat' agregados a la cadena base",
    )
    parser.add_argument(
        "--max-configuraciones",
        type=int,
        default=2_000_000,
        help="limite de configuraciones para el PDA no determinista",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    pda_construido = pda.construir_pda_desde_gramatica()
    tabla_lr = lr_pda.construir_tabla_slr()

    print("=" * 96)
    print("Analisis de crecimiento por conteo de operaciones")
    print("=" * 96)
    print("Familia: 'he cooks' + k * ' in the cat'")
    print("La longitud n se mide en tokens.")
    print()

    encabezado = (
        f"  {'k':>3} {'n':>4} {'CYK':>10} {'NPDA':>10} {'DPDA':>8} "
        f"{'CYK/n^3':>12} {'ratio CYK':>11} {'ratio NPDA':>11} {'ratio DPDA':>11}"
    )
    print(encabezado)
    print("  " + "-" * (len(encabezado) - 2))

    puntos_cyk: list[tuple[int, int]] = []
    puntos_npda: list[tuple[int, int]] = []
    puntos_dpda: list[tuple[int, int]] = []
    anterior: tuple[int, int, int] | None = None
    limite_alcanzado = False

    for k, cadena in cadenas_de_crecimiento(args.max_k):
        tokens = tokenizar(cadena)
        n = len(tokens)

        resultado_cyk = modulo_cyk.cyk(tokens)
        resultado_dpda = lr_pda.simular_dpda(tabla_lr, tokens)
        resultado_pda = pda.simular_pda(
            pda_construido, tokens, max_configuraciones=args.max_configuraciones
        )

        ops_cyk = resultado_cyk.contador.total
        ops_npda = resultado_pda.contador.total
        ops_dpda = resultado_dpda.contador.total
        puntos_cyk.append((n, ops_cyk))
        puntos_npda.append((n, ops_npda))
        puntos_dpda.append((n, ops_dpda))

        if anterior is None:
            ratio_cyk = ratio_npda = ratio_dpda = float("nan")
        else:
            n_ant, cyk_ant, npda_ant = anterior
            ops_dpda_ant = puntos_dpda[-2][1]
            ratio_cyk = ops_cyk / cyk_ant if cyk_ant else float("nan")
            ratio_npda = ops_npda / npda_ant if npda_ant else float("nan")
            ratio_dpda = ops_dpda / ops_dpda_ant if ops_dpda_ant else float("nan")

        marca = ""
        if resultado_pda.limite_alcanzado:
            limite_alcanzado = True
            marca = " LIMITE"

        print(
            f"  {k:>3} {n:>4} {ops_cyk:>10} {ops_npda:>10} {ops_dpda:>8} "
            f"{ops_cyk / (n ** 3):>12.4f} {ratio_cyk:>11.3f} "
            f"{ratio_npda:>11.3f} {ratio_dpda:>11.3f}{marca}"
        )
        anterior = (n, ops_cyk, ops_npda)

        if limite_alcanzado:
            print("  Se detiene el analisis: el NPDA alcanzo el limite de configuraciones.")
            break

    print()
    print("Ajustes empiricos:")
    for nombre, puntos in (
        ("CYK", puntos_cyk),
        ("NPDA", puntos_npda),
        ("DPDA", puntos_dpda),
    ):
        pendiente, constante, r2 = ajuste_log_log(puntos)
        base, constante_exp, r2_exp = ajuste_exponencial(puntos)
        local = pendiente_local(puntos)
        print(
            f"  {nombre:<5} log-log: operaciones ~ {constante:.4f} * n^{pendiente:.4f} "
            f"(R^2={r2:.4f}), pendiente local={local:.4f}"
        )
        print(
            f"        exponencial: operaciones ~ {constante_exp:.4f} * {base:.4f}^n "
            f"(R^2={r2_exp:.4f})"
        )

    print()
    print("Interpretacion teorica:")
    print("  CYK: tiempo Theta(n^3), espacio Theta(n^2) para gramatica fija.")
    print("  NPDA: peor caso exponencial por la busqueda no determinista;")
    print("        el ajuste empirico depende de la gramatica y de la poda aplicada.")
    print("  DPDA LR/SLR: tiempo Theta(n), espacio Theta(n).")
    print()
    print("Nota: el conteo se basa en operaciones del algoritmo, no en tiempo de ejecucion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
