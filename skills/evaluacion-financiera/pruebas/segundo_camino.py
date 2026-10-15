#!/usr/bin/env python3
"""Segundo camino para el caso ficticio: recalcula las cifras de esperado.json con fórmulas
cerradas (anualidades, saldos por fórmula, escudos anuales) y SIN importar el script principal.

Uso: python segundo_camino.py   → imprime cada cifra por los dos caminos y la diferencia.
Las diferencias de unos pocos pesos vienen de que el script redondea cada cuota e interés al peso
(como un banco) y este camino no redondea.
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
caso = json.loads((AQUI / "caso-ficticio.json").read_text(encoding="utf-8"))
esperado = json.loads((AQUI / "esperado.json").read_text(encoding="utf-8"))

t, r, H = 0.27, 0.12, 5                     # perfil-ficticio.yaml
P = caso["activo"]["precio_neto"]
vida = caso["activo"]["vida_util_anios"]
VM = caso["activo"]["valor_mercado_al_horizonte"]["valor"]
rm = (1 + r) ** (1 / 12) - 1                 # tasa mensual equivalente


def a(n, i):                                  # factor de anualidad vencida
    return (1 - (1 + i) ** -n) / i


def vp_anual(montos_por_anio):                # {año: monto} al cierre de cada año
    return sum(m / (1 + r) ** k for k, m in montos_por_anio.items())


# Contado ----------------------------------------------------------------------------------------
D = P / vida
libro5 = P - D * H
res_neto = VM - t * (VM - libro5)
escudo_dep = t * D * a(H, r)
costo_contado = P - escudo_dep - res_neto / (1 + r) ** H

# Proyecto ---------------------------------------------------------------------------------------
flujo = {0: -24000000, 1: 6800000, 2: 6800000, 3: 6800000, 4: 6800000, 5: 15221429}
van_proy = vp_anual(flujo)


# Crédito ----------------------------------------------------------------------------------------
def credito(alt, sistema):
    pie = P * alt["pie_fraccion"]
    L = P - pie
    n, i = alt["plazo_meses"], alt["tasa_mensual"]
    ite = L * min(alt["impuesto_credito"]["tasa_mensual"] * n, alt["impuesto_credito"]["tope"])
    gastos = alt["gastos_iniciales"] + ite
    seg = alt["seguro_mensual"]
    if sistema == "francesa":
        C = L * i / (1 - (1 + i) ** -n)
        saldo = lambda m: L * (1 + i) ** m - C * ((1 + i) ** m - 1) / i
        cuotas = {m: C for m in range(1, n + 1)}
        vp_cuotas = C * a(n, rm)
        total_int = n * C - L
    else:
        A = L / n
        saldo = lambda m: L - A * m
        cuotas = {m: A + (L - A * (m - 1)) * i for m in range(1, n + 1)}
        vp_cuotas = sum(c / (1 + rm) ** m for m, c in cuotas.items())
        total_int = i * L * (n + 1) / 2
    int_anual = {}
    for k in range(1, n // 12 + 1):
        pagado = sum(cuotas[m] for m in range(12 * (k - 1) + 1, 12 * k + 1))
        amort = saldo(12 * (k - 1)) - saldo(12 * k)
        int_anual[k] = pagado - amort
    ded = {k: v + 12 * seg for k, v in int_anual.items()}
    ded[1] += gastos
    costo = (pie + gastos + vp_cuotas + seg * a(n, rm) - t * vp_anual(ded)
             - escudo_dep - res_neto / (1 + r) ** H)
    return dict(cuota=cuotas[1], total_intereses=total_int, costo_vp=costo)


# Leasing ----------------------------------------------------------------------------------------
def leasing(alt):
    n, i = alt["plazo_meses"], alt["tasa_mensual"]
    C = P / (1 + a(n, i) + (1 + i) ** -(n + 1))        # pie = opción = una cuota
    ded = {1: C + 12 * C, 2: 12 * C, 3: 12 * C}        # cuota inicial + 12 cuotas por año
    D_op = C / vida                                    # la opción se deprecia desde el año 4
    ded[4] = D_op
    ded[5] = D_op
    libro = C - 2 * D_op
    res = VM - t * (VM - libro)
    costo = (C + C * a(n, rm) + C / (1 + rm) ** (n + 1) - t * vp_anual(ded) - res / (1 + r) ** H)
    return dict(cuota=C, total_intereses=(n + 2) * C - P, costo_vp=costo)


# Arriendo ---------------------------------------------------------------------------------------
def arriendo(alt):
    R, G, n = alt["renta_mensual"], alt["garantia"], alt["plazo_meses"]
    costo = G - G / (1 + rm) ** n + R * a(n, rm) - t * 12 * R * a(H, r)
    return dict(cuota=R, costo_vp=costo)


alts = {x["nombre"]: x for x in caso["alternativas"]}
calc = {
    "Contado": dict(costo_vp=costo_contado),
    "Crédito 36 cuotas": credito(alts["Crédito 36 cuotas"], "francesa"),
    "Crédito 36 cuotas (alemana)": credito(alts["Crédito 36 cuotas (alemana)"], "alemana"),
    "Leasing 36 cuotas": leasing(alts["Leasing 36 cuotas"]),
    "Arriendo 60 meses": arriendo(alts["Arriendo 60 meses"]),
}
for k, v in calc.items():
    v["van_inversionista"] = van_proy + costo_contado - v["costo_vp"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
peor = 0.0
print(f"{'cifra':52} {'esperado.json':>16} {'segundo camino':>16} {'dif':>8}")
print(f"{'VAN del proyecto':52} {esperado['van_proyecto']:>16,.0f} {van_proy:>16,.0f} "
      f"{esperado['van_proyecto'] - van_proy:>8,.0f}")
for nombre, v in calc.items():
    for clave, x in v.items():
        e = esperado["alternativas"][nombre].get(clave)
        if e is None:
            continue
        d = e - x
        peor = max(peor, abs(d))
        print(f"{nombre + ' · ' + clave:52} {e:>16,.0f} {x:>16,.0f} {d:>8,.0f}")
print(f"Mayor diferencia: {peor:,.0f} pesos (redondeo de cuotas e intereses al peso)")
sys.exit(0 if peor <= 100 else 1)
