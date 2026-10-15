#!/usr/bin/env python3
"""investigar · valida la investigación de un encargo (datos-investigados.json).

Revisa que cada dato traiga valor, unidad, fecha, fuente, fecha de consulta y nivel de fiabilidad
(A a D); que cada hueco tenga un dato usable o esté declarado «sin dato» con la gestión que lo
cierra; que ningún dato D (ni uno por confirmar) entre a un cálculo sin marcarse SUPUESTO; que los
datos calculados cuadren con su fórmula y no hereden un nivel mejor que el de su peor insumo; y
detecta contradicciones numéricas entre datos que miden lo mismo.

Uso:
    python validar_investigacion.py <datos-investigados.json> [--umbral 0.10] [--tabla] [--json]
    python validar_investigacion.py --probar

Solo biblioteca estándar. Termina en 0 si no hay errores (los avisos no fallan), 1 si los hay.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import date
from pathlib import Path

RAIZ_SKILL = Path(__file__).resolve().parents[1]

NIVELES = ("A", "B", "C", "D")
ESTADOS_DATO = ("verificado", "por_confirmar", "calculado", "no_encontrado")
ESTADOS_HUECO = ("con_dato", "sin_dato")
ACCESOS = ("abierta", "lo_baja_la_persona", "sin_fuente_publica", "no_responde")
CAMPOS_RAIZ = ("encargo", "fecha_investigacion", "huecos", "barrido", "datos", "contradicciones")
CAMPOS_HUECO = ("id", "pregunta", "precision", "metodo", "para_que", "estado")
CAMPOS_DATO = ("id", "hueco", "descripcion", "magnitud", "valor", "unidad", "fecha_dato",
               "fecha_consulta", "nivel", "estado", "usable", "supuesto")
CAMPOS_BARRIDO = ("id", "fuente", "acceso", "huecos")
UMBRAL_POR_DEFECTO = 0.10
VIGENCIA_POR_DEFECTO = 365

CODIGOS = {
    "E01": "falta un campo obligatorio",
    "E02": "nivel de fiabilidad fuera de A-D",
    "E03": "fecha inválida (se escribe DD-MM-AAAA)",
    "E04": "dato sin fuente (falta url http(s) o documento)",
    "E05": "hueco sin dato usable y sin declararse «sin dato» con la gestión que lo cierra",
    "E06": "dato D usable sin marcarse SUPUESTO",
    "E07": "contradicción numérica sin resolver (no está en «contradicciones»)",
    "E08": "dato calculado que no cuadra con su fórmula",
    "E09": "dato calculado con un nivel mejor que el de su peor insumo",
    "E10": "id repetido",
    "E11": "referencia a un hueco o dato que no existe",
    "E12": "hueco con dato sin «elegido» válido o sin «razon_eleccion»",
    "E13": "dato «no_encontrado» marcado usable",
    "E14": "dato calculado sobre un SUPUESTO que no se marca SUPUESTO",
    "E15": "dato por confirmar usable sin marcarse SUPUESTO",
    "E16": "valor o rango mal formado",
    "E17": "contradicción mal registrada (manda fuera de datos o sin razón)",
    "E18": "estado o acceso fuera de los valores permitidos",
    "E19": "fórmula inválida (solo ids, números y + - * / ** paréntesis)",
    "A01": "dato más viejo que la vigencia",
    "A02": "dato elegido de una sola fuente (sin contraste)",
    "A03": "dato sin fecha propia",
    "A04": "misma magnitud en unidades distintas: no se comparan",
    "A05": "fuente que tiene que bajar la persona",
}


# ----------------------------------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------------------------------

def leer_fecha(txt):
    """DD-MM-AAAA → date, o None si no es una fecha válida."""
    if not isinstance(txt, str):
        return None
    partes = txt.strip().split("-")
    if len(partes) != 3 or len(partes[0]) != 2 or len(partes[1]) != 2 or len(partes[2]) != 4:
        return None
    try:
        return date(int(partes[2]), int(partes[1]), int(partes[0]))
    except ValueError:
        return None


def es_numero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def ids_de_formula(formula):
    arbol = ast.parse(formula, mode="eval")
    return sorted({n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)})


def evaluar_formula(formula, valores):
    """Evalúa una fórmula aritmética con ids de datos como variables. Sin eval()."""
    arbol = ast.parse(formula, mode="eval")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and es_numero(n.value):
            return float(n.value)
        if isinstance(n, ast.Name):
            if n.id not in valores:
                raise KeyError(n.id)
            return float(valores[n.id])
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
        raise ValueError(f"elemento no permitido: {ast.dump(n)[:40]}")

    return ev(arbol)


def tiene_fuente(d):
    f = d.get("fuente")
    if not isinstance(f, dict):
        return False
    url = f.get("url") or ""
    doc = f.get("documento") or ""
    url_ok = isinstance(url, str) and url.startswith(("http://", "https://"))
    doc_ok = isinstance(doc, str) and doc.strip() != ""
    return url_ok or doc_ok


def clave_fuente(d):
    f = d.get("fuente") or {}
    return (f.get("url") or f.get("documento") or "").strip()


# ----------------------------------------------------------------------------------------------
# validación
# ----------------------------------------------------------------------------------------------

def validar(inv, umbral=None):
    errores, avisos = [], []

    def err(cod, ref, detalle=""):
        errores.append({"codigo": cod, "ref": ref, "detalle": detalle or CODIGOS[cod]})

    def avi(cod, ref, detalle=""):
        avisos.append({"codigo": cod, "ref": ref, "detalle": detalle or CODIGOS[cod]})

    for c in CAMPOS_RAIZ:
        if c not in inv:
            err("E01", "raiz", f"falta «{c}»")
    if any(e["ref"] == "raiz" for e in errores):
        return resultado(errores, avisos, [], [])

    f_inv = leer_fecha(inv["fecha_investigacion"])
    if f_inv is None:
        err("E03", "fecha_investigacion")
    if umbral is None:
        umbral = float(inv.get("umbral_contradiccion", UMBRAL_POR_DEFECTO))
    vigencia = int(inv.get("vigencia_dias", VIGENCIA_POR_DEFECTO))

    # --- huecos
    huecos = {}
    for h in inv["huecos"]:
        hid = h.get("id", "?")
        faltan = [c for c in CAMPOS_HUECO if c not in h]
        if faltan:
            err("E01", hid, "faltan: " + ", ".join(faltan))
            continue
        if hid in huecos:
            err("E10", hid)
            continue
        if h["estado"] not in ESTADOS_HUECO:
            err("E18", hid, f"estado «{h['estado']}»")
            continue
        huecos[hid] = h

    # --- barrido de obtenibilidad
    if not inv["barrido"]:
        err("E01", "barrido", "el barrido de obtenibilidad va antes de investigar y no puede quedar vacío")
    for b in inv["barrido"]:
        bid = b.get("id", "?")
        faltan = [c for c in CAMPOS_BARRIDO if c not in b]
        if faltan:
            err("E01", bid, "faltan: " + ", ".join(faltan))
            continue
        if b["acceso"] not in ACCESOS:
            err("E18", bid, f"acceso «{b['acceso']}»")
        for hid in b["huecos"]:
            if hid not in huecos:
                err("E11", bid, f"hueco «{hid}»")
        if b["acceso"] == "lo_baja_la_persona":
            avi("A05", bid, f"{b['fuente']}: {b.get('nota', 'la abre la persona')}")

    # --- datos: campos y formato
    datos, validos = {}, {}
    for d in inv["datos"]:
        did = d.get("id", "?")
        faltan = [c for c in CAMPOS_DATO if c not in d]
        if faltan:
            err("E01", did, "faltan: " + ", ".join(faltan))
            continue
        if did in datos:
            err("E10", did)
            continue
        datos[did] = d
        ok = True
        if d["hueco"] not in huecos:
            err("E11", did, f"hueco «{d['hueco']}»")
            ok = False
        if d["nivel"] not in NIVELES:
            err("E02", did, f"nivel «{d['nivel']}»")
            ok = False
        if d["estado"] not in ESTADOS_DATO:
            err("E18", did, f"estado «{d['estado']}»")
            ok = False
        if leer_fecha(d["fecha_consulta"]) is None:
            err("E03", did, f"fecha_consulta «{d['fecha_consulta']}»")
            ok = False
        if d["fecha_dato"] == "sin_fecha":
            avi("A03", did)
        elif leer_fecha(d["fecha_dato"]) is None:
            err("E03", did, f"fecha_dato «{d['fecha_dato']}»")
            ok = False
        elif f_inv and d.get("tipo") != "norma" and (f_inv - leer_fecha(d["fecha_dato"])).days > vigencia:
            avi("A01", did, f"fecha_dato {d['fecha_dato']}, más de {vigencia} días antes de la investigación")
        # valor
        v = d["valor"]
        if v is None and d["estado"] != "no_encontrado":
            err("E16", did, "valor nulo en un dato que no es «no_encontrado»")
            ok = False
        elif v is not None and not (es_numero(v) or (isinstance(v, str) and v.strip())):
            err("E16", did, "el valor es un número o un texto no vacío")
            ok = False
        if "rango" in d:
            r = d["rango"]
            if not (isinstance(r, list) and len(r) == 2 and all(es_numero(x) for x in r) and r[0] <= r[1]):
                err("E16", did, "rango = [mínimo, máximo] numéricos")
                ok = False
            elif es_numero(v) and not (r[0] <= v <= r[1]):
                err("E16", did, f"valor {v} fuera del rango {r}")
                ok = False
        # fuente o fórmula
        if d["estado"] == "calculado":
            if not isinstance(d.get("formula"), str) or not d["formula"].strip():
                err("E04", did, "un dato calculado lleva «formula» con los ids de sus insumos")
                ok = False
        elif not tiene_fuente(d):
            err("E04", did)
            ok = False
        # reglas de uso
        if d["usable"] and d["estado"] == "no_encontrado":
            err("E13", did)
        if d["usable"] and d["nivel"] == "D" and not d["supuesto"]:
            err("E06", did)
        if d["usable"] and d["estado"] == "por_confirmar" and not d["supuesto"]:
            err("E15", did)
        if ok:
            validos[did] = d

    # --- cadena de cálculo
    for did, d in validos.items():
        if d["estado"] != "calculado":
            continue
        try:
            insumos = ids_de_formula(d["formula"])
        except SyntaxError:
            err("E19", did, d["formula"])
            continue
        faltan = [i for i in insumos if i not in datos]
        if faltan:
            err("E11", did, "insumos inexistentes: " + ", ".join(faltan))
            continue
        no_num = [i for i in insumos if not es_numero(datos[i].get("valor"))]
        if no_num:
            err("E19", did, "insumos sin valor numérico: " + ", ".join(no_num))
            continue
        try:
            calc = evaluar_formula(d["formula"], {i: datos[i]["valor"] for i in insumos})
        except (ValueError, KeyError, ZeroDivisionError) as ex:
            err("E19", did, str(ex))
            continue
        tol = float(d.get("tolerancia", 0.001))
        v = d["valor"]
        if not es_numero(v) or abs(calc - v) > max(1e-9, tol * abs(calc)):
            err("E08", did, f"{d['formula']} = {calc:.6g}, el dato dice {v}")
        peor = max((datos[i]["nivel"] for i in insumos if datos[i].get("nivel") in NIVELES),
                   key=NIVELES.index, default="A")
        if NIVELES.index(d["nivel"]) < NIVELES.index(peor):
            err("E09", did, f"nivel {d['nivel']}, su peor insumo es {peor}")
        if any(datos[i].get("supuesto") for i in insumos) and not d["supuesto"]:
            err("E14", did)

    # --- huecos: dato usable o «sin dato»
    usables = {}
    for did, d in validos.items():
        if d["usable"] and d["estado"] != "no_encontrado":
            usables.setdefault(d["hueco"], []).append(did)
    for hid, h in huecos.items():
        if h["estado"] == "sin_dato":
            if not str(h.get("como_se_cierra", "")).strip():
                err("E05", hid, "«sin_dato» exige «como_se_cierra» (una llamada, una cotización, una solicitud)")
            continue
        if not usables.get(hid):
            err("E05", hid, "«con_dato» sin ningún dato usable")
            continue
        elegido = h.get("elegido")
        lista = [elegido] if isinstance(elegido, str) else elegido
        if not lista or not isinstance(lista, list) or not str(h.get("razon_eleccion", "")).strip():
            err("E12", hid, "falta «elegido» o «razon_eleccion»")
            continue
        malos = [e for e in lista if e not in usables[hid]]
        if malos:
            err("E12", hid, "elegido que no es un dato usable de este hueco: " + ", ".join(map(str, malos)))
            continue
        for e in lista:
            de = validos[e]
            if de["estado"] == "calculado" or de["supuesto"] or de.get("tipo") == "norma":
                continue
            fuentes = {clave_fuente(x) for x in validos.values()
                       if x["hueco"] == hid and x["magnitud"] == de["magnitud"] and x["estado"] != "calculado"}
            if len(fuentes) < 2:
                avi("A02", e, f"«{de['magnitud']}» tiene una sola fuente")

    # --- contradicciones
    grupos, unidades = {}, {}
    for did, d in validos.items():
        if es_numero(d["valor"]) and d["estado"] != "no_encontrado":
            grupos.setdefault((d["hueco"], d["magnitud"], d["unidad"]), []).append(did)
            unidades.setdefault((d["hueco"], d["magnitud"]), set()).add(d["unidad"])
    for (hid, mag), us in sorted(unidades.items()):
        if len(us) > 1:
            avi("A04", f"{hid}:{mag}", "unidades: " + " | ".join(sorted(us)))

    registradas = []
    for c in inv["contradicciones"]:
        ids = c.get("datos") or []
        desconocidos = [i for i in ids if i not in datos]
        if desconocidos:
            err("E11", "contradicciones", "datos inexistentes: " + ", ".join(desconocidos))
            continue
        if len(ids) < 2 or c.get("manda") not in ids or not str(c.get("razon", "")).strip():
            err("E17", ",".join(ids) or "contradicciones")
            continue
        registradas.append(set(ids))

    detectadas = []
    for (hid, mag, uni), ids in sorted(grupos.items()):
        if len(ids) < 2:
            continue
        vals = [float(validos[i]["valor"]) for i in ids]
        lo, hi = min(vals), max(vals)
        base = max(abs(lo), abs(hi))
        brecha = 0.0 if base == 0 else (hi - lo) / (abs(lo) if lo > 0 else base)
        if brecha > umbral:
            detectadas.append({"hueco": hid, "magnitud": mag, "unidad": uni, "datos": sorted(ids),
                               "brecha": round(brecha, 4)})
            if not any(set(ids) <= r for r in registradas):
                err("E07", f"{hid}:{mag}", f"{', '.join(sorted(ids))}: brecha {brecha:.1%} > umbral {umbral:.0%}")

    sin_dato = sorted(h for h, x in huecos.items() if x["estado"] == "sin_dato")
    return resultado(errores, avisos, detectadas, sin_dato)


def resultado(errores, avisos, detectadas, sin_dato):
    return {"ok": not errores, "errores": errores, "avisos": avisos,
            "contradicciones_detectadas": detectadas, "huecos_sin_dato": sin_dato}


# ----------------------------------------------------------------------------------------------
# salida
# ----------------------------------------------------------------------------------------------

def imprimir(res, inv):
    n_d = len(inv.get("datos", []))
    n_h = len(inv.get("huecos", []))
    print(f"Investigación: {inv.get('encargo', '?')}")
    print(f"{n_h} huecos · {n_d} datos · {len(res['contradicciones_detectadas'])} contradicciones sobre el umbral"
          f" · huecos sin dato: {', '.join(res['huecos_sin_dato']) or 'ninguno'}")
    for e in res["errores"]:
        print(f"  ERROR {e['codigo']} [{e['ref']}] {e['detalle']}")
    for a in res["avisos"]:
        print(f"  aviso {a['codigo']} [{a['ref']}] {a['detalle']}")
    for c in res["contradicciones_detectadas"]:
        print(f"  contradicción {c['hueco']}:{c['magnitud']} ({c['unidad']}): {', '.join(c['datos'])}"
              f" · brecha {c['brecha']:.1%}")
    print("OK" if res["ok"] else f"FALLA ({len(res['errores'])})")


def fmt_num(v):
    """Número a la chilena: miles con punto, decimales con coma (hasta 4)."""
    txt = f"{v:,.4f}".rstrip("0").rstrip(".")
    return txt.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_valor(d):
    v = d.get("valor")
    txt = fmt_num(v) if es_numero(v) else str(v)
    if "rango" in d:
        txt += f" (rango {fmt_num(d['rango'][0])} a {fmt_num(d['rango'][1])})"
    return txt


def tabla_md(inv):
    """Tablas para pegar en INVESTIGACION.md: así ninguna cifra se copia a mano."""
    filas = ["| Id | Hueco | Dato | Valor | Unidad | Fecha del dato | Fuente | Nivel | Estado | Uso |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for d in inv["datos"]:
        f = d.get("fuente") or {}
        fuente = f.get("url") or f.get("documento") or ("= " + d.get("formula", ""))
        uso = "SUPUESTO" if d.get("usable") and d.get("supuesto") else ("sí" if d.get("usable") else "no")
        filas.append(f"| {d['id']} | {d['hueco']} | {d['descripcion']} | {fmt_valor(d)} | {d['unidad']} | "
                     f"{d['fecha_dato']} | {fuente} | {d['nivel']} | {d['estado']} | {uso} |")
    out = "\n".join(filas)
    if inv.get("contradicciones"):
        out += "\n\n| Datos | Manda | Por qué |\n|---|---|---|\n"
        out += "\n".join(f"| {', '.join(c['datos'])} | {c['manda']} | {c['razon']} |" for c in inv["contradicciones"])
    return out


# ----------------------------------------------------------------------------------------------
# --probar
# ----------------------------------------------------------------------------------------------

def firmas(lista):
    return sorted(f"{x['codigo']}:{x['ref']}" for x in lista)


def probar():
    pr = RAIZ_SKILL / "pruebas"
    esperado = json.loads((pr / "esperado.json").read_text(encoding="utf-8"))
    fallas = []

    def chequear(cond, msg):
        print(("  ok   " if cond else "  FALLA ") + msg)
        if not cond:
            fallas.append(msg)

    print("1. Caso ficticio válido: sin errores, avisos y contradicciones esperados")
    inv = json.loads((pr / "caso-ficticio.json").read_text(encoding="utf-8"))
    res = validar(inv)
    esp = esperado["caso_ficticio"]
    chequear(res["ok"], f"sin errores ({firmas(res['errores'])})")
    chequear(firmas(res["avisos"]) == sorted(esp["avisos"]), f"avisos {firmas(res['avisos'])}")
    chequear([c["datos"] for c in res["contradicciones_detectadas"]] == esp["contradicciones_detectadas"],
             f"contradicciones detectadas {[c['datos'] for c in res['contradicciones_detectadas']]}")
    chequear(res["huecos_sin_dato"] == esp["huecos_sin_dato"], f"huecos sin dato {res['huecos_sin_dato']}")

    print("2. Caso con errores sembrados: cada error se detecta, y ninguno de más")
    inv_e = json.loads((pr / "caso-con-errores.json").read_text(encoding="utf-8"))
    res_e = validar(inv_e)
    esp_e = sorted(esperado["caso_con_errores"]["errores"])
    got_e = firmas(res_e["errores"])
    chequear(not res_e["ok"], "el caso con errores falla")
    for f in esp_e:
        chequear(f in got_e, f"detecta {f} · {CODIGOS[f.split(':')[0]]}")
    sobran = [f for f in got_e if f not in esp_e]
    chequear(not sobran, f"sin errores de más {sobran}")

    print("3. Segundo camino de la cadena de cálculo: el evaluador contra valores calculados a mano")
    d = {x["id"]: x for x in inv["datos"]}
    for did, a_mano in esp["calculados_a_mano"].items():
        x = d[did]
        calc = evaluar_formula(x["formula"], {i: d[i]["valor"] for i in ids_de_formula(x["formula"])})
        chequear(abs(calc - a_mano) < 1e-9, f"{did}: {x['formula']} = {calc:.6g}; a mano {a_mano}")
    chequear(abs(evaluar_formula("(a + b) * 2 ** 2 / -c", {"a": 1, "b": 3, "c": 4}) + 4.0) < 1e-12,
             "evaluador: (1 + 3) · 2² / −4 = −4")
    try:
        evaluar_formula("__import__('os')", {})
        chequear(False, "el evaluador rechaza llamadas")
    except ValueError:
        chequear(True, "el evaluador rechaza llamadas (no usa eval)")

    print("4. El umbral manda: con umbral 50 % la contradicción del caso deja de detectarse")
    res_u = validar(inv, umbral=0.50)
    chequear(res_u["ok"] and not res_u["contradicciones_detectadas"], "umbral 0,50: cero contradicciones detectadas")

    print("OK" if not fallas else f"FALLA ({len(fallas)})")
    return 0 if not fallas else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Valida contexto/datos-investigados.json de la etapa Investigar.")
    ap.add_argument("archivo", nargs="?", help="ruta a datos-investigados.json")
    ap.add_argument("--umbral", type=float, help="brecha relativa que cuenta como contradicción (por defecto la del JSON o 0,10)")
    ap.add_argument("--tabla", action="store_true", help="imprime las tablas en Markdown para INVESTIGACION.md")
    ap.add_argument("--json", action="store_true", help="imprime el resultado en JSON")
    ap.add_argument("--probar", action="store_true", help="corre las pruebas de pruebas/ y termina en OK o FALLA")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.probar:
        return probar()
    if not a.archivo:
        ap.error("falta el archivo (o usa --probar)")
    try:
        inv = json.loads(Path(a.archivo).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as ex:
        print(f"ERROR: no se pudo leer {a.archivo}: {ex}", file=sys.stderr)
        return 2
    res = validar(inv, a.umbral)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif a.tabla:
        print(tabla_md(inv))
    else:
        imprimir(res, inv)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
