# -*- coding: utf-8 -*-
"""
mapa_contexto · etapa 0 (Cartografiar) de ingeniero-agentico.

    python mapa_contexto.py <carpeta> [<carpeta> ...] --salida <contexto/>
                            [--excluir PATRON ...] [--umbral 0.20] [--max-palabras 3000]
                            [--max-mb 25] [--graphify]
    python mapa_contexto.py --probar

Recorre las carpetas del encargo y deja en <salida>:

- grafo.json   nodos (archivos) y aristas (enlaces entre ellos), con la forma de graphify
               (nodes: [{id, label, type, ...}], links: [{source, target, relation}]).
- huellas.json ruta → tamaño, fecha y sha1 corto de cada archivo (lo que decide el modo).
- MAPA.md      lo que hay, dónde y de cuándo, en ≤ 3.000 palabras, con el MODO arriba.

Sin LLM: el resumen de una línea sale de la estructura del archivo (frontmatter, título,
docstring, claves, hojas, metadatos). Lo mismo entra, lo mismo sale.

El MODO se decide comparando con el huellas.json anterior:
- no hay huellas (o no hay MAPA.md, o cambiaron las raíces) → primera-vez;
- cambió ≤ umbral de los archivos (nuevos + cambiados + borrados) → relectura, con la lista;
- cambió más → primera-vez.

Solo biblioteca estándar; openpyxl (hojas de .xlsx) y pypdf (título de .pdf) si están.
"""
import argparse
import ast
import datetime as dt
import fnmatch
import hashlib
import json
import os
import posixpath
import re
import shutil
import struct
import sys
import tempfile
import time
import urllib.parse
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve()
SKILL = AQUI.parents[1]
VERSION = 1

EXCLUIR_CARPETAS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".obsidian", ".trash", "graphify-out", ".idea", ".vscode",
}
EXCLUIR_ARCHIVOS = {"thumbs.db", "desktop.ini", ".ds_store"}
EXCLUIR_PREFIJOS = ("~$", ".~lock")

TIPO_POR_EXT = {
    ".md": "markdown", ".markdown": "markdown", ".txt": "texto",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "config", ".ini": "config",
    ".cfg": "config", ".py": "python", ".ps1": "script", ".sh": "script", ".bat": "script",
    ".cmd": "script", ".js": "script", ".ts": "script", ".sql": "script",
    ".html": "web", ".htm": "web", ".css": "web", ".xml": "datos",
    ".csv": "tabla", ".tsv": "tabla", ".xlsx": "excel", ".xlsm": "excel", ".xls": "excel",
    ".docx": "word", ".doc": "word", ".pptx": "presentacion", ".pdf": "pdf",
    ".png": "imagen", ".jpg": "imagen", ".jpeg": "imagen", ".gif": "imagen", ".webp": "imagen",
    ".svg": "imagen", ".bmp": "imagen", ".zip": "comprimido", ".base": "obsidian",
    ".canvas": "obsidian", ".dxf": "cad", ".dwg": "cad", ".step": "cad", ".stp": "cad",
}
EXT_TEXTO = {
    ".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".py", ".ps1",
    ".sh", ".bat", ".cmd", ".js", ".ts", ".sql", ".html", ".htm", ".css", ".xml", ".csv", ".tsv",
    ".base", ".canvas", ".svg",
}
# Archivos en los que se buscan enlaces (los demás solo se resumen).
EXT_CON_ENLACES = EXT_TEXTO - {".csv", ".tsv", ".svg", ".css"}
LIMITE_TEXTO = 2_000_000          # bytes que se leen de un archivo de texto
PALABRAS_RESUMEN = 30             # tope del resumen guardado en el grafo
PALABRAS_MD = 60                  # un .md lleva además sus secciones
DOC = {"markdown", "texto", "word", "pdf", "excel", "presentacion"}
NOMBRES_CLAVE = {"leeme", "readme", "skill", "claude", "indice", "mapa", "arquitectura", "guia",
                 "resultado", "agents", "prd"}

EXT_CITABLES = ("md|markdown|txt|json|ya?ml|toml|py|ps1|sh|bat|js|ts|sql|html?|css|csv|tsv|"
                "xlsx|xlsm|xls|docx|pptx|pdf|png|jpe?g|gif|webp|svg|zip|base|canvas|dxf|dwg|step|stp")
