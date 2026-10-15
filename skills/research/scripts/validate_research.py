#!/usr/bin/env python3
"""research · validates the research of a task (context/research-data.json).

Checks that every datum carries value, unit, date, source, retrieval date and a reliability level
(A to D); that every gap has a usable datum or is declared "no_data" with the action that closes
it; that no D datum (nor one still to confirm) enters a calculation without being marked as an
ASSUMPTION; that calculated data match their formula and do not inherit a better level than their
worst input; and detects numeric contradictions between data that measure the same thing.

Usage:
    python validate_research.py <research-data.json> [--threshold 0.10] [--table] [--json]
    python validate_research.py --test

English keys are canonical. A file written before v1.1 (datos-investigados.json, Spanish keys and
values: huecos, datos, nivel, elegido, para_que, verificado...) is accepted as it is: it is
normalized at load. Old flags (--umbral, --tabla, --probar) still work as hidden aliases.

Standard library only. Exits 0 if there are no errors (warnings do not fail), 1 if there are.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]

LEVELS = ("A", "B", "C", "D")
DATUM_STATUS = ("verified", "to_confirm", "calculated", "not_found")
GAP_STATUS = ("has_data", "no_data")
ACCESS = ("open", "person_fetches", "no_public_source", "no_response")
ROOT_FIELDS = ("task", "research_date", "gaps", "sweep", "data", "contradictions")
GAP_FIELDS = ("id", "question", "precision", "method", "for", "status")
DATUM_FIELDS = ("id", "gap", "description", "quantity", "value", "unit", "data_date",
                "retrieval_date", "reliability", "status", "usable", "assumption")
SWEEP_FIELDS = ("id", "source", "access", "gaps")
DEFAULT_THRESHOLD = 0.10
DEFAULT_VALIDITY = 365
UNDATED = "undated"

# ---- Spanish keys and values (files written before v1.1) -> English
ROOT_KEYS = {"encargo": "task", "fecha_investigacion": "research_date", "origen_huecos": "gaps_source",
             "umbral_contradiccion": "contradiction_threshold", "vigencia_dias": "validity_days",
             "huecos": "gaps", "barrido": "sweep", "datos": "data", "contradicciones": "contradictions"}
GAP_KEYS = {"pregunta": "question", "metodo": "method", "para_que": "for", "estado": "status",
            "elegido": "chosen", "razon_eleccion": "choice_reason", "como_se_cierra": "how_to_close"}
SWEEP_KEYS = {"fuente": "source", "acceso": "access", "huecos": "gaps", "nota": "note"}
DATUM_KEYS = {"hueco": "gap", "descripcion": "description", "magnitud": "quantity", "valor": "value",
              "rango": "range", "unidad": "unit", "fecha_dato": "data_date",
              "fecha_consulta": "retrieval_date", "nivel": "reliability", "fiabilidad": "reliability",
              "estado": "status", "supuesto": "assumption", "tolerancia": "tolerance", "tipo": "type",
              "nota": "note", "fuente": "source"}
SOURCE_KEYS = {"documento": "document"}
CONTRADICTION_KEYS = {"datos": "data", "manda": "prevails", "razon": "reason"}
GAP_STATUS_ES = {"con_dato": "has_data", "sin_dato": "no_data"}
ACCESS_ES = {"abierta": "open", "lo_baja_la_persona": "person_fetches",
             "sin_fuente_publica": "no_public_source", "no_responde": "no_response"}
DATUM_STATUS_ES = {"verificado": "verified", "por_confirmar": "to_confirm", "calculado": "calculated",
                   "no_encontrado": "not_found"}
TYPE_ES = {"norma": "norm"}

CODES = {
    "E01": "a required field is missing",
    "E02": "reliability level outside A-D",
    "E03": "invalid date (written DD-MM-YYYY)",
    "E04": "datum without a source (no http(s) url or document)",
    "E05": "gap without a usable datum and not declared «no_data» with the action that closes it",
    "E06": "usable D datum not marked as an ASSUMPTION",
    "E07": "unresolved numeric contradiction (not listed in «contradictions»)",
    "E08": "calculated datum that does not match its formula",
    "E09": "calculated datum with a better level than its worst input",
    "E10": "repeated id",
    "E11": "reference to a gap or datum that does not exist",
    "E12": "gap with data but no valid «chosen» or no «choice_reason»",
    "E13": "«not_found» datum marked usable",
    "E14": "datum calculated on an ASSUMPTION that is not marked as an ASSUMPTION",
    "E15": "usable datum still to confirm not marked as an ASSUMPTION",
    "E16": "malformed value or range",
    "E17": "badly recorded contradiction (prevailing datum outside its data, or no reason)",
    "E18": "status or access outside the allowed values",
    "E19": "invalid formula (only ids, numbers and + - * / ** parentheses)",
    "A01": "datum older than the validity window",
    "A02": "chosen datum from a single source (no cross-check)",
    "A03": "datum without its own date",
    "A04": "same quantity in different units: not compared",
    "A05": "source the person has to fetch",
}


# ----------------------------------------------------------------------------------------------
# loading: Spanish keys accepted
# ----------------------------------------------------------------------------------------------

def _rename(d, keys):
    return {keys.get(k, k): v for k, v in d.items()} if isinstance(d, dict) else d


def normalize(inv):
    """English keys and values. A file written before v1.1 (Spanish keys) comes out the same."""
    if not isinstance(inv, dict):
        return inv
    out = _rename(inv, ROOT_KEYS)
    gaps = []
    for g in out.get("gaps", []) or []:
        g = _rename(g, GAP_KEYS)
        if isinstance(g, dict):
            g["status"] = GAP_STATUS_ES.get(g.get("status"), g.get("status"))
        gaps.append(g)
    sweep = []
    for b in out.get("sweep", []) or []:
        b = _rename(b, SWEEP_KEYS)
        if isinstance(b, dict):
            b["access"] = ACCESS_ES.get(b.get("access"), b.get("access"))
        sweep.append(b)
    data = []
    for d in out.get("data", []) or []:
        d = _rename(d, DATUM_KEYS)
        if isinstance(d, dict):
            d["status"] = DATUM_STATUS_ES.get(d.get("status"), d.get("status"))
            if "type" in d:
                d["type"] = TYPE_ES.get(d["type"], d["type"])
            if d.get("data_date") == "sin_fecha":
                d["data_date"] = UNDATED
            if isinstance(d.get("source"), dict):
                d["source"] = _rename(d["source"], SOURCE_KEYS)
        data.append(d)
    contradictions = [_rename(c, CONTRADICTION_KEYS) for c in out.get("contradictions", []) or []]
    for key, value in (("gaps", gaps), ("sweep", sweep), ("data", data), ("contradictions", contradictions)):
        if key in out:
            out[key] = value
    return out


# ----------------------------------------------------------------------------------------------
# utilities
# ----------------------------------------------------------------------------------------------

def read_date(txt):
    """DD-MM-YYYY -> date, or None if it is not a valid date."""
    if not isinstance(txt, str):
        return None
    parts = txt.strip().split("-")
    if len(parts) != 3 or len(parts[0]) != 2 or len(parts[1]) != 2 or len(parts[2]) != 4:
        return None
    try:
        return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except ValueError:
        return None


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def formula_ids(formula):
    tree = ast.parse(formula, mode="eval")
    return sorted({n.id for n in ast.walk(tree) if isinstance(n, ast.Name)})


def eval_formula(formula, values):
    """Evaluates an arithmetic formula with datum ids as variables. No eval()."""
    tree = ast.parse(formula, mode="eval")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and is_number(n.value):
            return float(n.value)
        if isinstance(n, ast.Name):
            if n.id not in values:
                raise KeyError(n.id)
            return float(values[n.id])
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                return a / b
            if isinstance(n.op, ast.Pow):
                return a ** b
        raise ValueError(f"element not allowed: {ast.dump(n)[:40]}")

    return ev(tree)


def has_source(d):
    f = d.get("source")
    if not isinstance(f, dict):
        return False
    url = f.get("url") or ""
    doc = f.get("document") or ""
    url_ok = isinstance(url, str) and url.startswith(("http://", "https://"))
    doc_ok = isinstance(doc, str) and doc.strip() != ""
    return url_ok or doc_ok


def source_key(d):
    f = d.get("source") or {}
    return (f.get("url") or f.get("document") or "").strip()


def usage(d):
    """What the executor and the auditor read: yes (enters) · ASSUMPTION (enters, marked) · no."""
    if not d.get("usable"):
        return "no"
    return "ASSUMPTION" if d.get("assumption") else "yes"


# ----------------------------------------------------------------------------------------------
# validation
# ----------------------------------------------------------------------------------------------

def validate(inv, threshold=None):
    inv = normalize(inv)
    errors, warnings = [], []

    def err(code, ref, detail=""):
        errors.append({"code": code, "ref": ref, "detail": detail or CODES[code]})

    def warn(code, ref, detail=""):
        warnings.append({"code": code, "ref": ref, "detail": detail or CODES[code]})

    for c in ROOT_FIELDS:
        if c not in inv:
            err("E01", "root", f"«{c}» is missing")
    if any(e["ref"] == "root" for e in errors):
        return result(errors, warnings, [], [], [])

    d_inv = read_date(inv["research_date"])
    if d_inv is None:
        err("E03", "research_date")
    if threshold is None:
        threshold = float(inv.get("contradiction_threshold", DEFAULT_THRESHOLD))
    validity = int(inv.get("validity_days", DEFAULT_VALIDITY))

    # --- gaps
    gaps = {}
    for h in inv["gaps"]:
        hid = h.get("id", "?")
        missing = [c for c in GAP_FIELDS if c not in h]
        if missing:
            err("E01", hid, "missing: " + ", ".join(missing))
            continue
        if hid in gaps:
            err("E10", hid)
            continue
        if h["status"] not in GAP_STATUS:
            err("E18", hid, f"status «{h['status']}»")
            continue
        gaps[hid] = h

    # --- obtainability sweep
    if not inv["sweep"]:
        err("E01", "sweep", "the obtainability sweep comes before researching and cannot be empty")
    for b in inv["sweep"]:
        bid = b.get("id", "?")
        missing = [c for c in SWEEP_FIELDS if c not in b]
        if missing:
            err("E01", bid, "missing: " + ", ".join(missing))
            continue
        if b["access"] not in ACCESS:
            err("E18", bid, f"access «{b['access']}»")
        for hid in b["gaps"]:
            if hid not in gaps:
                err("E11", bid, f"gap «{hid}»")
        if b["access"] == "person_fetches":
            warn("A05", bid, f"{b['source']}: {b.get('note', 'the person opens it')}")

    # --- data: fields and format
    data, valid = {}, {}
    for d in inv["data"]:
        did = d.get("id", "?")
        missing = [c for c in DATUM_FIELDS if c not in d]
        if missing:
            err("E01", did, "missing: " + ", ".join(missing))
            continue
        if did in data:
            err("E10", did)
            continue
        data[did] = d
        ok = True
        if d["gap"] not in gaps:
            err("E11", did, f"gap «{d['gap']}»")
            ok = False
        if d["reliability"] not in LEVELS:
            err("E02", did, f"reliability «{d['reliability']}»")
            ok = False
        if d["status"] not in DATUM_STATUS:
            err("E18", did, f"status «{d['status']}»")
            ok = False
        if read_date(d["retrieval_date"]) is None:
            err("E03", did, f"retrieval_date «{d['retrieval_date']}»")
            ok = False
        if d["data_date"] == UNDATED:
            warn("A03", did)
        elif read_date(d["data_date"]) is None:
            err("E03", did, f"data_date «{d['data_date']}»")
            ok = False
        elif d_inv and d.get("type") != "norm" and (d_inv - read_date(d["data_date"])).days > validity:
            warn("A01", did, f"data_date {d['data_date']}, more than {validity} days before the research")
        # value
        v = d["value"]
        if v is None and d["status"] != "not_found":
            err("E16", did, "null value in a datum that is not «not_found»")
            ok = False
        elif v is not None and not (is_number(v) or (isinstance(v, str) and v.strip())):
            err("E16", did, "the value is a number or a non-empty text")
            ok = False
        if "range" in d:
            r = d["range"]
            if not (isinstance(r, list) and len(r) == 2 and all(is_number(x) for x in r) and r[0] <= r[1]):
                err("E16", did, "range = [minimum, maximum], numeric")
                ok = False
            elif is_number(v) and not (r[0] <= v <= r[1]):
                err("E16", did, f"value {v} outside the range {r}")
                ok = False
        # source or formula
        if d["status"] == "calculated":
            if not isinstance(d.get("formula"), str) or not d["formula"].strip():
                err("E04", did, "a calculated datum carries «formula» with the ids of its inputs")
                ok = False
        elif not has_source(d):
            err("E04", did)
            ok = False
        # usage rules
        if d["usable"] and d["status"] == "not_found":
            err("E13", did)
        if d["usable"] and d["reliability"] == "D" and not d["assumption"]:
            err("E06", did)
        if d["usable"] and d["status"] == "to_confirm" and not d["assumption"]:
            err("E15", did)
        if ok:
            valid[did] = d

    # --- calculation chain
    for did, d in valid.items():
        if d["status"] != "calculated":
            continue
        try:
            inputs = formula_ids(d["formula"])
        except SyntaxError:
            err("E19", did, d["formula"])
            continue
        missing = [i for i in inputs if i not in data]
        if missing:
            err("E11", did, "inputs that do not exist: " + ", ".join(missing))
            continue
        non_num = [i for i in inputs if not is_number(data[i].get("value"))]
        if non_num:
            err("E19", did, "inputs without a numeric value: " + ", ".join(non_num))
            continue
        try:
            calc = eval_formula(d["formula"], {i: data[i]["value"] for i in inputs})
        except (ValueError, KeyError, ZeroDivisionError) as ex:
            err("E19", did, str(ex))
            continue
        tol = float(d.get("tolerance", 0.001))
        v = d["value"]
        if not is_number(v) or abs(calc - v) > max(1e-9, tol * abs(calc)):
            err("E08", did, f"{d['formula']} = {calc:.6g}, the datum says {v}")
        worst = max((data[i]["reliability"] for i in inputs if data[i].get("reliability") in LEVELS),
                    key=LEVELS.index, default="A")
        if LEVELS.index(d["reliability"]) < LEVELS.index(worst):
            err("E09", did, f"reliability {d['reliability']}, its worst input is {worst}")
        if any(data[i].get("assumption") for i in inputs) and not d["assumption"]:
            err("E14", did)

    # --- gaps: a usable datum or «no_data»
    usables = {}
    for did, d in valid.items():
        if d["usable"] and d["status"] != "not_found":
            usables.setdefault(d["gap"], []).append(did)
    chosen_out = []
    for hid, h in gaps.items():
        if h["status"] == "no_data":
            if not str(h.get("how_to_close", "")).strip():
                err("E05", hid, "«no_data» requires «how_to_close» (a call, a quote, a request)")
            continue
        if not usables.get(hid):
            err("E05", hid, "«has_data» without any usable datum")
            continue
        chosen = h.get("chosen")
        lst = [chosen] if isinstance(chosen, str) else chosen
        if not lst or not isinstance(lst, list) or not str(h.get("choice_reason", "")).strip():
            err("E12", hid, "«chosen» or «choice_reason» is missing")
            continue
        bad = [e for e in lst if e not in usables[hid]]
        if bad:
            err("E12", hid, "chosen datum that is not a usable datum of this gap: " + ", ".join(map(str, bad)))
            continue
        chosen_out.append({"gap": hid, "method": h["method"], "for": h["for"], "chosen": [
            {"id": e, "value": valid[e]["value"], "unit": valid[e]["unit"],
             "reliability": valid[e]["reliability"], "usage": usage(valid[e]),
             "source": source_key(valid[e]) or ("= " + valid[e].get("formula", ""))} for e in lst]})
        for e in lst:
            de = valid[e]
            if de["status"] == "calculated" or de["assumption"] or de.get("type") == "norm":
                continue
            sources = {source_key(x) for x in valid.values()
                       if x["gap"] == hid and x["quantity"] == de["quantity"] and x["status"] != "calculated"}
            if len(sources) < 2:
                warn("A02", e, f"«{de['quantity']}» has a single source")

    # --- contradictions
    groups, units = {}, {}
    for did, d in valid.items():
        if is_number(d["value"]) and d["status"] != "not_found":
            groups.setdefault((d["gap"], d["quantity"], d["unit"]), []).append(did)
            units.setdefault((d["gap"], d["quantity"]), set()).add(d["unit"])
    for (hid, qty), us in sorted(units.items()):
        if len(us) > 1:
            warn("A04", f"{hid}:{qty}", "units: " + " | ".join(sorted(us)))

    recorded = []
    for c in inv["contradictions"]:
        ids = c.get("data") or []
        unknown = [i for i in ids if i not in data]
        if unknown:
            err("E11", "contradictions", "data that do not exist: " + ", ".join(unknown))
            continue
        if len(ids) < 2 or c.get("prevails") not in ids or not str(c.get("reason", "")).strip():
            err("E17", ",".join(ids) or "contradictions")
            continue
        recorded.append(set(ids))

    detected = []
    for (hid, qty, unit), ids in sorted(groups.items()):
        if len(ids) < 2:
            continue
        vals = [float(valid[i]["value"]) for i in ids]
        lo, hi = min(vals), max(vals)
        base = max(abs(lo), abs(hi))
        gap = 0.0 if base == 0 else (hi - lo) / (abs(lo) if lo > 0 else base)
        if gap > threshold:
            detected.append({"gap": hid, "quantity": qty, "unit": unit, "data": sorted(ids),
                             "spread": round(gap, 4)})
            if not any(set(ids) <= r for r in recorded):
                err("E07", f"{hid}:{qty}", f"{', '.join(sorted(ids))}: spread {gap:.1%} > threshold {threshold:.0%}")

    no_data = sorted(h for h, x in gaps.items() if x["status"] == "no_data")
    return result(errors, warnings, detected, no_data, chosen_out)


def result(errors, warnings, detected, no_data, chosen):
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "contradictions_detected": detected, "gaps_without_data": no_data, "chosen": chosen}


# ----------------------------------------------------------------------------------------------
# output
# ----------------------------------------------------------------------------------------------

def report(res, inv):
    inv = normalize(inv)
    n_d = len(inv.get("data", []))
    n_h = len(inv.get("gaps", []))
    print(f"Research: {inv.get('task', '?')}")
    print(f"{n_h} gaps · {n_d} data · {len(res['contradictions_detected'])} contradictions over the threshold"
          f" · gaps without data: {', '.join(res['gaps_without_data']) or 'none'}")
    for e in res["errors"]:
        print(f"  ERROR {e['code']} [{e['ref']}] {e['detail']}")
    for a in res["warnings"]:
        print(f"  warning {a['code']} [{a['ref']}] {a['detail']}")
    for c in res["contradictions_detected"]:
        print(f"  contradiction {c['gap']}:{c['quantity']} ({c['unit']}): {', '.join(c['data'])}"
              f" · spread {c['spread']:.1%}")
    print("OK" if res["ok"] else f"FAIL ({len(res['errors'])})")


def fmt_num(v):
    """Number with thousands separator and up to 4 decimals."""
    return f"{v:,.4f}".rstrip("0").rstrip(".")


def fmt_value(d):
    v = d.get("value")
    txt = fmt_num(v) if is_number(v) else str(v)
    if "range" in d:
        txt += f" (range {fmt_num(d['range'][0])} to {fmt_num(d['range'][1])})"
    return txt


def table_md(inv):
    """Tables to paste into RESEARCH.md: so no figure is copied by hand."""
    inv = normalize(inv)
    rows = ["| Id | Gap | Datum | Value | Unit | Data date | Source | Reliability | Status | Usage |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for d in inv["data"]:
        f = d.get("source") or {}
        source = f.get("url") or f.get("document") or ("= " + d.get("formula", ""))
        rows.append(f"| {d['id']} | {d['gap']} | {d['description']} | {fmt_value(d)} | {d['unit']} | "
                    f"{d['data_date']} | {source} | {d['reliability']} | {d['status']} | {usage(d)} |")
    out = "\n".join(rows)
    if inv.get("contradictions"):
        out += "\n\n| Data | Prevails | Why |\n|---|---|---|\n"
        out += "\n".join(f"| {', '.join(c['data'])} | {c['prevails']} | {c['reason']} |"
                         for c in inv["contradictions"])
    return out


# ----------------------------------------------------------------------------------------------
# --test
# ----------------------------------------------------------------------------------------------

def signatures(lst):
    return sorted(f"{x['code']}:{x['ref']}" for x in lst)


def run_test():
    tests = SKILL_ROOT / "tests"
    expected = json.loads((tests / "expected.json").read_text(encoding="utf-8"))
    failures = []

    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        if not cond:
            failures.append(msg)

    print("1. Valid sample case: no errors, the expected warnings and contradictions")
    inv = json.loads((tests / "sample-case.json").read_text(encoding="utf-8"))
    res = validate(inv)
    exp = expected["sample_case"]
    check(res["ok"], f"no errors ({signatures(res['errors'])})")
    check(signatures(res["warnings"]) == sorted(exp["warnings"]), f"warnings {signatures(res['warnings'])}")
    check([c["data"] for c in res["contradictions_detected"]] == exp["contradictions_detected"],
          f"contradictions detected {[c['data'] for c in res['contradictions_detected']]}")
    check(res["gaps_without_data"] == exp["gaps_without_data"], f"gaps without data {res['gaps_without_data']}")
    usage_got = {c["gap"]: [(x["id"], x["reliability"], x["usage"]) for x in c["chosen"]] for c in res["chosen"]}
    usage_exp = {g: [tuple(x) for x in v] for g, v in exp["chosen"].items()}
    check(usage_got == usage_exp, f"chosen data with reliability and usage {usage_got}")

    print("2. Case with planted errors: each error is detected, and none extra")
    inv_e = json.loads((tests / "case-with-errors.json").read_text(encoding="utf-8"))
    res_e = validate(inv_e)
    exp_e = sorted(expected["case_with_errors"]["errors"])
    got_e = signatures(res_e["errors"])
    check(not res_e["ok"], "the case with errors fails")
    for f in exp_e:
        check(f in got_e, f"detects {f} · {CODES[f.split(':')[0]]}")
    extra = [f for f in got_e if f not in exp_e]
    check(not extra, f"no extra errors {extra}")

    print("3. Second path of the calculation chain: the evaluator against values computed by hand")
    d = {x["id"]: x for x in inv["data"]}
    for did, by_hand in exp["computed_by_hand"].items():
        x = d[did]
        calc = eval_formula(x["formula"], {i: d[i]["value"] for i in formula_ids(x["formula"])})
        check(abs(calc - by_hand) < 1e-9, f"{did}: {x['formula']} = {calc:.6g}; by hand {by_hand}")
    check(abs(eval_formula("(a + b) * 2 ** 2 / -c", {"a": 1, "b": 3, "c": 4}) + 4.0) < 1e-12,
          "evaluator: (1 + 3) · 2² / −4 = −4")
    try:
        eval_formula("__import__('os')", {})
        check(False, "the evaluator rejects calls")
    except ValueError:
        check(True, "the evaluator rejects calls (it does not use eval)")

    print("4. The threshold rules: with a 50% threshold the case's contradiction is no longer detected")
    res_u = validate(inv, threshold=0.50)
    check(res_u["ok"] and not res_u["contradictions_detected"], "threshold 0.50: zero contradictions detected")

    print("5. A file written before v1.1 (Spanish keys and values) gives the same result")
    inv_es = json.loads((tests / "sample-case-es.json").read_text(encoding="utf-8"))
    res_es = validate(inv_es)
    check(res_es["ok"], f"Spanish keys: no errors ({signatures(res_es['errors'])})")
    check(signatures(res_es["warnings"]) == signatures(res["warnings"]), "same warnings as the English file")
    check([c["data"] for c in res_es["contradictions_detected"]] == [c["data"] for c in res["contradictions_detected"]]
          and res_es["gaps_without_data"] == res["gaps_without_data"],
          "same contradictions and gaps without data")
    usage_es = {c["gap"]: [(x["id"], x["reliability"], x["usage"]) for x in c["chosen"]] for c in res_es["chosen"]}
    check(usage_es == usage_got, "same chosen data, reliability and usage («nivel», «elegido», «supuesto»)")
    def cols(md):
        return [[c.strip() for c in row.split("|")[1:-1]] for row in md.splitlines()[2:] if row.startswith("| ")]

    keep = (0, 1, 7, 8, 9)                    # Id, Gap, Reliability, Status, Usage
    t_en = [[r[k] for k in keep] for r in cols(table_md(inv)) if len(r) == 10]
    t_es = [[r[k] for k in keep] for r in cols(table_md(inv_es)) if len(r) == 10]
    check(t_en and t_es == t_en, "--table reads the Spanish file (same ids, reliability, status and usage)")

    print("OK" if not failures else f"FAIL ({len(failures)})")
    return 0 if not failures else 1


def _alias(ap, old, dest, **kw):
    """A pre-v1.1 Spanish flag that still works and does not show in --help."""
    ap.add_argument(old, dest=dest, help=argparse.SUPPRESS, default=argparse.SUPPRESS, **kw)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validates context/research-data.json of the research stage.")
    ap.add_argument("file", nargs="?", help="path to research-data.json (or an old datos-investigados.json)")
    ap.add_argument("--threshold", type=float,
                    help="relative spread that counts as a contradiction (default: the JSON's, or 0.10)")
    ap.add_argument("--table", action="store_true", help="prints the Markdown tables for RESEARCH.md")
    ap.add_argument("--json", action="store_true", help="prints the result as JSON")
    ap.add_argument("--test", action="store_true", help="runs the tests in tests/ and ends in OK or FAIL")
    _alias(ap, "--umbral", "threshold", type=float)
    _alias(ap, "--tabla", "table", action="store_true")
    _alias(ap, "--probar", "test", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.test:
        return run_test()
    if not a.file:
        ap.error("the file is missing (or use --test)")
    try:
        inv = json.loads(Path(a.file).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as ex:
        print(f"ERROR: could not read {a.file}: {ex}", file=sys.stderr)
        return 2
    res = validate(inv, a.threshold)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif a.table:
        print(table_md(inv))
    else:
        report(res, inv)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
