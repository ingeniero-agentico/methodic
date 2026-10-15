#!/usr/bin/env python3
"""Second path for the sample case: recomputes the figures of expected.json with closed formulas
(annuities, balances by formula, yearly tax shields) and WITHOUT importing the main script.

Usage: python second_path.py   → prints each figure by both paths and the difference.
Differences of a few pesos come from the script rounding each installment and interest to the
peso (as a bank does) while this path does not round.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
case = json.loads((HERE / "sample-case.json").read_text(encoding="utf-8"))
expected = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))

t, r, H = 0.27, 0.12, 5                      # sample-profile.yaml
P = case["asset"]["net_price"]
life = case["asset"]["useful_life_years"]
MV = case["asset"]["market_value_at_horizon"]["value"]
rm = (1 + r) ** (1 / 12) - 1                 # equivalent monthly rate


def a(n, i):                                  # annuity factor in arrears
    return (1 - (1 + i) ** -n) / i


def pv_yearly(amounts_by_year):               # {year: amount} at the close of each year
    return sum(m / (1 + r) ** k for k, m in amounts_by_year.items())


# Cash --------------------------------------------------------------------------------------------
D = P / life
book5 = P - D * H
net_residual = MV - t * (MV - book5)
dep_shield = t * D * a(H, r)
cash_cost = P - dep_shield - net_residual / (1 + r) ** H

# Project -----------------------------------------------------------------------------------------
flow = {0: -24000000, 1: 6800000, 2: 6800000, 3: 6800000, 4: 6800000, 5: 15221429}
project_npv = pv_yearly(flow)


# Loan --------------------------------------------------------------------------------------------
def loan(alt, system):
    down = P * alt["down_payment_fraction"]
    L = P - down
    n, i = alt["term_months"], alt["monthly_rate"]
    stamp = L * min(alt["loan_tax"]["monthly_rate"] * n, alt["loan_tax"]["cap"])
    fees = alt["upfront_fees"] + stamp
    ins = alt["monthly_insurance"]
    if system == "french":
        C = L * i / (1 - (1 + i) ** -n)
        balance = lambda m: L * (1 + i) ** m - C * ((1 + i) ** m - 1) / i
        inst = {m: C for m in range(1, n + 1)}
        pv_inst = C * a(n, rm)
        total_int = n * C - L
    else:
        A = L / n
        balance = lambda m: L - A * m
        inst = {m: A + (L - A * (m - 1)) * i for m in range(1, n + 1)}
        pv_inst = sum(c / (1 + rm) ** m for m, c in inst.items())
        total_int = i * L * (n + 1) / 2
    int_year = {}
    for k in range(1, n // 12 + 1):
        paid = sum(inst[m] for m in range(12 * (k - 1) + 1, 12 * k + 1))
        principal = balance(12 * (k - 1)) - balance(12 * k)
        int_year[k] = paid - principal
    ded = {k: v + 12 * ins for k, v in int_year.items()}
    ded[1] += fees
    cost = (down + fees + pv_inst + ins * a(n, rm) - t * pv_yearly(ded)
            - dep_shield - net_residual / (1 + r) ** H)
    return dict(installment=inst[1], total_interest=total_int, pv_cost=cost)


# Leasing -----------------------------------------------------------------------------------------
def leasing(alt):
    n, i = alt["term_months"], alt["monthly_rate"]
    C = P / (1 + a(n, i) + (1 + i) ** -(n + 1))        # initial = option = one installment
    ded = {1: C + 12 * C, 2: 12 * C, 3: 12 * C}        # initial installment + 12 installments a year
    D_op = C / life                                    # the option is depreciated from year 4
    ded[4] = D_op
    ded[5] = D_op
    book = C - 2 * D_op
    res = MV - t * (MV - book)
    cost = (C + C * a(n, rm) + C / (1 + rm) ** (n + 1) - t * pv_yearly(ded) - res / (1 + r) ** H)
    return dict(installment=C, total_interest=(n + 2) * C - P, pv_cost=cost)


# Rental ------------------------------------------------------------------------------------------
def rental(alt):
    R, G, n = alt["monthly_rent"], alt["deposit"], alt["term_months"]
    cost = G - G / (1 + rm) ** n + R * a(n, rm) - t * 12 * R * a(H, r)
    return dict(installment=R, pv_cost=cost)


alts = {x["name"]: x for x in case["alternatives"]}
calc = {
    "Cash": dict(pv_cost=cash_cost),
    "Loan 36 months": loan(alts["Loan 36 months"], "french"),
    "Loan 36 months (German)": loan(alts["Loan 36 months (German)"], "german"),
    "Leasing 36 months": leasing(alts["Leasing 36 months"]),
    "Rental 60 months": rental(alts["Rental 60 months"]),
}
for k, v in calc.items():
    v["investor_npv"] = project_npv + cash_cost - v["pv_cost"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
worst = 0.0
print(f"{'figure':52} {'expected.json':>16} {'second path':>16} {'diff':>8}")
print(f"{'Project NPV':52} {expected['project_npv']:>16,.0f} {project_npv:>16,.0f} "
      f"{expected['project_npv'] - project_npv:>8,.0f}")
for name, v in calc.items():
    for key, x in v.items():
        e = expected["alternatives"][name].get(key)
        if e is None:
            continue
        d = e - x
        worst = max(worst, abs(d))
        print(f"{name + ' · ' + key:52} {e:>16,.0f} {x:>16,.0f} {d:>8,.0f}")
print(f"Largest difference: {worst:,.0f} pesos (installments and interest rounded to the peso)")
sys.exit(0 if worst <= 100 else 1)