RE_URL = re.compile(r"(?:https?|ftp|mailto):\S+", re.I)
RE_WIKI = re.compile(r"!?\[\[([^\]\|#\n]+)(?:#[^\]\|\n]*)?(?:\|[^\]\n]*)?\]\]")
RE_MDLINK = re.compile(r"!?\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
RE_BACKTICK = re.compile(r"`([^`\n]{1,240})`")
RE_RUTA = re.compile(r"(?<![\w/\\.:])((?:[A-Za-z]:[\\/])?[\w\-.~/\\]*[\w\-]\.(?:" + EXT_CITABLES
                     + r"))(?![\w])", re.I)


class ErrorEntrada(Exception):
    """Error que impide cartografiar. Se corrige la llamada y se vuelve a correr."""


# ------------------------------------------------------------------ utilidades
def _larga(p):
    """Ruta absoluta con prefijo \\\\?\\ en Windows (las de más de 260 caracteres «no existen»)."""
    p = os.path.abspath(p)
    if os.name == "nt" and not p.startswith("\\\\?\\"):
        if p.startswith("\\\\"):
            return "\\\\?\\UNC\\" + p[2:]
        return "\\\\?\\" + p
    return p


def _corta(p):
    if p.startswith("\\\\?\\UNC\\"):
        return "\\\\" + p[8:]
    if p.startswith("\\\\?\\"):
        return p[4:]
    return p


def _posix(p):
    return p.replace("\\", "/")


def _palabras(texto):
    return len(re.findall(r"\S+", texto))


def _recortar(texto, n):
    pal = texto.split()
    if len(pal) <= n:
        return " ".join(pal)
    return " ".join(pal[:n]).rstrip(".,;:") + "…"


def _fecha(ns):
    return dt.datetime.fromtimestamp(ns / 1e9).strftime("%d-%m-%Y")


def _iso(ns):
    return dt.datetime.fromtimestamp(ns / 1e9).isoformat(timespec="seconds")


def _tam(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{round(n / 1024)} KB"
    return f"{n / 1024 / 1024:.1f} MB".replace(".", ",")


def _pct(x):
    return f"{x * 100:.1f} %".replace(".", ",")


def _leer_texto(full, limite=LIMITE_TEXTO):
    with open(full, "rb") as fh:
        datos = fh.read(limite)
    for cod in ("utf-8-sig", "cp1252"):
        try:
            return datos.decode(cod)
        except UnicodeDecodeError:
            continue
    return datos.decode("utf-8", errors="replace")


def _sha1(full):
    h = hashlib.sha1()
    with open(full, "rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()[:12]


def _limpiar_md(s):
    s = re.sub(r"!?\[\[([^\]\|]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"!?\[\[([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"(\*\*|__|~~)(.+?)\1", r"\2", s)
    s = re.sub(r"(?<![\w*])([*_])(?=\S)(.+?)(?<=\S)\1(?![\w*])", r"\2", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _primera_frase(s):
    m = re.search(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡«(\d])", s)
    return s[:m.start()] if m else s


# ------------------------------------------------------------------ frontmatter
def frontmatter(texto):
    """Devuelve (dict, cuerpo). YAML mínimo: escalares, listas [a, b] y listas con guion."""
    if not texto.startswith("---"):
        return {}, texto
    m = re.match(r"---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", texto, re.S)
    if not m:
        return {}, texto
    datos, clave = {}, None
    for linea in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_][\w\-]*):\s*(.*)$", linea)
        if mm:
            clave = mm.group(1)
            datos[clave] = mm.group(2).strip()
            continue
        if clave is None or not linea.strip():
            continue
        s = linea.strip()
        if s.startswith("- "):
            previo = datos.get(clave)
            lista = previo if isinstance(previo, list) else []
            lista.append(s[2:].strip().strip("\"'"))
            datos[clave] = lista
        elif isinstance(datos.get(clave), str) and linea[:1] in " \t":
            datos[clave] = (datos[clave] + " " + s).strip()
    for k, v in list(datos.items()):
        if isinstance(v, str):
            v = re.sub(r"^[>|][+-]?\s*", "", v).strip()
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
            elif len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            datos[k] = v
    return datos, texto[m.end():]


# ------------------------------------------------------------------ resúmenes
RE_CAMPO = re.compile(r"^\|?\s*\*\*([^*|]{1,30}?)\s*:?\s*\*\*\s*:?\s*\|?\s*(.*?)\s*\|?\s*$")
CAMPOS_CLAVE = {"estado", "status", "para qué", "para que", "reemplaza a", "cliente", "cliente / obra"}


def resumen_md(texto):
    """Título · campos de estado · primera frase (o description) · secciones ##."""
    fm, cuerpo = frontmatter(texto)
    titulo, frase, en_codigo = None, None, False
    campos, secciones = [], []
    for linea in cuerpo.splitlines():
        s = linea.strip()
        if s.startswith("```") or s.startswith("~~~"):
            en_codigo = not en_codigo
            continue
        if en_codigo or not s:
            continue
        if s.startswith("#"):
            nivel = len(s) - len(s.lstrip("#"))
            limpio = _limpiar_md(s.lstrip("#").strip())
            if titulo is None:
                titulo = limpio
            elif nivel == 2:
                secciones.append(_recortar(re.sub(r"^[\d.]+\s*[·.\-)]?\s*", "", limpio), 5))
            continue
        m = RE_CAMPO.match(s)
        if m:                                     # metadato «**Clave:** valor» o «| **Clave** | valor |»
            clave = m.group(1).strip().rstrip(":").lower()
            if clave in CAMPOS_CLAVE and m.group(2) and len(campos) < 3:
                campos.append(f"{clave}: {_recortar(_limpiar_md(m.group(2)), 8)}")
            continue
        if frase is not None:
            continue
        if s.startswith(("|", "<!--", "---", "***", "![", "<")) or re.match(r"^[-=]{3,}$", s):
            continue
        s = re.sub(r"^(>\s*)+", "", s)
        s = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)
        s = _limpiar_md(s)
        if len(s) >= 3 and not re.match(r"^[\wÁÉÍÓÚÑáéíóúñ /]{1,25}:\s", s):
            frase = _recortar(_primera_frase(s), 25)
    titulo = titulo or (fm.get("title") or fm.get("titulo") or fm.get("name") or None)
    desc = fm.get("description") or fm.get("descripcion") or fm.get("resumen")
    cuerpo_res = _recortar(desc, 25) if isinstance(desc, str) and desc else frase
    partes = [p for p in [titulo] + campos + [cuerpo_res] if p]
    if len(secciones) >= 2:
        partes.append("secciones: " + "; ".join(secciones[:6]) + (" …" if len(secciones) > 6 else ""))
    return _recortar(" · ".join(partes), PALABRAS_MD), fm


def resumen_json(texto):
    try:
        obj = json.loads(texto)
    except (ValueError, RecursionError):
        return "JSON que no se pudo leer"
    if isinstance(obj, dict):
        claves = list(obj.keys())
        extra = f" (+{len(claves) - 8})" if len(claves) > 8 else ""
        return "claves: " + ", ".join(map(str, claves[:8])) + extra
    if isinstance(obj, list):
        s = f"lista de {len(obj)} elementos"
        if obj and isinstance(obj[0], dict):
            s += "; claves: " + ", ".join(map(str, list(obj[0].keys())[:6]))
        return s
    return f"valor {type(obj).__name__}"


def resumen_yaml(texto):
    claves = re.findall(r"^([A-Za-z_][\w\-]*)\s*:", texto, re.M)
    if not claves:
        return ""
    extra = f" (+{len(claves) - 8})" if len(claves) > 8 else ""
    return "claves: " + ", ".join(claves[:8]) + extra


def resumen_py(texto):
    try:
        doc = ast.get_docstring(ast.parse(texto))
    except (SyntaxError, ValueError, RecursionError):
        doc = None
    if doc:
        for linea in doc.strip().splitlines():
            if linea.strip():
                return linea.strip()
    return resumen_comentario(texto)


def resumen_comentario(texto):
    for linea in texto.splitlines()[:40]:
        s = linea.strip()
        if s.startswith("#!") or "coding" in s[:20]:
            continue
        m = re.match(r"^(?:#|//|REM\s|::|<#|--)\s*(.+)$", s, re.I)
        if m and len(m.group(1).strip("#=-* ")) >= 3:
            return m.group(1).strip("#=-* ")
    return ""


def resumen_texto(texto):
    for linea in texto.splitlines():
        if linea.strip():
            return _recortar(linea.strip(), PALABRAS_RESUMEN)
    return ""


def resumen_csv(texto):
    lineas = [x for x in texto.splitlines() if x.strip()]
    if not lineas:
        return ""
    return f"{len(lineas) - 1} filas; columnas: " + _recortar(lineas[0], 12)


def resumen_html(texto):
    m = re.search(r"<title[^>]*>(.*?)</title>", texto, re.I | re.S)
    return _limpiar_md(m.group(1)) if m else ""


def resumen_xlsx(full):
    try:
        import openpyxl  # noqa: PLC0415
    except ImportError:
        return "", "openpyxl no está: solo el nombre"
    try:
        wb = openpyxl.load_workbook(full, read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001
        return f"Excel que no se pudo abrir ({type(e).__name__})", None
    try:
        hojas = []
        a1 = None
        for i, ws in enumerate(wb.worksheets):
            dim = f" ({ws.max_row}×{ws.max_column})" if ws.max_row and ws.max_column else ""
            hojas.append(f"{ws.title}{dim}")
            if i == 0:
                try:
                    fila = next(ws.iter_rows(min_row=1, max_row=1, max_col=3, values_only=True), ())
                    a1 = next((str(v) for v in fila if isinstance(v, str) and v.strip()), None)
                except Exception:  # noqa: BLE001
                    a1 = None
        s = "hojas: " + ", ".join(hojas[:8]) + (f" (+{len(hojas) - 8})" if len(hojas) > 8 else "")
        if a1:
            s += f"; primera fila «{_recortar(a1, 8)}»"
        return s, None
    finally:
        wb.close()


def resumen_docx(full):
    try:
        with zipfile.ZipFile(full) as z:
            titulo = None
            if "docProps/core.xml" in z.namelist():
                core = z.read("docProps/core.xml").decode("utf-8", "replace")
                m = re.search(r"<dc:title>([^<]+)</dc:title>", core)
                titulo = m.group(1).strip() if m else None
            parrafo = None
            if "word/document.xml" in z.namelist():
                with z.open("word/document.xml") as fh:
                    xml = fh.read(2_000_000).decode("utf-8", "replace")
                for p in re.finditer(r"<w:p[ >].*?</w:p>", xml, re.S):
                    t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p.group(0))).strip()
                    if len(t) >= 3:
                        parrafo = t
                        break
        partes = list(dict.fromkeys(x for x in (titulo, parrafo) if x))
        return _recortar(" · ".join(partes), PALABRAS_RESUMEN)
    except (zipfile.BadZipFile, OSError, KeyError):
        return ""


def resumen_pdf(full):
    try:
        import logging  # noqa: PLC0415
        import pypdf  # noqa: PLC0415
        logging.getLogger("pypdf").setLevel(logging.ERROR)
    except ImportError:
        return "", "pypdf no está: solo el nombre"
    try:
        r = pypdf.PdfReader(full)
        n = len(r.pages)
        titulo = None
        try:
            meta = r.metadata
            titulo = (meta.title or "").strip() if meta else None
        except Exception:  # noqa: BLE001
            titulo = None
        if not titulo and n:
            try:
                texto = r.pages[0].extract_text() or ""
                for linea in texto.splitlines():
                    if len(linea.strip()) >= 4:
                        titulo = "1.ª línea: «" + _recortar(linea.strip(), 14) + "»"
                        break
            except Exception:  # noqa: BLE001
                pass
        pags = f"{n} pág."
        return (f"{titulo} · {pags}" if titulo else pags), None
    except Exception as e:  # noqa: BLE001
        return f"PDF que no se pudo leer ({type(e).__name__})", None


def resumen_imagen(full, ext):
    try:
        with open(full, "rb") as fh:
            cab = fh.read(65536)
        w = h = None
        if ext == ".png" and cab[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", cab[16:24])
        elif ext == ".gif" and cab[:4] == b"GIF8":
            w, h = struct.unpack("<HH", cab[6:10])
        elif ext in (".jpg", ".jpeg") and cab[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(cab):
                if cab[i] != 0xFF:
                    i += 1
                    continue
                marca = cab[i + 1]
                largo = struct.unpack(">H", cab[i + 2:i + 4])[0]
                if marca in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", cab[i + 5:i + 9])
                    break
                i += 2 + largo
        return f"imagen {w}×{h}" if w and h else "imagen"
    except (OSError, struct.error):
        return "imagen"


def resumen_zip(full):
    try:
        with zipfile.ZipFile(full) as z:
            return f"comprimido con {len(z.namelist())} archivos"
    except (zipfile.BadZipFile, OSError):
        return "comprimido"


def resumir(full, ext, texto):
    """(resumen, frontmatter, aviso). Nunca llama a un modelo."""
    fm, aviso = {}, None
    if ext in (".md", ".markdown"):
        res, fm = resumen_md(texto)
    elif ext in (".json", ".canvas"):
        res = resumen_json(texto)
    elif ext in (".yaml", ".yml", ".toml", ".base"):
        res = resumen_yaml(texto)
    elif ext == ".py":
        res = resumen_py(texto)
    elif ext in (".ps1", ".sh", ".bat", ".cmd", ".js", ".ts", ".sql", ".ini", ".cfg"):
        res = resumen_comentario(texto)
    elif ext in (".html", ".htm"):
        res = resumen_html(texto)
    elif ext in (".csv", ".tsv"):
        res = resumen_csv(texto)
    elif ext == ".txt":
        res = resumen_texto(texto)
    elif ext in (".xlsx", ".xlsm"):
        res, aviso = resumen_xlsx(full)
    elif ext == ".docx":
        res = resumen_docx(full)
    elif ext == ".pdf":
        res, aviso = resumen_pdf(full)
    elif ext in (".png", ".jpg", ".jpeg", ".gif"):
        res = resumen_imagen(full, ext)
    elif ext == ".zip":
        res = resumen_zip(full)
    else:
        res = ""
    tope = PALABRAS_MD if ext in (".md", ".markdown") else PALABRAS_RESUMEN
    return _recortar(res or "", tope), fm, aviso


# ------------------------------------------------------------------ recorrido
def _coincide(nombre, rel, patrones):
    return any(fnmatch.fnmatch(nombre, p) or fnmatch.fnmatch(rel, p) for p in patrones)


def _es_enlace(full):
    try:
        if os.path.islink(full):
            return True
        isj = getattr(os.path, "isjunction", None)
        return bool(isj and isj(full))
    except OSError:
        return False


def recorrer(raiz, patrones, salida_larga, max_bytes, excl):
    base = _larga(raiz)
    for dirpath, dirnames, filenames in os.walk(base):
        rel_dir = _posix(dirpath[len(base):].lstrip("\\/"))
        quedan = []
        for d in sorted(dirnames):
            full = os.path.join(dirpath, d)
            rel = posixpath.join(rel_dir, d) if rel_dir else d
            if os.path.normcase(full) == os.path.normcase(salida_larga):
                excl["salida"].append(rel)
            elif d in EXCLUIR_CARPETAS:
                excl["carpetas"].append(rel)
            elif _coincide(d, rel, patrones):
                excl["patron"].append(rel + "/")
            elif _es_enlace(full):
                excl["enlaces"].append(rel)
            else:
                quedan.append(d)
        dirnames[:] = quedan
        for f in sorted(filenames):
            full = os.path.join(dirpath, f)
            rel = posixpath.join(rel_dir, f) if rel_dir else f
            if f.lower() in EXCLUIR_ARCHIVOS or f.startswith(EXCLUIR_PREFIJOS):
                excl["sistema"].append(rel)
                continue
            if _coincide(f, rel, patrones):
                excl["patron"].append(rel)
                continue
            try:
                st = os.stat(full)
            except OSError:
                excl["ilegibles"].append(rel)
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext not in EXT_TEXTO and st.st_size > max_bytes:
                excl["binarios"].append(rel)
                continue
            yield rel, full, st, ext


def _prefijos(raices):
    if len(raices) == 1:
        return [""]
    vistos, salida = Counter(), []
    for r in raices:
        b = os.path.basename(r.rstrip("\\/")) or "raiz"
        vistos[b] += 1
        salida.append(f"{b}~{vistos[b]}/" if vistos[b] > 1 else f"{b}/")
    return salida


# ------------------------------------------------------------------ enlaces
class Resolutor:
    def __init__(self, ids, raices, prefijos):
        self.ids = set(ids)
        self.minus = {i.lower(): i for i in ids}
        self.por_nombre = defaultdict(list)
        self.por_stem = defaultdict(list)
        for i in ids:
            nombre = posixpath.basename(i).lower()
            self.por_nombre[nombre].append(i)
            self.por_stem[os.path.splitext(nombre)[0]].append(i)
        self.raices = [(_posix(r).rstrip("/").lower(), p) for r, p in zip(raices, prefijos)]

    def _exacto(self, c):
        if c in self.ids:
            return c
        return self.minus.get(c.lower())

    def resolver(self, cand, origen, prefijo, wiki=False):
        c = urllib.parse.unquote(cand.strip().strip("\"'<>()[]")).replace("\\", "/")
        c = c.split("#")[0].split("?")[0].strip()
        if not c or c.endswith("/"):
            return None
        if re.match(r"^[A-Za-z]:/", c) or c.startswith("/"):
            cl = c.lower()
            for raiz, pref in self.raices:
                if cl.startswith(raiz + "/"):
                    return self._exacto(posixpath.normpath(pref + c[len(raiz) + 1:]))
            return None
        c = re.sub(r"^(\./)+", "", c)
        base = posixpath.dirname(origen)
        intentos = [posixpath.normpath(posixpath.join(base, c)),
                    posixpath.normpath(posixpath.join(prefijo, c)) if prefijo else posixpath.normpath(c)]
        for t in intentos:
            for v in (t, t + ".md"):
                hit = self._exacto(v)
                if hit:
                    return hit
        nombre = posixpath.basename(c).lower()
        if "/" not in c:
            lista = self.por_nombre.get(nombre) or (self.por_stem.get(nombre) if wiki else None) or []
            if not lista and wiki:
                lista = self.por_nombre.get(nombre + ".md", [])
            return lista[0] if len(lista) == 1 else None
        # ruta parcial citada desde otra raíz: sufijo único
        cand_ids = self.por_nombre.get(nombre) or (self.por_nombre.get(nombre + ".md", []) if wiki else [])
        sufijo = "/" + c.lower().lstrip("/")
        hits = [i for i in cand_ids if ("/" + i.lower()).endswith(sufijo)
                or ("/" + i.lower()).endswith(sufijo + ".md")]
        return hits[0] if len(hits) == 1 else None


def extraer_enlaces(texto, fm, origen, prefijo, res):
    """Lista de (destino, relación, confianza). Destino = id de archivo o «skill:<nombre>»."""
    salida = []
    skills = []
    for k in ("skills", "skill"):
        v = fm.get(k)
        if isinstance(v, str) and v:
            skills += [x.strip() for x in v.split(",") if x.strip()]
        elif isinstance(v, list):
            skills += [str(x) for x in v if str(x).strip()]
    for s in skills:
        destino = res.resolver(f"skills/{s}/SKILL.md", origen, prefijo)
        salida.append((destino or f"skill:{s}", "usa_skill", "EXTRACTED"))
    sin_url = RE_URL.sub(" ", texto)
    for m in RE_WIKI.finditer(sin_url):
        d = res.resolver(m.group(1), origen, prefijo, wiki=True)
        if d:
            salida.append((d, "wikilink", "EXTRACTED"))
    for m in RE_MDLINK.finditer(sin_url):
        d = res.resolver(m.group(1), origen, prefijo)
        if d:
            salida.append((d, "enlace", "EXTRACTED"))
    candidatos = [m.group(1) for m in RE_BACKTICK.finditer(sin_url)]
    candidatos += [m.group(1) for m in RE_RUTA.finditer(sin_url)]
    for c in candidatos:
        if "." not in c:
            continue
        d = res.resolver(c, origen, prefijo)
        if d:
            salida.append((d, "cita", "INFERRED"))
    return salida


# ------------------------------------------------------------------ huellas y modo
def leer_json(ruta):
    try:
        with open(_larga(ruta), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def delta(prev, actuales):
    """Cambios de esta corrida contra la anterior: (nuevos, cambiados, borrados)."""
    nuevos = sorted(i for i in actuales if i not in prev)
    borrados = sorted(i for i in prev if i not in actuales)
    cambiados = sorted(i for i in actuales if i in prev and (
        actuales[i]["sha1"] != prev[i].get("sha1") or actuales[i]["tam"] != prev[i].get("tam")))
    return nuevos, cambiados, borrados


def neto(corridas):
    """Estado acumulado de cada archivo a lo largo de las corridas no leídas.

    nuevo → cambiado sigue nuevo; nuevo → borrado desaparece (nunca estuvo en la base);
    borrado → nuevo es cambiado."""
    estado = {}
    for c in corridas:
        for i in c.get("nuevos", []):
            estado[i] = "cambiado" if estado.get(i) == "borrado" else "nuevo"
        for i in c.get("cambiados", []):
            estado[i] = "nuevo" if estado.get(i) == "nuevo" else "cambiado"
        for i in c.get("borrados", []):
            if estado.get(i) == "nuevo":
                estado.pop(i)
            else:
                estado[i] = "borrado"
    return sorted(estado.items())


def cambios_vacio(base=None):
    return {"version": VERSION, "leido_el": None, "base": base, "primera_vez_pendiente": False,
            "primera_vez_desde": None, "corridas": []}


def decidir_modo(previo, cambios, actuales, raices, hay_mapa, umbral, ahora):
    """Decide el modo contra lo acumulado NO leído (cambios.json).

    Devuelve (modo, motivo, delta_corrida, acumulado, ratio, cambios actualizado)."""
    sin_delta = ([], [], [])
    if not previo or "archivos" not in previo:
        c = cambios_vacio()
        c.update(primera_vez_pendiente=True, primera_vez_desde=ahora)
        return "primera-vez", "no hay huellas.json previo", sin_delta, [], 1.0, c
    prev = previo["archivos"]
    if [r.lower() for r in previo.get("raices", [])] != [r.lower() for r in raices]:
        c = cambios_vacio()
        c.update(primera_vez_pendiente=True, primera_vez_desde=ahora)
        return "primera-vez", "cambiaron las carpetas cartografiadas", sin_delta, [], 1.0, c
    c = cambios if isinstance(cambios, dict) and "corridas" in cambios else cambios_vacio(len(prev))
    if c.get("base") is None:
        c["base"] = len(prev)
    d = delta(prev, actuales)
    if any(d):
        c["corridas"].append({"fecha": ahora, "nuevos": d[0], "cambiados": d[1], "borrados": d[2]})
    acumulado = neto(c["corridas"])
    ratio = len(acumulado) / max(c["base"], 1)
    if not hay_mapa:
        c.update(primera_vez_pendiente=True, primera_vez_desde=c.get("primera_vez_desde") or ahora)
        return "primera-vez", "hay huellas pero falta MAPA.md", d, acumulado, ratio, c
    if c.get("primera_vez_pendiente"):
        motivo = (f"la primera vez del {c.get('primera_vez_desde') or '?'} no se ha marcado leída "
                  "(`--marcar-leido` al consolidar)")
        return "primera-vez", motivo, d, acumulado, ratio, c
    desde = f" desde el {c['leido_el']}" if c.get("leido_el") else ""
    if ratio <= umbral:
        motivo = (f"{len(acumulado)} de {c['base']} archivos cambiaron{desde} sin leerse "
                  f"({_pct(ratio)}, umbral {_pct(umbral)})" + ("" if acumulado else "; basta este mapa"))
        return "relectura", motivo, d, acumulado, ratio, c
    c.update(primera_vez_pendiente=True, primera_vez_desde=ahora)
    motivo = (f"{len(acumulado)} de {c['base']} archivos cambiaron{desde} sin leerse "
              f"({_pct(ratio)}, sobre el umbral {_pct(umbral)})")
    return "primera-vez", motivo, d, acumulado, ratio, c


def marcar_leido(salida):
    """Vacía lo acumulado: lo llama orquestar al consolidar. La base pasa a ser la última corrida."""
    salida = _corta(os.path.abspath(salida))
    huellas = leer_json(os.path.join(salida, "huellas.json"))
    if not isinstance(huellas, dict) or "archivos" not in huellas:
        raise ErrorEntrada(f"No hay huellas.json en {salida}: primero hay que cartografiar")
    c = cambios_vacio(len(huellas["archivos"]))
    c["leido_el"] = dt.datetime.now().strftime("%d-%m-%Y %H:%M")
    with open(os.path.join(_larga(salida), "cambios.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(c, fh, ensure_ascii=False, indent=1)
    return c


# ------------------------------------------------------------------ núcleo
NUCLEO_NOMBRES = ["leeme", "readme", "trabajo", "claude", "indice"]
NUCLEO_FUERA = {"imagen", "comprimido", "cad"}
NUCLEO_MAX = 3


def elegir_nucleo(archivos, entrantes, fijos=()):
    """Hasta 3 archivos que se leen siempre. Regla determinista:
    1) los fijados con --nucleo; 2) nombres clave (LEEME, README, TRABAJO, CLAUDE, INDICE), primero
    el menos profundo; 3) los más enlazados (sin imágenes ni comprimidos); empate: el más reciente."""
    def stem(i):
        return os.path.splitext(posixpath.basename(i))[0].lower()

    elegidos = []
    for f in fijos:
        elegidos.append((f, "fijado a mano"))
    usados = {i for i, _ in elegidos}
    por_nombre = sorted((i for i in archivos if stem(i) in NUCLEO_NOMBRES and i not in usados),
                        key=lambda i: (i.count("/"), NUCLEO_NOMBRES.index(stem(i)), -entrantes[i],
                                       -archivos[i]["mtime_ns"], i))
    for i in por_nombre:
        if len(elegidos) >= NUCLEO_MAX:
            break
        elegidos.append((i, "nombre clave"))
        usados.add(i)
    resto = sorted((i for i in archivos if i not in usados and archivos[i]["tipo"] not in NUCLEO_FUERA),
                   key=lambda i: (-entrantes[i], -archivos[i]["mtime_ns"], i))
    for i in resto:
        if len(elegidos) >= NUCLEO_MAX:
            break
        n = entrantes[i]
        elegidos.append((i, f"{n} enlace{'s' if n != 1 else ''} entrante{'s' if n != 1 else ''}"
                         if n else "el más reciente"))
    return elegidos[:NUCLEO_MAX]


def _validar_fijos(fijos, archivos):
    minus = {i.lower(): i for i in archivos}
    salida = []
    for f in fijos:
        c = re.sub(r"^(\./)+", "", _posix(f.strip()))
        if not c:
            continue
        hit = minus.get(c.lower())
        if not hit:
            raise ErrorEntrada(f"--nucleo: «{f}» no está en el mapa (se escribe como ruta relativa del mapa)")
        if hit not in salida:
            salida.append(hit)
    if len(salida) > NUCLEO_MAX:
        raise ErrorEntrada(f"--nucleo: a lo más {NUCLEO_MAX} archivos")
    return salida


# ------------------------------------------------------------------ MAPA.md
NIVELES = [
    dict(res=60, k=None, tam=True, cap=25, prof=2),
    dict(res=30, k=None, tam=True, cap=25, prof=2),
    dict(res=14, k=None, tam=False, cap=15, prof=2),
    dict(res=12, k=10, tam=False, cap=10, prof=2),
    dict(res=10, k=6, tam=False, cap=10, prof=2),
    dict(res=10, k=4, tam=False, cap=8, prof=1),
    dict(res=8, k=2, tam=False, cap=8, prof=1),
    dict(res=8, k=1, tam=False, cap=6, prof=1),
    dict(res=8, k=0, tam=False, cap=6, prof=1),
    dict(res=6, k=0, tam=False, cap=4, prof=0),
]


def _carpeta(i):
    d = posixpath.dirname(i)
    return d + "/" if d else "./"


def _resumen_tipos(lista, n=4):
    c = Counter(x["tipo"] for x in lista)
    return ", ".join(f"{v} {k}" for k, v in c.most_common(n)) + (" …" if len(c) > n else "")


def render_mapa(ctx, nv):
    nodos = ctx["nodos"]
    L = []
    a = L.append
    a("# Mapa de contexto")
    a("")
    a(f"**MODO: {ctx['modo']}** · {ctx['motivo']}")
    a("")
    a(f"Generado el {ctx['generado']} por `mapa_contexto.py` (sin LLM). Raíces: "
      + " · ".join(f"`{r}`" for r in ctx["raices"]))
    a(f"{len(nodos)} archivos · {_tam(ctx['bytes'])} · del {ctx['desde']} al {ctx['hasta']} · "
      f"{ctx['n_aristas']} enlaces entre archivos")
    a("Por tipo: " + _resumen_tipos(nodos.values(), 12))
    if ctx["excluido"]:
        a("Excluido: " + ctx["excluido"])
    a("")
    a("## Núcleo · leer siempre")
    a("")
    a("Relectura = estos archivos + los de «A releer» + este mapa.")
    for i, motivo in ctx["nucleo"]:
        r = _recortar(nodos[i]["resumen"], min(nv["res"], 30)) if i in nodos else ""
        a(f"- `{i}` ({motivo})" + (f" · {r}" if r else ""))
    a("")
    if ctx["releer"] or ctx["borrados"]:
        a("## A releer")
        a("")
        if ctx["releer_desde"]:
            a(f"Cambios acumulados sin leer desde el {ctx['releer_desde']}.")
        lim = nv["cap"] * 2
        for i, estado in ctx["releer"][:lim]:
            r = _recortar(nodos[i]["resumen"], nv["res"]) if i in nodos else ""
            a(f"- `{i}` ({estado})" + (f" · {r}" if r else ""))
        for i in ctx["borrados"][:lim]:
            a(f"- `{i}` (borrado)")
        resto = max(len(ctx["releer"]) - lim, 0) + max(len(ctx["borrados"]) - lim, 0)
        if resto:
            a(f"- +{resto} más: la lista completa está en `grafo.json` (graph.cambios)")
        a("")

    # Carpetas, agregadas a la profundidad del nivel
    a("## Carpetas")
    a("")
    grupos = defaultdict(list)
    for n in nodos.values():
        partes = posixpath.dirname(n["id"]).split("/") if posixpath.dirname(n["id"]) else []
        clave = "/".join(partes[:nv["prof"]]) + "/" if partes and nv["prof"] else "./"
        if nv["prof"] == 0:
            clave = "./"
        grupos[clave].append(n)
    for c in sorted(grupos):
        g = grupos[c]
        ult = max(x["mtime_ns"] for x in g)
        a(f"- `{c}` · {len(g)} archivo{'s' if len(g) != 1 else ''} ({_resumen_tipos(g)}) · "
          f"último {_fecha(ult)}")
    a("")

    puntaje = ctx["puntaje"]
    if nv["k"] != 0:
        a("## Archivos")
        a("")
        por_carpeta = defaultdict(list)
        for n in nodos.values():
            por_carpeta[_carpeta(n["id"])].append(n)
        for c in sorted(por_carpeta):
            g = por_carpeta[c]
            a(f"### `{c}`")
            if nv["k"] is None or len(g) <= nv["k"]:
                elegidos, resto = g, []
            else:
                orden = sorted(g, key=lambda x: (-puntaje[x["id"]], x["id"]))
                elegidos, resto = orden[:nv["k"]], orden[nv["k"]:]
            for n in sorted(elegidos, key=lambda x: x["id"].lower()):
                partes = [f"`{posixpath.basename(n['id'])}`"]
                if nv["tam"]:
                    partes.append(_tam(n["tam"]))
                partes.append(_fecha(n["mtime_ns"]))
                r = _recortar(n["resumen"], nv["res"])
                if r:
                    partes.append(r)
                a("- " + " · ".join(partes))
            if resto:
                a(f"- +{len(resto)} más ({_resumen_tipos(resto)})")
            a("")
    else:
        a("## Archivos clave")
        a("")
        top = sorted(nodos.values(), key=lambda x: (-puntaje[x["id"]], x["id"]))[:nv["cap"] * 3]
        for n in top:
            r = _recortar(n["resumen"], nv["res"])
            a(f"- `{n['id']}` · {_fecha(n['mtime_ns'])}" + (f" · {r}" if r else ""))
        a(f"- (los otros {max(len(nodos) - len(top), 0)} están en `grafo.json`)")
        a("")

    a("## Lo más reciente")
    a("")
    for n in sorted(nodos.values(), key=lambda x: (-x["mtime_ns"], x["id"]))[:nv["cap"] // 2 or 1]:
        hora = dt.datetime.fromtimestamp(n["mtime_ns"] / 1e9).strftime("%H:%M")
        a(f"- {_fecha(n['mtime_ns'])} {hora} · `{n['id']}`")
    a("")

    a("## Más enlazados")
    a("")
    entrantes = ctx["entrantes"]
    top = sorted((i for i in entrantes if entrantes[i]), key=lambda i: (-entrantes[i], i))[:nv["cap"] // 2 or 1]
    if top:
        for i in top:
            a(f"- `{i}` ← {entrantes[i]}")
    else:
        a("- ninguno: los archivos no se citan entre sí")
    a("")

    huerf = ctx["huerfanos"]
    a(f"## Huérfanos ({len(huerf)})")
    a("")
    a("Nadie los enlaza ni enlazan a nadie.")
    for i in huerf[:nv["cap"]]:
        a(f"- `{i}`")
    if len(huerf) > nv["cap"]:
        a(f"- +{len(huerf) - nv['cap']} más")
    a("")

    sin = ctx["sin_resumen"]
    a(f"## Sin resumen ({len(sin)})")
    a("")
    if sin:
        a("El script no pudo resumirlos; los primeros son los que más pesan en el grafo.")
        for i in sin[:min(nv["cap"], 10)]:
            a(f"- `{i}`")
        if len(sin) > min(nv["cap"], 10):
            a(f"- +{len(sin) - min(nv['cap'], 10)} más")
    else:
        a("Todos tienen resumen.")
    a("")
    for nota in ctx["notas"]:
        a(nota)
        a("")
    return "\n".join(L).rstrip() + "\n"


def armar_mapa(ctx, max_palabras):
    texto = ""
    for nv in NIVELES:
        texto = render_mapa(ctx, nv)
        if _palabras(texto) <= max_palabras:
            return texto, nv
    # Último recurso: cortar por líneas hasta caber.
    lineas, cuenta, salida = texto.splitlines(), 0, []
    for ln in lineas:
        p = _palabras(ln)
        if cuenta + p > max_palabras - 20:
            break
        salida.append(ln)
        cuenta += p
    salida.append("")
    salida.append("(Mapa truncado para caber en el tope de palabras; el detalle completo está en `grafo.json`.)")
    return "\n".join(salida) + "\n", NIVELES[-1]


# ------------------------------------------------------------------ principal
def cartografiar(carpetas, salida, excluir=(), umbral=0.20, max_palabras=3000, max_mb=25.0,
                 graphify=False, nucleo=()):
    t0 = time.perf_counter()
    ahora = dt.datetime.now().strftime("%d-%m-%Y %H:%M")
    raices = []
    for c in carpetas:
        p = _corta(os.path.abspath(c))
        if not os.path.isdir(_larga(p)):
            raise ErrorEntrada(f"No existe la carpeta: {c}")
        raices.append(p)
    prefijos = _prefijos(raices)
    salida = _corta(os.path.abspath(salida))
    salida_larga = _larga(salida)
    excl = defaultdict(list)
    archivos = {}
    for raiz, pref in zip(raices, prefijos):
        for rel, full, st, ext in recorrer(raiz, list(excluir), salida_larga, max_mb * 1024 * 1024, excl):
            i = pref + rel
            archivos[i] = {"id": i, "full": full, "pref": pref, "ext": ext, "tam": st.st_size,
                           "mtime_ns": st.st_mtime_ns,
                           "tipo": TIPO_POR_EXT.get(ext, ext.lstrip(".") or "sin-extension")}

    ruta_h = os.path.join(salida, "huellas.json")
    previo = leer_json(ruta_h)
    prev_arch = (previo or {}).get("archivos", {}) if isinstance(previo, dict) else {}
    misma_version = isinstance(previo, dict) and previo.get("version") == VERSION
    avisos = set()

    # Huella: se reutiliza el sha1 si tamaño y fecha no cambiaron (no se vuelve a leer el archivo).
    for i, x in archivos.items():
        p = prev_arch.get(i)
        if p and p.get("tam") == x["tam"] and p.get("mtime_ns") == x["mtime_ns"] and p.get("sha1"):
            x["sha1"] = p["sha1"]
            x["reusa"] = misma_version and "resumen" in p
            x["resumen_prev"] = p.get("resumen", "")
        else:
            try:
                x["sha1"] = _sha1(x["full"])
            except OSError:
                x["sha1"] = "ilegible"
            x["reusa"] = False

    fijos = _validar_fijos(nucleo, archivos)
    modo, motivo, d_corrida, acumulado, ratio, cambios = decidir_modo(
        previo if isinstance(previo, dict) else None,
        leer_json(os.path.join(salida, "cambios.json")), archivos, raices,
        os.path.exists(os.path.join(salida_larga, "MAPA.md")), umbral, ahora)
    nuevos = [i for i, e in acumulado if e == "nuevo"]
    cambiados = [i for i, e in acumulado if e == "cambiado"]
    borrados = [i for i, e in acumulado if e == "borrado"]

    res = Resolutor(list(archivos), raices, prefijos)
    aristas = {}
    for i, x in archivos.items():
        texto, fm = "", {}
        if x["ext"] in EXT_TEXTO:
            try:
                texto = _leer_texto(x["full"])
            except OSError:
                texto = ""
        if x["reusa"] and x["ext"] not in EXT_TEXTO:
            resumen, aviso = x["resumen_prev"], None
        else:
            try:
                resumen, fm, aviso = resumir(x["full"], x["ext"], texto)
            except Exception as e:  # noqa: BLE001  (un archivo raro no detiene el mapa)
                resumen, fm, aviso = "", {}, f"{type(e).__name__} al resumir"
        if x["ext"] in (".md", ".markdown") and not fm:
            fm = frontmatter(texto)[0]
        if aviso:
            avisos.add(aviso)
        x["resumen"] = resumen
        if x["ext"] in EXT_CON_ENLACES and texto:
            for destino, rel, conf in extraer_enlaces(texto, fm, i, x["pref"], res):
                if destino == i:
                    continue
                clave = (i, destino)
                orden = {"usa_skill": 0, "wikilink": 1, "enlace": 2, "cita": 3}
                if clave not in aristas or orden[rel] < orden[aristas[clave][0]]:
                    aristas[clave] = (rel, conf)

    # Grados y puntaje de relevancia
    entrantes, salientes = Counter(), Counter()
    for (s, t) in aristas:
        salientes[s] += 1
        entrantes[t] += 1
    mt_max = max((x["mtime_ns"] for x in archivos.values()), default=0)
    puntaje = {}
    for i, x in archivos.items():
        stem = os.path.splitext(posixpath.basename(i))[0].lower()
        p = entrantes[i] * 3 + salientes[i]
        p += 2 if x["tipo"] in DOC else 0
        p += 3 if stem in NOMBRES_CLAVE or stem.startswith(tuple(NOMBRES_CLAVE)) else 0
        p += 1 if mt_max - x["mtime_ns"] < 30 * 86400 * 10**9 else 0
        puntaje[i] = p
    huerfanos = sorted(i for i in archivos if not entrantes[i] and not salientes[i])
    sin_resumen = sorted((i for i, x in archivos.items() if not x["resumen"]),
                         key=lambda i: (-puntaje[i], i))

    releer = [(i, e) for i, e in acumulado if e != "borrado"]
    if modo == "primera-vez":
        releer_mapa, borr_mapa = [], []
    else:
        releer_mapa, borr_mapa = releer, borrados
    nucleo_sel = elegir_nucleo(archivos, entrantes, fijos)

    # Exclusiones legibles
    partes = []
    if excl["salida"]:
        partes.append("la carpeta de salida")
    if excl["carpetas"]:
        nombres = sorted({posixpath.basename(x) for x in excl["carpetas"]})
        partes.append(f"{len(excl['carpetas'])} carpetas de sistema ({', '.join(nombres[:5])})")
    if excl["enlaces"]:
        partes.append(f"{len(excl['enlaces'])} enlaces o junctions (no se siguen)")
    if excl["binarios"]:
        partes.append(f"{len(excl['binarios'])} binarios sobre {max_mb:g} MB")
    if excl["patron"]:
        partes.append(f"{len(excl['patron'])} por --excluir")
    if excl["ilegibles"]:
        partes.append(f"{len(excl['ilegibles'])} ilegibles")

    notas = []
    if avisos:
        notas.append("Avisos: " + "; ".join(sorted(avisos)) + ".")
    graphify_ruta = shutil.which("graphify") if graphify else None
    if graphify:
        if graphify_ruta:
            notas.append(
                "## Enriquecer con graphify\n\n"
                "graphify está instalado. Este mapa no lo llama (graphify extrae conceptos con un "
                "modelo y eso cuesta). Si el encargo lo justifica, en Claude Code: `/graphify <carpeta>`; "
                "deja `graphify-out/graph.json`, con la misma forma que `grafo.json` (nodes, links), y "
                "`graphify merge-graphs` los junta.")
        else:
            notas.append("graphify no está instalado: el mapa queda solo con lo estructural.")

    nodos = {}
    for i, x in archivos.items():
        nodos[i] = {"id": i, "label": posixpath.basename(i), "type": "archivo", "tipo": x["tipo"],
                    "file_type": x["tipo"], "source_file": i, "carpeta": _carpeta(i),
                    "tam": x["tam"], "mtime_ns": x["mtime_ns"], "fecha": _iso(x["mtime_ns"]),
                    "resumen": x["resumen"], "entrantes": entrantes[i], "salientes": salientes[i]}
    generado = ahora
    ctx = {
        "nucleo": nucleo_sel,
        "releer_desde": cambios["corridas"][0]["fecha"] if cambios.get("corridas") else None,
        "modo": modo, "motivo": motivo, "generado": generado, "raices": raices, "nodos": nodos,
        "bytes": sum(x["tam"] for x in archivos.values()),
        "desde": _fecha(min((x["mtime_ns"] for x in archivos.values()), default=0)),
        "hasta": _fecha(mt_max), "n_aristas": len(aristas), "excluido": " · ".join(partes),
        "releer": releer_mapa, "borrados": borr_mapa, "puntaje": puntaje, "entrantes": entrantes,
        "huerfanos": huerfanos, "sin_resumen": sin_resumen, "notas": notas,
    }
    mapa, nivel = armar_mapa(ctx, max_palabras)
    palabras = _palabras(mapa)

    # grafo.json
    externos = sorted({t for (_, t) in aristas if t not in nodos})
    grafo = {
        "directed": True, "multigraph": False,
        "graph": {"herramienta": "mapa_contexto", "version": VERSION, "generado": generado,
                  "raices": raices, "modo": modo, "motivo": motivo,
                  "nucleo": [i for i, _ in nucleo_sel],
                  "cambios": {"nuevos": nuevos, "cambiados": cambiados, "borrados": borrados},
                  "cambios_esta_corrida": {"nuevos": d_corrida[0], "cambiados": d_corrida[1],
                                           "borrados": d_corrida[2]}},
        "nodes": [{k: v for k, v in n.items() if k != "mtime_ns"} for n in
                  sorted(nodos.values(), key=lambda n: n["id"])]
        + [{"id": e, "label": e.split(":", 1)[1], "type": "skill", "file_type": "skill",
            "externo": True} for e in externos],
        "links": [{"source": s, "target": t, "relation": r, "confidence": c}
                  for (s, t), (r, c) in sorted(aristas.items())],
    }
    huellas = {
        "version": VERSION, "generado": generado, "raices": raices,
        "archivos": {i: {"tam": x["tam"], "mtime_ns": x["mtime_ns"], "fecha": _iso(x["mtime_ns"]),
                         "sha1": x["sha1"], "resumen": x["resumen"]}
                     for i, x in sorted(archivos.items())},
    }
    os.makedirs(salida_larga, exist_ok=True)
    for nombre, contenido in (("grafo.json", grafo), ("huellas.json", huellas), ("cambios.json", cambios)):
        with open(os.path.join(salida_larga, nombre), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(contenido, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(salida_larga, "MAPA.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(mapa)

    return {
        "modo": modo, "motivo": motivo, "nuevos": nuevos, "cambiados": cambiados,
        "borrados": borrados, "n_cambios": len(acumulado), "nucleo": nucleo_sel,
        "corridas_pendientes": len(cambios.get("corridas", [])),
        "ratio": ratio, "palabras": palabras, "archivos": len(archivos), "aristas": len(aristas),
        "aristas_lista": sorted((s, t, r) for (s, t), (r, _) in aristas.items()),
        "huerfanos": huerfanos, "sin_resumen": sin_resumen, "excluidos": {k: list(v) for k, v in excl.items()},
        "nivel": NIVELES.index(nivel), "segundos": time.perf_counter() - t0,
        "mapa": os.path.join(salida, "MAPA.md"), "resumenes": {i: x["resumen"] for i, x in archivos.items()},
    }


def linea_final(r):
    return f"MODO: {r['modo']} · cambiados {r['n_cambios']} · mapa {r['palabras']} palabras"


def imprimir(r):
    print(f"Archivos: {r['archivos']} · enlaces: {r['aristas']} · huérfanos: {len(r['huerfanos'])} · "
          f"sin resumen: {len(r['sin_resumen'])}")
    print(f"Motivo del modo: {r['motivo']}")
    for i, motivo in r["nucleo"]:
        print(f"  núcleo: {i} ({motivo})")
    if r["modo"] == "relectura":
        for i in r["nuevos"]:
            print(f"  releer (nuevo): {i}")
        for i in r["cambiados"]:
            print(f"  releer (cambiado): {i}")
        for i in r["borrados"]:
            print(f"  borrado: {i}")
    print(f"Mapa: {r['mapa']} (nivel de compresión {r['nivel']})")
    print(f"Tiempo: {r['segundos']:.2f} s".replace(".", ","))
    print(linea_final(r))


# ------------------------------------------------------------------ prueba
def probar():
    caso = json.loads((SKILL / "pruebas" / "caso-ficticio.json").read_text(encoding="utf-8"))
    esp = json.loads((SKILL / "pruebas" / "esperado.json").read_text(encoding="utf-8"))
    fallas = []

    def chequear(cond, msg):
        print(("  ok    " if cond else "  FALLA ") + msg)
        if not cond:
            fallas.append(msg)

    tmp = tempfile.mkdtemp(prefix="cartografiar-")
    try:
        raiz = os.path.join(tmp, "encargo")
        for rel, contenido in caso["archivos"].items():
            ruta = os.path.join(raiz, *rel.split("/"))
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(contenido)
        hay_xlsx = False
        try:
            import openpyxl  # noqa: PLC0415
            wb = openpyxl.Workbook()
            wb.active.title = "RESUMEN"
            wb.active["A1"] = "Compra ficticia"
            wb.create_sheet("DETALLE")
            wb.save(os.path.join(raiz, "datos", "planilla.xlsx"))
            hay_xlsx = True
        except ImportError:
            pass
        salida = os.path.join(raiz, "contexto")      # dentro de la raíz: debe excluirse sola
        n_esp = esp["primera"]["archivos"] + (1 if hay_xlsx else 0)

        print("1 · primera vez")
        r = cartografiar([raiz], salida)
        chequear(r["modo"] == "primera-vez", f"modo primera-vez (dio {r['modo']})")
        chequear(r["archivos"] == n_esp, f"{n_esp} archivos (dio {r['archivos']})")
        for s, t, rel in esp["primera"]["aristas"]:
            chequear((s, t, rel) in r["aristas_lista"], f"arista {s} → {t} ({rel})")
        chequear(r["aristas"] == len(esp["primera"]["aristas"]),
                 f"{len(esp['primera']['aristas'])} aristas en total (dio {r['aristas']})")
        for i, frag in esp["primera"]["resumenes"].items():
            chequear(frag in r["resumenes"].get(i, ""), f"resumen de {i} contiene «{frag}»")
        if hay_xlsx:
            chequear("RESUMEN" in r["resumenes"].get("datos/planilla.xlsx", ""), "resumen del xlsx trae sus hojas")
        for h in esp["primera"]["huerfanos"]:
            chequear(h in r["huerfanos"], f"huérfano {h}")
        exc = [posixpath.basename(x) for x in r["excluidos"].get("carpetas", [])]
        for d in esp["primera"]["carpetas_excluidas"]:
            chequear(d in exc, f"carpeta excluida {d}")
        for f in ("MAPA.md", "grafo.json", "huellas.json"):
            chequear(os.path.exists(os.path.join(salida, f)), f"escribió {f}")
        g = leer_json(os.path.join(salida, "grafo.json"))
        chequear(bool(g) and {"id", "label", "type"} <= set(g["nodes"][0])
                 and {"source", "target", "relation"} <= set(g["links"][0]), "grafo.json con forma nodes/links")
        mapa = Path(salida, "MAPA.md").read_text(encoding="utf-8")
        chequear(mapa.splitlines()[2].startswith("**MODO: primera-vez**"), "MAPA.md abre con el MODO")
        chequear(r["palabras"] <= 3000, f"mapa ≤ 3.000 palabras ({r['palabras']})")
        nuc = [i for i, _ in r["nucleo"]]
        chequear(nuc == esp["nucleo"]["regla"], f"núcleo por regla {esp['nucleo']['regla']} (dio {nuc})")
        chequear("## Núcleo · leer siempre" in mapa and mapa.index("## Núcleo") < mapa.index("## Carpetas"),
                 "MAPA.md trae «Núcleo · leer siempre» al inicio")
        print("  " + linea_final(r))

        def editar(rel, texto="\nCambio.\n"):
            with open(os.path.join(raiz, *rel.split("/")), "a", encoding="utf-8") as fh:
                fh.write(texto)

        def pendientes():
            return [i for i, _ in neto((leer_json(os.path.join(salida, "cambios.json")) or {}).get("corridas", []))]

        print("1b · otra corrida sin marcar leído")
        r = cartografiar([raiz], salida)
        chequear(r["modo"] == "primera-vez" and "marcado leída" in r["motivo"],
                 f"sigue primera-vez mientras no se marque leída (dio {r['modo']})")
        print("  " + linea_final(r))

        print("2 · --marcar-leido y sin cambios")
        c = marcar_leido(salida)
        chequear(c["base"] == n_esp and not c["corridas"] and not c["primera_vez_pendiente"],
                 f"marcar leído deja base {n_esp} y nada pendiente")
        r = cartografiar([raiz], salida)
        chequear(r["modo"] == "relectura" and r["n_cambios"] == 0,
                 f"relectura con 0 cambiados (dio {r['modo']}, {r['n_cambios']})")
        chequear(r["excluidos"].get("salida") == ["contexto"] and r["archivos"] == n_esp,
                 "la carpeta de salida (dentro de la raíz) no se cartografía")
        print("  " + linea_final(r))

        print("3 · cambia un archivo")
        mod = esp["un_cambio"]["modificar"]
        editar(mod, "\nLlegó una cuarta cotización.\n")
        r = cartografiar([raiz], salida)
        chequear(r["modo"] == "relectura", f"modo relectura (dio {r['modo']})")
        chequear(r["cambiados"] == [mod] and not r["nuevos"] and not r["borrados"],
                 f"releer exactamente {mod} (dio {r['nuevos'] + r['cambiados'] + r['borrados']})")
        mapa = Path(salida, "MAPA.md").read_text(encoding="utf-8")
        chequear(f"- `{mod}` (cambiado)" in mapa, "MAPA.md lo lista en «A releer»")
        print("  " + linea_final(r))

        print("3b · otra corrida sin cambios: lo no leído se mantiene")
        r = cartografiar([raiz], salida)
        chequear(r["modo"] == "relectura" and r["cambiados"] == [mod],
                 f"sigue pendiente {mod} (dio {r['cambiados']})")
        chequear(r["corridas_pendientes"] == 1, "una corrida vacía no se anota en cambios.json")
        print("  " + linea_final(r))

        print("3c · cambia otro: se acumula")
        otro = esp["acumulado"]["modificar"]
        editar(otro)
        r = cartografiar([raiz], salida, umbral=esp["acumulado"]["umbral"])
        chequear(r["modo"] == "relectura" and r["cambiados"] == sorted([mod, otro]),
                 f"acumula {sorted([mod, otro])} (dio {r['cambiados']})")
        chequear(pendientes() == sorted([mod, otro]) and r["corridas_pendientes"] == 2,
                 "cambios.json guarda las dos corridas no leídas")
        print("  " + linea_final(r))

        print("3d · --marcar-leido vacía lo acumulado")
        marcar_leido(salida)
        chequear(pendientes() == [], "cambios.json queda vacío")
        r = cartografiar([raiz], salida)
        chequear(r["modo"] == "relectura" and r["n_cambios"] == 0, f"relectura con 0 (dio {r['n_cambios']})")
        print("  " + linea_final(r))

        print("4 · cambian muchos")
        for rel in esp["muchos_cambios"]["modificar"]:
            editar(rel)
        for rel in esp["muchos_cambios"]["borrar"]:
            os.remove(os.path.join(raiz, *rel.split("/")))
        r = cartografiar([raiz], salida)
        chequear(r["modo"] == "primera-vez", f"sobre el umbral vuelve a primera-vez (dio {r['modo']}, "
                 f"{_pct(r['ratio'])})")
        print("  " + linea_final(r))
        r = cartografiar([raiz], salida)
        chequear(r["modo"] == "primera-vez", "y sigue primera-vez hasta que se marque leída")

        print("5 · --nucleo fija archivos a mano")
        r = cartografiar([raiz], salida, nucleo=esp["nucleo"]["fijar"])
        nuc = [(i, m) for i, m in r["nucleo"]]
        chequear([i for i, _ in nuc] == esp["nucleo"]["con_fijo"] and nuc[0][1] == "fijado a mano",
                 f"núcleo {esp['nucleo']['con_fijo']} (dio {[i for i, _ in nuc]})")
        try:
            cartografiar([raiz], salida, nucleo=["no/existe.md"])
            chequear(False, "--nucleo con una ruta que no existe aborta")
        except ErrorEntrada:
            chequear(True, "--nucleo con una ruta que no existe aborta")

        print("6 · árbol grande: el mapa se comprime")
        grande = os.path.join(tmp, "grande")
        nc, na = esp["grande"]["carpetas"], esp["grande"]["archivos_por_carpeta"]
        for c in range(nc):
            for k in range(na):
                ruta = os.path.join(grande, f"area-{c:02d}", f"sub-{k % 3}", f"nota-{k:03d}.md")
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                with open(ruta, "w", encoding="utf-8") as fh:
                    fh.write(f"# Nota {k} del área {c}\n\nUna nota ficticia con bastante texto para "
                             f"llenar el resumen de una línea del archivo número {k}. Ver [[nota-{(k + 1) % na:03d}]].\n")
        r = cartografiar([grande], os.path.join(tmp, "contexto-grande"))
        chequear(r["archivos"] == nc * na, f"{nc * na} archivos (dio {r['archivos']})")
        chequear(r["palabras"] <= 3000, f"mapa ≤ 3.000 palabras con {nc * na} archivos ({r['palabras']}, "
                 f"nivel {r['nivel']})")
        print("  " + linea_final(r))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fallas:
        print(f"FALLA · {len(fallas)} chequeos no cuadran")
        return 1
    print("OK")
    return 0


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Cartografiar carpetas: MAPA.md + grafo.json + huellas.json, sin LLM.")
    ap.add_argument("carpetas", nargs="*", help="carpetas del encargo")
    ap.add_argument("--salida", help="carpeta contexto/ donde quedan los tres archivos")
    ap.add_argument("--excluir", action="append", default=[], metavar="PATRON",
                    help="patrón glob sobre el nombre o la ruta relativa (se repite)")
    ap.add_argument("--umbral", type=float, default=0.20, help="fracción de cambios hasta la que vale relectura")
    ap.add_argument("--max-palabras", type=int, default=3000)
    ap.add_argument("--max-mb", type=float, default=25.0, help="binarios más grandes que esto se excluyen")
    ap.add_argument("--graphify", action="store_true", help="agrega la nota de cómo enriquecer con /graphify")
    ap.add_argument("--nucleo", default="", metavar="RUTA1,RUTA2",
                    help="hasta 3 archivos (ruta relativa del mapa) que se leen siempre; la regla completa el resto")
    ap.add_argument("--marcar-leido", action="store_true",
                    help="vacía los cambios acumulados de <salida>/cambios.json (lo llama orquestar al consolidar)")
    ap.add_argument("--probar", action="store_true", help="corre la prueba con el caso ficticio")
    a = ap.parse_args(argv)
    if a.probar:
        return probar()
    if a.marcar_leido:
        if not a.salida or a.carpetas:
            ap.error("--marcar-leido va solo, con --salida")
        try:
            c = marcar_leido(a.salida)
        except ErrorEntrada as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        print(f"Marcado leído el {c['leido_el']}: base {c['base']} archivos, cambios acumulados en 0.")
        return 0
    if not a.carpetas or not a.salida:
        ap.error("faltan las carpetas o --salida")
    try:
        r = cartografiar(a.carpetas, a.salida, excluir=a.excluir, umbral=a.umbral,
                         max_palabras=a.max_palabras, max_mb=a.max_mb, graphify=a.graphify,
                         nucleo=[x for x in a.nucleo.split(",") if x.strip()])
    except ErrorEntrada as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    imprimir(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
