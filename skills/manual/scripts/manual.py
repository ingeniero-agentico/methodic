# -*- coding: utf-8 -*-
"""
manual · write and check the operator's traceable manual (contract: docs/MANUAL-FORMAT.md).

    python manual.py init --company <name> [--data <folder>]
    python manual.py new-process <CODE> "<title>" [--owner <role>] [--company <name>] [--data <folder>]
    python manual.py revise <CODE> --change "<what changed>" [--by <role>] [--approve]
    python manual.py check [--company <name>] [--data <folder>] [--strict] [--json]
    python manual.py --test

The manual is an index (NEGOCIO.md / BUSINESS.md) plus one page per process (SIPOC on top, coded
steps below, every step with exactly one source line), next to the interview record, the scope,
the logbook, backups and a work area. `check` applies every rule of the contract and is the gate:
a manual with errors is not done.

Data folder: --data · $METHODIC_DATA · $INGENIERO_DATOS (legacy) · the repo's sibling
../methodic-data · the legacy sibling ../ingeniero-agentico-datos. Company = the profile file name
without .yaml (<data>/profiles/, then perfiles/). Language = the profile's `language` (es by
default). Both name sets are read; the profile's is written; an existing manual keeps the names it
was created with.

Never deletes an operator's file, never overwrites an existing file on init or new-process, uses no
network and starts no process. `--test` removes only its own mn- temp folder (METHODIC_KEEP_TEMP=1
keeps it). Standard library only (Python 3.11+).
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
SKILL = HERE.parents[1]
REPO = HERE.parents[3] if len(HERE.parents) > 3 else SKILL

LANG = "es"


def set_language(lang):
    global LANG
    LANG = "en" if str(lang or "es").strip().lower() == "en" else "es"


def tr(es, en):
    return en if LANG == "en" else es


def other(lang):
    return "en" if lang == "es" else "es"


class UsageError(Exception):
    """A command that cannot run as asked. Nothing was written."""


# ---------------------------------------------------------------- the contract
LAYOUT = {
    "es": {"index": "NEGOCIO.md", "processes": "procesos", "interview": "entrevista",
           "scope": "alcance.yaml", "logbook": "bitacora.md", "backups": "respaldos", "work": "trabajo"},
    "en": {"index": "BUSINESS.md", "processes": "processes", "interview": "interview",
           "scope": "scope.yaml", "logbook": "logbook.md", "backups": "backups", "work": "work"},
}
TEMPLATES = {"es": {"index": "NEGOCIO.md", "process": "proceso.md", "scope": "alcance.yaml"},
             "en": {"index": "BUSINESS.md", "process": "process.md", "scope": "scope.yaml"}}
INDEX_SECTIONS = {"es": ["Qué hace", "Clientes y cobro", "Quién decide", "Procesos", "Límites", "Huecos"],
                  "en": ["What it does", "Customers and billing", "Who decides", "Processes", "Limits", "Gaps"]}
INDEX_HEADERS = {"es": ["Código", "Proceso", "Estado", "Archivo", "Duele"],
                 "en": ["Code", "Process", "Status", "File", "Pain"]}
PAGE_SECTIONS = {"es": {"sipoc": "SIPOC", "operation": "Operación", "steps": "Pasos", "gaps": "Huecos",
                        "history": "Historial"},
                 "en": {"sipoc": "SIPOC", "operation": "Operation", "steps": "Steps", "gaps": "Gaps",
                        "history": "History"}}
# The optional Operation section: what describes the process as a whole, each line with its source.
OPERATION_LABELS = {"es": ("Frecuencia", "Fallas habituales", "Archivos"),
                    "en": ("Frequency", "Usual failures", "Files")}
OP_LINE_RE = re.compile(r"^[-*]\s+([^:]+?)\s*:\s*(.*)$")
OP_SOURCE_RE = re.compile(r"·\s*(?:Origen|Source)\s*:\s*", re.I)
SCOPE_KEYS = ("read", "write_with_ok", "never", "sensitive", "ok_by")
SIPOC_HEADERS = {"es": ["Proveedores", "Entradas", "Proceso", "Salidas", "Clientes"],
                 "en": ["Suppliers", "Inputs", "Process", "Outputs", "Customers"]}
HISTORY_HEADERS = {"es": ["Rev.", "Fecha", "Cambio", "Aprobó"],
                   "en": ["Rev.", "Date", "Change", "Approved by"]}
STATUS = {"es": ("Borrador", "En revisión", "Aprobado"), "en": ("Draft", "In review", "Approved")}
ALL_STATUS = STATUS["es"] + STATUS["en"]
APPROVED = (STATUS["es"][2], STATUS["en"][2])
CAPS = {"index": 400, "process": 800}

PROC_RE = re.compile(r"^[A-ZÁÉÍÓÚÑÜ0-9]+(-[A-ZÁÉÍÓÚÑÜ0-9]+)*$")
REV_RE = re.compile(r"^([A-Z]+|\d+)$")
DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}$")
COMPANY_RE = re.compile(r"^[\w][\w.-]*$")
STEP_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
SUB_RE = re.compile(r"^\s+[-*]\s+(.*)$")
CODE_RE = re.compile(r"^\*\*([^*]+)\*\*(.*)$")
SOURCE_RE = re.compile(r"^(Origen|Source)\s*:\s*(.*)$", re.I)
SKILL_REF_RE = re.compile(r"→\s*`([^`]+)`")
OBS_RE = re.compile(r"^(bit[aá]cora|logbook)\s*,\s*(l[ií]nea|line)\s+(\d+)\s*$", re.I)
GAP_DATE_RE = re.compile(r"(declarado el|declared on)\s+(\S+)", re.I)
SEP_RE = re.compile(r"^:?-{2,}:?$")
SEARCH_CAP = 20000   # files walked per document search, so a huge read root cannot hang the check

# Every code `check` can report. Errors make it fail; warnings are listed.
ERROR_CODES = {
    "manual-missing": "the manual folder does not exist",
    "index-missing": "no NEGOCIO.md / BUSINESS.md",
    "frontmatter": "frontmatter missing or a required field empty",
    "section-missing": "a heading of the contract is missing",
    "cap-words": "body over its word cap (index 400, process 800; frontmatter and History excluded)",
    "code-format": "process or step code not <PROCESS>-NN[.N], or a step without a bold code",
    "code-duplicate": "the same step code twice in the manual",
    "process-mismatch": "file name differs from the frontmatter process",
    "source-missing": "a step without a source line",
    "source-multiple": "a step with more than one source line",
    "source-kind": "a source line that is none of the four kinds",
    "operation-line": "an Operation line that is not Frecuencia · Fallas habituales · Archivos (Frequency · Usual failures · Files)",
    "interview-missing": "interview source whose entrevista/AAAA-MM-DD.md does not exist",
    "logbook-line-missing": "observed source whose logbook line does not exist",
    "document-missing": "document source not found under a read root of the scope",
    "document-out-of-scope": "document source outside the read roots or under never",
    "decision-mark": "◆ not right after the step code",
    "skill-unknown": "→ `skill` that does not exist in the repo's skills/",
    "status-invalid": "status not Borrador · En revisión · Aprobado (Draft · In review · Approved)",
    "revision-invalid": "revision not a letter or a number",
    "status-revision": "approved with a letter revision, or a numbered revision not approved",
    "history-missing": "no history rows",
    "history-mismatch": "last history revision differs from the frontmatter",
    "history-sequence": "history not A, B, … then 0, 1, … one row per revision",
    "date-format": "a date not DD-MM-AAAA (or not a real day)",
    "sipoc-table": "SIPOC table header wrong or without a row",
    "index-row-missing": "a process file without its row in the index",
    "index-file-missing": "an index row whose file does not exist",
    "index-mismatch": "index row code or status differs from the page",
    "scope-invalid": "the scope file cannot be read as the contract's YAML",
    "scope-missing": "no scope file (error only with --strict)",
}
WARNING_CODES = {
    "scope-missing": "no scope file: document sources are not verified",
    "skills-unchecked": "installed outside the repo: → `skill` names are not verified",
    "no-steps": "a process page without steps",
    "sipoc-empty": "a SIPOC cell still empty",
    "gap-undated": "a gap without «declarado el DD-MM-AAAA»",
    "interview-role": "the role of an interview source does not appear in that record",
    "layout-mixed": "both name sets present (NEGOCIO.md and BUSINESS.md)",
    "title-mismatch": "index title or page heading differs from the frontmatter title",
    "owner-missing": "a process page without owner",
    "document-search-capped": "a document search stopped at the file cap",
}


# ---------------------------------------------------------------- small helpers
def today():
    return dt.date.today().strftime("%d-%m-%Y")


def valid_date(s):
    s = (s or "").strip()
    if not DATE_RE.match(s):
        return False
    try:
        dt.date(int(s[6:10]), int(s[3:5]), int(s[0:2]))
        return True
    except ValueError:
        return False


def iso(s):
    return f"{s[6:10]}-{s[3:5]}-{s[0:2]}"


def read_text(p):
    return Path(p).read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def write_text(p, text, exclusive=False):
    """UTF-8 without BOM, LF. exclusive=True refuses to touch an existing file."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x" if exclusive else "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def words(lines):
    """Words of a body: tokens with at least one letter or digit (|, ---, ◆, → do not count)."""
    return sum(1 for ln in lines for tok in ln.split() if any(ch.isalnum() for ch in tok))


def _norm(p):
    return os.path.normcase(os.path.abspath(str(p)))


def under(p, roots):
    np_ = _norm(p)
    for r in roots:
        nr = _norm(r).rstrip("\\/")
        if np_ == nr or np_.startswith(nr + os.sep):
            return True
    return False


def next_letter(r):
    s = list(r)
    i = len(s) - 1
    while i >= 0:
        if s[i] != "Z":
            s[i] = chr(ord(s[i]) + 1)
            return "".join(s)
        s[i] = "A"
        i -= 1
    return "A" + "".join(s)


def status_of(kind, lang):
    return STATUS[lang][{"draft": 0, "review": 1, "approved": 2}[kind]]


# ---------------------------------------------------------------- minimal YAML
def _scalar(s):
    s = s.strip()
    if s in ("", "~", "null", "Null", "NULL"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s == "[]":
        return []
    if s == "{}":
        return {}
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        return [_scalar(x) for x in s[1:-1].split(",") if x.strip()]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def _strip_comment(line):
    inside, q = False, ""
    for i, ch in enumerate(line):
        if ch in "\"'":
            if not inside:
                inside, q = True, ch
            elif ch == q:
                inside = False
        elif ch == "#" and not inside and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


_KEY_RE = re.compile(r"^[^\s:\"'#-][^:]*:(\s|$)")


def read_yaml(text):
    """The YAML subset profiles and scopes use: nested maps, lists and scalars.
    A list item is a map only when it reads «key: value», so «- C:/Users/…» stays a path."""
    rows = []
    for raw in text.splitlines():
        ln = _strip_comment(raw)
        if ln.strip():
            rows.append((len(ln) - len(ln.lstrip(" ")), ln.strip()))

    def block(i, ind):
        if i >= len(rows):
            return None, i
        if rows[i][1].startswith("- ") or rows[i][1] == "-":
            items = []
            while i < len(rows) and rows[i][0] == ind and rows[i][1].startswith("-"):
                rest = rows[i][1][1:].strip()
                if not rest:
                    val, i = block(i + 1, rows[i + 1][0]) if i + 1 < len(rows) else (None, i + 1)
                    items.append(val)
                    continue
                if _KEY_RE.match(rest):
                    rows[i] = (ind + 2, rest)
                    val, i = block(i, ind + 2)
                    items.append(val)
                else:
                    items.append(_scalar(rest))
                    i += 1
            return items, i
        mapping = {}
        while i < len(rows) and rows[i][0] == ind and not rows[i][1].startswith("- "):
            key, _, value = rows[i][1].partition(":")
            key = key.strip().strip("\"'")
            if value.strip():
                mapping[key] = _scalar(value)
                i += 1
            elif i + 1 < len(rows) and rows[i + 1][0] > ind:
                mapping[key], i = block(i + 1, rows[i + 1][0])
            elif i + 1 < len(rows) and rows[i + 1][0] == ind and rows[i + 1][1].startswith("- "):
                mapping[key], i = block(i + 1, ind)
            else:
                mapping[key] = None
                i += 1
        return mapping, i

    data, _ = block(0, rows[0][0]) if rows else ({}, 0)
    return data if data is not None else {}


# ---------------------------------------------------------------- markdown pieces
def parse_doc(text):
    """(frontmatter dict, {key: file line}, has_frontmatter, all lines, index of the first body line)."""
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                fm, where = {}, {}
                for k in range(1, i):
                    m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", lines[k])
                    if m:
                        v = m.group(2).strip()
                        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                            v = v[1:-1]
                        fm[m.group(1)] = v
                        where[m.group(1)] = k + 1
                return fm, where, True, lines, i + 1
    return {}, {}, False, lines, 0


def sections(lines, start=0):
    """{heading: (heading index, end index)} for the «## » headings (first occurrence wins)."""
    out, cur = {}, None
    for i in range(start, len(lines)):
        m = re.match(r"^##\s+(.*?)\s*$", lines[i])
        if m:
            if cur and cur[0] not in out:
                out[cur[0]] = (cur[1], i)
            cur = (m.group(1).strip(), i)
    if cur and cur[0] not in out:
        out[cur[0]] = (cur[1], len(lines))
    return out


def table(lines, start, end):
    """(header cells, [(line index, cells)]) of the first table in lines[start:end]."""
    header, rows = None, []
    for i in range(start, end):
        s = lines[i].strip()
        if not s.startswith("|"):
            if header is not None:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = cells
        elif all(SEP_RE.match(c) for c in cells if c) and any(cells):
            continue
        else:
            rows.append((i, cells))
    return header, rows


def row_text(cells):
    return "| " + " | ".join(cells) + " |"


def parse_steps(lines, start, end):
    steps = []
    for i in range(start, end):
        ln = lines[i]
        m = STEP_RE.match(ln)
        if m:
            steps.append({"idx": i, "text": m.group(1).strip(), "subs": [], "more": []})
            continue
        if not steps or not ln.strip():
            continue
        s = SUB_RE.match(ln)
        if s:
            steps[-1]["subs"].append((i, s.group(1).strip()))
        else:
            steps[-1]["more"].append(ln.strip())
    return steps


def page_lang(secs, default):
    if "Pasos" in secs or "Historial" in secs:
        return "es"
    if "Steps" in secs or "History" in secs:
        return "en"
    return default


def index_lang(secs, default):
    if "Procesos" in secs or "Huecos" in secs:
        return "es"
    if "Processes" in secs or "Gaps" in secs:
        return "en"
    return default


def set_frontmatter(text, updates):
    lines = text.split("\n")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    for k, v in updates.items():
        for i in range(1, end):
            if re.match(rf"^{re.escape(k)}\s*:", lines[i]):
                lines[i] = f"{k}: {v}"
                break
        else:
            lines.insert(end, f"{k}: {v}")
            end += 1
    return "\n".join(lines)


# ---------------------------------------------------------------- data folder, profile, manual
def resolve_data(arg=None, repo=None, env=None):
    """(folder, how). Order: --data · $METHODIC_DATA · $INGENIERO_DATOS · ../methodic-data ·
    ../ingeniero-agentico-datos."""
    env = os.environ if env is None else env
    if arg:
        return Path(arg), "--data"
    for var in ("METHODIC_DATA", "INGENIERO_DATOS"):
        v = env.get(var)
        if v:
            p = Path(v)
            if p.is_file():   # a profile file: its data folder is above profiles/
                p = p.parent.parent if p.parent.name in ("profiles", "perfiles") else p.parent
            return p, "$" + var
    repo = Path(repo) if repo else REPO
    for name in ("methodic-data", "ingeniero-agentico-datos"):
        p = repo.parent / name
        if p.is_dir():
            return p, "../" + name
    raise UsageError(tr("No hay carpeta de datos: usa --data, o define $METHODIC_DATA, o crea "
                        "../methodic-data junto al repo.",
                        "No data folder: pass --data, or set $METHODIC_DATA, or create ../methodic-data "
                        "next to the repo."))


def profile_paths(data):
    out = []
    for sub in ("profiles", "perfiles"):
        d = Path(data) / sub
        if d.is_dir():
            out += sorted(p for p in d.glob("*.yaml") if not p.name.startswith("_"))
    return out


def profile_info(data, company):
    """Language and display name from <data>/profiles/<company>.yaml (then perfiles/)."""
    for sub in ("profiles", "perfiles"):
        p = Path(data) / sub / f"{company}.yaml"
        if p.is_file():
            raw = read_yaml(read_text(p)) or {}
            lang = raw.get("language") or raw.get("idioma") or "es"
            comp = raw.get("company") or raw.get("empresa") or {}
            name = (comp.get("name") or comp.get("nombre")) if isinstance(comp, dict) else None
            return {"path": p, "language": "en" if str(lang).strip().lower() == "en" else "es",
                    "name": name or company}
    return {"path": None, "language": "es", "name": company}


def resolve_company(data, company):
    if company:
        if not COMPANY_RE.match(company):
            raise UsageError(tr(f"--company debe ser un nombre de archivo simple: «{company}»",
                                f"--company must be a plain file name: «{company}»"))
        return company
    mdir = Path(data) / "manual"
    names = sorted(p.name for p in mdir.iterdir() if p.is_dir()) if mdir.is_dir() else []
    if len(names) == 1:
        return names[0]
    if not names:
        names = [p.stem for p in profile_paths(data)]
        if len(names) == 1:
            return names[0]
    raise UsageError(tr(f"Elige la empresa con --company. Hay: {', '.join(names) or 'ninguna'}",
                        f"Pick the company with --company. Found: {', '.join(names) or 'none'}"))


class Manual:
    """One manual: <data>/manual/<company>/, with the name set it was created with."""

    def __init__(self, data, company, profile_lang="es"):
        self.data, self.company = Path(data), company
        self.root = self.data / "manual" / company
        es = (self.root / LAYOUT["es"]["index"]).is_file()
        en = (self.root / LAYOUT["en"]["index"]).is_file()
        self.mixed = es and en
        self.profile_lang = profile_lang
        self.lang = "es" if es and not en else "en" if en and not es else profile_lang

    def path(self, piece):
        return self.root / LAYOUT[self.lang][piece]

    def all(self, piece):
        seen, out = set(), []
        for lang in (self.lang, other(self.lang)):
            p = self.root / LAYOUT[lang][piece]
            if p.exists() and _norm(p) not in seen:
                seen.add(_norm(p))
                out.append(p)
        return out

    def find(self, piece):
        found = self.all(piece)
        return found[0] if found else None

    def rel(self, p):
        return Path(p).relative_to(self.root).as_posix()

    def page(self, code):
        for d in self.all("processes"):
            if (d / f"{code}.md").is_file():
                return d / f"{code}.md"
        return None


def repo_skills_dir():
    """The repo's skills/ when this script runs inside the repo; None when installed as a copy."""
    skills = SKILL.parent
    if skills.name == "skills" and any((skills.parent / p).is_file() for p in
                                       ("profiles/_template.yaml", "perfiles/_plantilla.yaml")):
        return skills
    return None


def template(lang, piece, **values):
    p = SKILL / "templates" / TEMPLATES[lang][piece]
    if not p.is_file():
        raise UsageError(tr(f"Falta la plantilla {p.name} en templates/", f"Template {p.name} missing in templates/"))
    text = read_text(p)
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


# ---------------------------------------------------------------- commands that write
def cmd_init(data, company, date=None, profile=None):
    """Create <data>/manual/<company>/ in the profile's language. Never overwrites a file."""
    if not COMPANY_RE.match(company or ""):
        raise UsageError(tr("init necesita --company <nombre>", "init needs --company <name>"))
    profile = profile or profile_info(data, company)
    man = Manual(data, company, profile["language"])
    set_language(man.lang)
    date = date or today()
    created, kept = [], []
    man.root.mkdir(parents=True, exist_ok=True)
    for piece in ("processes", "interview", "backups", "work"):
        if man.find(piece):
            kept.append(man.rel(man.find(piece)))
        else:
            man.path(piece).mkdir(parents=True)
            created.append(LAYOUT[man.lang][piece] + "/")
    files = (("index", lambda: template(man.lang, "index", company=profile["name"], date=date)),
             ("scope", lambda: template(man.lang, "scope")),
             ("logbook", lambda: ""))
    for piece, make in files:
        if man.find(piece):
            kept.append(man.rel(man.find(piece)))
            continue
        write_text(man.path(piece), make(), exclusive=True)
        created.append(LAYOUT[man.lang][piece])
    return man, created, kept


def _index_row_update(man, code, title, status, revision, date, file_rel=None):
    """Add or update the index row of a process; returns 'added' or 'updated'."""
    idx = man.find("index")
    if not idx:
        raise UsageError(tr("No hay índice: corre init primero.", "No index: run init first."))
    text = read_text(idx)
    lines = text.split("\n")
    lang = index_lang(sections(lines), man.lang)
    name = INDEX_SECTIONS[lang][3]
    secs = sections(lines)
    if name not in secs:
        raise UsageError(tr(f"El índice no tiene «## {name}».", f"The index has no «## {name}»."))
    start, end = secs[name]
    header, rows = table(lines, start + 1, end)
    st = f"{status} · rev. {revision}"
    action = "updated"
    for i, cells in rows:
        if cells and cells[0] == code:
            cells = (cells + [""] * 5)[:max(5, len(cells))]
            cells[2] = st
            lines[i] = row_text(cells)
            break
    else:
        action = "added"
        new = row_text([code, title, st, file_rel or f"{LAYOUT[man.lang]['processes']}/{code}.md", "—"])
        if header is None:
            at = start + 1
            lines[at:at] = [row_text(INDEX_HEADERS[lang]), "|---|---|---|---|---|", new]
        else:
            last = rows[-1][0] if rows else next(i for i in range(start + 1, end) if lines[i].strip().startswith("|")) + 1
            lines.insert(last + 1, new)
    text = set_frontmatter("\n".join(lines), {"date": date}) if lines[0].strip() == "---" else "\n".join(lines)
    write_text(idx, text)
    return action


def cmd_new_process(man, code, title, owner=None, date=None):
    set_language(man.lang)
    if not PROC_RE.match(code or ""):
        raise UsageError(tr(f"Código «{code}» inválido: mayúsculas, dígitos y -, como COMPRAS.",
                            f"Invalid code «{code}»: uppercase letters, digits and -, like PURCHASING."))
    if not (title or "").strip():
        raise UsageError(tr("Falta el título del proceso.", "The process title is missing."))
    if not man.find("index"):
        raise UsageError(tr("No hay manual: corre init primero.", "No manual: run init first."))
    if man.page(code):
        raise UsageError(tr(f"{code} ya existe: {man.rel(man.page(code))}. Se cambia con revise, no se pisa.",
                            f"{code} already exists: {man.rel(man.page(code))}. Change it with revise; it is "
                            f"never overwritten."))
    date = date or today()
    title = title.strip().replace("|", "/")
    page = man.path("processes") / f"{code}.md"
    write_text(page, template(man.lang, "process", code=code, title=title, owner=(owner or "—").strip(),
                              date=date), exclusive=True)
    _index_row_update(man, code, title, status_of("draft", man.lang), "A", date, man.rel(page))
    return page


def cmd_revise(man, code, change, by=None, approve=False, date=None, skills_dir=None, strict=False):
    """Append a history row and move the revision: letter → next letter (In review);
    --approve → 0 (Approved), then 1, 2… An approved page changes only with --approve."""
    set_language(man.lang)
    page = man.page(code)
    if not page:
        raise UsageError(tr(f"No existe el proceso {code}.", f"Process {code} does not exist."))
    if not (change or "").strip():
        raise UsageError(tr("--change dice qué cambió.", "--change says what changed."))
    date = date or today()
    text = read_text(page)
    fm, _, has_fm, lines, _ = parse_doc(text)
    if not has_fm:
        raise UsageError(tr(f"{man.rel(page)} no tiene frontmatter.", f"{man.rel(page)} has no frontmatter."))
    rev = fm.get("revision", "")
    if not REV_RE.match(rev):
        raise UsageError(tr(f"Revisión «{rev}» inválida en {man.rel(page)}.", f"Invalid revision «{rev}» in {man.rel(page)}."))
    lang = page_lang(sections(lines), man.lang)
    if approve:
        if not (by or "").strip():
            raise UsageError(tr("--approve necesita --by <rol>: quién aprobó (el operador, nunca el modelo).",
                                "--approve needs --by <role>: who approved (the operator, never the model)."))
        rep = check_manual(man, skills_dir, strict=strict)
        mine = [e for e in rep["errors"] if e["file"] == man.rel(page)]
        if mine:
            raise UsageError(tr(f"{code} tiene {len(mine)} error(es); no se aprueba hasta corregirlos:\n",
                                f"{code} has {len(mine)} error(s); it is not approved until they are fixed:\n")
                             + "\n".join(f"{e['code']} · line {e['line']} · {e['message']}" for e in mine))
        new_rev = "0" if rev.isalpha() else str(int(rev) + 1)
        new_status = status_of("approved", lang)
    else:
        if rev.isdigit():
            raise UsageError(tr(f"{code} está aprobado (rev. {rev}). Un cambio a una página aprobada lo aprueba "
                                f"el operador: registra con --approve --by <rol> después de su OK.",
                                f"{code} is approved (rev. {rev}). A change to an approved page is approved by "
                                f"the operator: record it with --approve --by <role> after their OK."))
        new_rev, new_status = next_letter(rev), status_of("review", lang)
    # history row
    secs = sections(lines)
    hname = PAGE_SECTIONS[lang]["history"]
    row = row_text([new_rev, date, change.strip().replace("|", "/"), (by or "—").strip().replace("|", "/")])
    if hname in secs:
        start, end = secs[hname]
        header, rows = table(lines, start + 1, end)
        if rows:
            lines.insert(rows[-1][0] + 1, row)
        elif header is not None:
            sep = next(i for i in range(start + 1, end) if lines[i].strip().startswith("|")) + 1
            lines.insert(sep + 1, row)
        else:
            lines[start + 1:start + 1] = [row_text(HISTORY_HEADERS[lang]), "|---|---|---|---|", row]
    else:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", f"## {hname}", row_text(HISTORY_HEADERS[lang]), "|---|---|---|---|", row, ""]
    text = set_frontmatter("\n".join(lines), {"status": new_status, "revision": new_rev, "date": date})
    write_text(page, text)
    _index_row_update(man, code, fm.get("title", code), new_status, new_rev, date, man.rel(page))
    return rev, new_rev, new_status


# ---------------------------------------------------------------- check
class Checker:
    def __init__(self, man, skills_dir, strict):
        self.man, self.skills_dir, self.strict = man, skills_dir, strict
        self.errors, self.warnings, self.assumptions, self.pieces = [], [], [], []
        self.codes = {}
        self.scope_state, self.read_roots, self.never, self.ok_by = "missing", [], [], []
        self.scope_rel = LAYOUT[man.lang]["scope"]
        self.docs_unverified = 0
        self.logbook = None
        self.skill_refs = 0
        self.search_cache = {}
        self.capped = False

    def err(self, code, rel, line, msg):
        self.errors.append({"code": code, "file": rel, "line": line, "message": msg})

    def warn(self, code, rel, line, msg):
        self.warnings.append({"code": code, "file": rel, "line": line, "message": msg})

    # -- inputs
    def load_scope(self):
        p = self.man.find("scope")
        if not p:
            return
        self.scope_rel = self.man.rel(p)
        try:
            raw = read_yaml(read_text(p))
        except Exception as e:   # malformed YAML is reported, not raised
            raw = e
        if not isinstance(raw, dict):
            self.scope_state = "invalid"
            self.err("scope-invalid", self.scope_rel, 0, tr("no se lee como mapa YAML", "cannot be read as a YAML map"))
            return
        bad = [k for k in SCOPE_KEYS if raw.get(k) is not None and not isinstance(raw.get(k), list)]
        if bad:
            self.scope_state = "invalid"
            self.err("scope-invalid", self.scope_rel, 0, tr(f"deben ser listas: {', '.join(bad)}",
                                                             f"must be lists: {', '.join(bad)}"))
            return
        self.scope_state = "ok"
        self.read_roots = [Path(str(x)) for x in (raw.get("read") or []) if x]
        self.never = [Path(str(x)) for x in (raw.get("never") or []) if x]
        self.ok_by = [str(x) for x in (raw.get("ok_by") or []) if x]   # read for intervene; listed only

    def load_logbook(self):
        p = self.man.find("logbook")
        if p:
            text = read_text(p)
            self.logbook = text[:-1].split("\n") if text.endswith("\n") else text.split("\n")
            if self.logbook == [""]:
                self.logbook = []

    # -- sources
    def check_source(self, rel, line, code, value):
        kind, _, rest = value.partition("·")
        k = kind.strip().lower()
        rest = rest.strip()
        if k in ("entrevista", "interview"):
            parts = [x.strip() for x in rest.split("·")]
            if len(parts) != 2 or not all(parts):
                self.err("source-kind", rel, line, tr("se espera «entrevista · <rol> · DD-MM-AAAA»",
                                                      "expected «interview · <role> · DD-MM-YYYY»"))
                return
            role, date = parts
            if not valid_date(date):
                self.err("date-format", rel, line, tr(f"fecha «{date}» no es DD-MM-AAAA", f"date «{date}» is not DD-MM-YYYY"))
                return
            found = [d / f"{iso(date)}.md" for d in self.man.all("interview") if (d / f"{iso(date)}.md").is_file()]
            if not found:
                self.err("interview-missing", rel, line,
                         tr(f"{code}: no existe {LAYOUT[self.man.lang]['interview']}/{iso(date)}.md",
                            f"{code}: {LAYOUT[self.man.lang]['interview']}/{iso(date)}.md does not exist"))
            elif role.casefold() not in read_text(found[0]).casefold():
                self.warn("interview-role", rel, line, tr(f"{code}: «{role}» no aparece en {self.man.rel(found[0])}",
                                                          f"{code}: «{role}» does not appear in {self.man.rel(found[0])}"))
        elif k in ("documento", "document"):
            name = rest.split(",")[0].strip()
            if not name:
                self.err("source-kind", rel, line, tr("se espera «documento · <archivo>[, <lugar>]»",
                                                      "expected «document · <file>[, <location>]»"))
                return
            self.check_document(rel, line, code, name)
        elif k in ("observado", "observed"):
            m = OBS_RE.match(rest)
            if not m:
                self.err("source-kind", rel, line, tr("se espera «observado · bitácora, línea N»",
                                                      "expected «observed · logbook, line N»"))
                return
            n = int(m.group(3))
            if self.logbook is None:
                self.err("logbook-line-missing", rel, line, tr(f"{code}: no hay bitácora", f"{code}: there is no logbook"))
            elif not (1 <= n <= len(self.logbook)) or not self.logbook[n - 1].strip():
                self.err("logbook-line-missing", rel, line,
                         tr(f"{code}: la bitácora no tiene línea {n} (tiene {len(self.logbook)})",
                            f"{code}: the logbook has no line {n} (it has {len(self.logbook)})"))
        elif k in ("supuesto", "assumption"):
            if not rest:
                self.err("source-kind", rel, line, tr("un SUPUESTO dice por qué", "an ASSUMPTION says why"))
                return
            self.assumptions.append({"step": code, "file": rel, "line": line, "why": rest})
        else:
            self.err("source-kind", rel, line,
                     tr(f"«{kind.strip()}» no es entrevista · documento · observado · SUPUESTO",
                        f"«{kind.strip()}» is not interview · document · observed · ASSUMPTION"))

    def search(self, name, roots):
        key = name.casefold()
        if key in self.search_cache:
            return self.search_cache[key]
        found, walked = [], 0
        for r in roots:
            if not Path(r).is_dir():
                continue
            for dirpath, dirnames, filenames in os.walk(r):
                dirnames[:] = [d for d in dirnames if not under(Path(dirpath) / d, self.never)]
                walked += len(filenames)
                for f in filenames:
                    if f.casefold() == key:
                        found.append(Path(dirpath) / f)
                if walked > SEARCH_CAP:
                    self.capped = True
                    break
            if found or walked > SEARCH_CAP:
                break
        self.search_cache[key] = found
        return found

    def check_document(self, rel, line, code, name):
        if self.scope_state != "ok":
            self.docs_unverified += 1
            return
        roots = self.read_roots + self.man.all("work")
        p = Path(name)
        if p.is_absolute():
            if not p.is_file():
                self.err("document-missing", rel, line, tr(f"{code}: no existe {name}", f"{code}: {name} does not exist"))
            elif under(p, self.never) or not under(p, roots):
                self.err("document-out-of-scope", rel, line, tr(f"{code}: {name} está fuera de read o bajo never",
                                                                f"{code}: {name} is outside read or under never"))
            return
        # A path under `never` is refused without looking at it; the search never walks into `never`.
        direct = [r / p for r in roots]
        if any(not under(c, self.never) and c.is_file() for c in direct):
            return
        if any(under(c, self.never) for c in direct):
            self.err("document-out-of-scope", rel, line, tr(f"{code}: {name} está bajo never",
                                                            f"{code}: {name} is under never"))
            return
        if len(p.parts) == 1 and self.search(name, roots):
            return
        self.err("document-missing", rel, line,
                 tr(f"{code}: «{name}» no está bajo ninguna carpeta read de {self.scope_rel}",
                    f"{code}: «{name}» is not under any read folder of {self.scope_rel}"))

    # -- gaps
    def check_gaps(self, rel, lines, sec):
        start, end = sec
        for i in range(start + 1, end):
            s = lines[i].strip()
            if not s.startswith(("- ", "* ")):
                continue
            m = GAP_DATE_RE.search(s)
            if not m:
                self.warn("gap-undated", rel, i + 1, tr("hueco sin «declarado el DD-MM-AAAA»",
                                                        "gap without «declared on DD-MM-YYYY»"))
            elif not valid_date(m.group(2).rstrip(".,;")):
                self.err("date-format", rel, i + 1, tr(f"fecha «{m.group(2)}» no es DD-MM-AAAA",
                                                       f"date «{m.group(2)}» is not DD-MM-YYYY"))

    # -- a process page
    def check_page(self, path):
        rel = self.man.rel(path)
        fm, where, has_fm, lines, body = parse_doc(read_text(path))
        info = {"file": rel, "process": fm.get("process", ""), "title": fm.get("title", ""),
                "status": fm.get("status", ""), "revision": fm.get("revision", ""), "steps": 0}
        if not has_fm:
            self.err("frontmatter", rel, 1, tr("sin frontmatter ---", "no --- frontmatter"))
        else:
            for k in ("process", "title", "status", "revision", "date"):
                if not fm.get(k):
                    self.err("frontmatter", rel, where.get(k, 1), tr(f"falta «{k}»", f"«{k}» missing"))
            if not fm.get("owner") or fm.get("owner") == "—":
                self.warn("owner-missing", rel, where.get("owner", 1), tr("sin dueño del proceso", "no process owner"))
        proc = fm.get("process", "")
        if proc and not PROC_RE.match(proc):
            self.err("code-format", rel, where.get("process", 1),
                     tr(f"proceso «{proc}»: mayúsculas, dígitos y -", f"process «{proc}»: uppercase, digits and -"))
        if proc and proc != path.stem:
            self.err("process-mismatch", rel, where.get("process", 1),
                     tr(f"el archivo se llama {path.stem} y el proceso es {proc}",
                        f"the file is {path.stem} and the process is {proc}"))
        if fm.get("date") and not valid_date(fm["date"]):
            self.err("date-format", rel, where.get("date", 1), tr(f"fecha «{fm['date']}» no es DD-MM-AAAA",
                                                                  f"date «{fm['date']}» is not DD-MM-YYYY"))
        secs = sections(lines, body)
        lang = page_lang(secs, self.man.lang)
        names = PAGE_SECTIONS[lang]
        for key in ("sipoc", "steps", "gaps", "history"):
            if names[key] not in secs:
                self.err("section-missing", rel, body + 1, tr(f"falta «## {names[key]}»", f"«## {names[key]}» missing"))
        h1 = next((ln for ln in lines[body:] if ln.startswith("# ")), "")
        if proc and fm.get("title") and h1.strip() != f"# {proc} · {fm['title']}":
            self.warn("title-mismatch", rel, body + 1, tr(f"el título debe ser «# {proc} · {fm['title']}»",
                                                          f"the heading should be «# {proc} · {fm['title']}»"))
        # status and revision
        status, rev = fm.get("status", ""), fm.get("revision", "")
        if status and status not in ALL_STATUS:
            self.err("status-invalid", rel, where.get("status", 1), tr(f"estado «{status}»", f"status «{status}»"))
        if rev and not REV_RE.match(rev):
            self.err("revision-invalid", rel, where.get("revision", 1), tr(f"revisión «{rev}»", f"revision «{rev}»"))
        if status in ALL_STATUS and REV_RE.match(rev or ""):
            if status in APPROVED and rev.isalpha():
                self.err("status-revision", rel, where.get("status", 1),
                         tr(f"{status} con revisión en letra ({rev}): al aprobar la revisión pasa a 0",
                            f"{status} with a letter revision ({rev}): approval sets revision 0"))
            if status not in APPROVED and rev.isdigit():
                self.err("status-revision", rel, where.get("status", 1),
                         tr(f"revisión {rev} es de página aprobada, pero el estado es {status}",
                            f"revision {rev} belongs to an approved page, but the status is {status}"))
        # history
        hsec = secs.get(names["history"])
        if hsec:
            header, rows = table(lines, hsec[0] + 1, hsec[1])
            if not rows:
                self.err("history-missing", rel, hsec[0] + 1, tr("historial sin filas", "history without rows"))
            else:
                for i, cells in rows:
                    if len(cells) < 2 or not valid_date(cells[1]):
                        self.err("date-format", rel, i + 1, tr(f"fecha del historial «{cells[1] if len(cells) > 1 else ''}»",
                                                               f"history date «{cells[1] if len(cells) > 1 else ''}»"))
                revs = [cells[0] for _, cells in rows]
                if revs[-1] != rev:
                    self.err("history-mismatch", rel, rows[-1][0] + 1,
                             tr(f"última fila {revs[-1]}, frontmatter {rev}", f"last row {revs[-1]}, frontmatter {rev}"))
                prev = None
                for (i, cells), r in zip(rows, revs):
                    ok = (r == "A") if prev is None else (
                        r in (next_letter(prev), "0") if prev.isalpha() and REV_RE.match(prev) else
                        (prev.isdigit() and r == str(int(prev) + 1)))
                    if not ok:
                        self.err("history-sequence", rel, i + 1,
                                 tr(f"después de {prev or '(inicio)'} viene {r}", f"{r} follows {prev or '(start)'}"))
                        break
                    prev = r
        # SIPOC
        ssec = secs.get(names["sipoc"])
        if ssec:
            header, rows = table(lines, ssec[0] + 1, ssec[1])
            if header != SIPOC_HEADERS[lang] or not rows:
                self.err("sipoc-table", rel, ssec[0] + 1,
                         tr(f"se espera «{' | '.join(SIPOC_HEADERS[lang])}» y una fila",
                            f"expected «{' | '.join(SIPOC_HEADERS[lang])}» and one row"))
            elif any(not c for _, cells in rows for c in cells):
                self.warn("sipoc-empty", rel, rows[0][0] + 1, tr("SIPOC con celdas vacías", "SIPOC with empty cells"))
        # Operation (optional): «- Frecuencia: … · Origen: <source>», sources checked like a step's
        osec = secs.get(names["operation"])
        if osec:
            labels = OPERATION_LABELS["es"] + OPERATION_LABELS["en"]
            for i in range(osec[0] + 1, osec[1]):
                s = lines[i].strip()
                if not s:
                    continue
                m = OP_LINE_RE.match(s)
                if not m or m.group(1) not in labels:
                    self.err("operation-line", rel, i + 1,
                             tr(f"se espera «- {' / '.join(OPERATION_LABELS['es'])}: … · Origen: …»",
                                f"expected «- {' / '.join(OPERATION_LABELS['en'])}: … · Source: …»"))
                    continue
                label = f"{names['operation']} · {m.group(1)}"
                parts = OP_SOURCE_RE.split(m.group(2))
                if len(parts) < 2:
                    self.err("source-missing", rel, i + 1, tr(f"{label}: sin «· Origen: …» al final",
                                                              f"{label}: no «· Source: …» at the end"))
                elif len(parts) > 2:
                    self.err("source-multiple", rel, i + 1, tr(f"{label}: {len(parts) - 1} orígenes; va uno",
                                                               f"{label}: {len(parts) - 1} sources; one goes"))
                else:
                    self.check_source(rel, i + 1, label, parts[1].strip())
        # steps
        stsec = secs.get(names["steps"])
        steps = parse_steps(lines, stsec[0] + 1, stsec[1]) if stsec else []
        info["steps"] = len(steps)
        if stsec and not steps:
            self.warn("no-steps", rel, stsec[0] + 1, tr("proceso sin pasos", "process without steps"))
        for st in steps:
            ln = st["idx"] + 1
            m = CODE_RE.match(st["text"])
            code, rest = None, st["text"]
            if not m:
                self.err("code-format", rel, ln, tr("paso sin código en negrita **PROCESO-NN**",
                                                    "step without a bold code **PROCESS-NN**"))
            else:
                code, rest = m.group(1).strip(), m.group(2)
                if proc and not re.fullmatch(re.escape(proc) + r"-\d{2}(\.\d+)?", code):
                    self.err("code-format", rel, ln, tr(f"«{code}» no es {proc}-NN[.N]", f"«{code}» is not {proc}-NN[.N]"))
                if code in self.codes:
                    f0, l0 = self.codes[code]
                    self.err("code-duplicate", rel, ln, tr(f"{code} ya está en {f0}:{l0}", f"{code} is already at {f0}:{l0}"))
                else:
                    self.codes[code] = (rel, ln)
            n_marks = rest.count("◆") + sum(t.count("◆") for t in st["more"])
            if n_marks and not (n_marks == 1 and m and rest.lstrip().startswith("◆")):
                self.err("decision-mark", rel, ln, tr("◆ va justo después del código", "◆ goes right after the code"))
            for i, sub in st["subs"]:
                if "◆" in sub:
                    self.err("decision-mark", rel, i + 1, tr("◆ va en la línea del paso, después del código",
                                                             "◆ goes on the step line, after the code"))
            for name in SKILL_REF_RE.findall(" ".join([st["text"]] + st["more"] + [s for _, s in st["subs"]])):
                self.skill_refs += 1
                name = name.strip()
                if self.skills_dir is not None and not (Path(self.skills_dir) / name / "SKILL.md").is_file():
                    self.err("skill-unknown", rel, ln, tr(f"→ `{name}` no existe en skills/", f"→ `{name}` does not exist in skills/"))
            srcs = [(i, SOURCE_RE.match(s).group(2).strip()) for i, s in st["subs"] if SOURCE_RE.match(s)]
            label = code or f"#{ln}"
            if not srcs:
                self.err("source-missing", rel, ln, tr(f"{label}: sin línea «Origen:»", f"{label}: no «Source:» line"))
            elif len(srcs) > 1:
                self.err("source-multiple", rel, srcs[1][0] + 1, tr(f"{label}: {len(srcs)} líneas de origen; va una",
                                                                    f"{label}: {len(srcs)} source lines; one goes"))
            for i, value in srcs[:1]:
                self.check_source(rel, i + 1, label, value)
        # gaps
        if names["gaps"] in secs:
            self.check_gaps(rel, lines, secs[names["gaps"]])
        # words: body without the History section
        counted = lines[body:]
        if hsec:
            counted = lines[body:hsec[0]] + lines[hsec[1]:]
        n = words(counted)
        self.pieces.append({"file": rel, "kind": "process", "words": n, "cap": CAPS["process"],
                            "status": status, "revision": rev, "steps": len(steps)})
        if n > CAPS["process"]:
            self.err("cap-words", rel, 1, tr(f"{n} palabras; el tope es {CAPS['process']}",
                                             f"{n} words; the cap is {CAPS['process']}"))
        return info

    # -- the index
    def check_index(self, pages):
        p = self.man.find("index")
        if not p:
            self.err("index-missing", LAYOUT[self.man.lang]["index"], 0, tr("no hay índice del negocio", "no business index"))
            return
        rel = self.man.rel(p)
        fm, where, has_fm, lines, body = parse_doc(read_text(p))
        if not has_fm:
            self.err("frontmatter", rel, 1, tr("sin frontmatter ---", "no --- frontmatter"))
        else:
            for k in ("company", "date", "revision"):
                if not fm.get(k):
                    self.err("frontmatter", rel, where.get(k, 1), tr(f"falta «{k}»", f"«{k}» missing"))
        if fm.get("date") and not valid_date(fm["date"]):
            self.err("date-format", rel, where.get("date", 1), tr(f"fecha «{fm['date']}» no es DD-MM-AAAA",
                                                                  f"date «{fm['date']}» is not DD-MM-YYYY"))
        if fm.get("revision") and not REV_RE.match(fm["revision"]):
            self.err("revision-invalid", rel, where.get("revision", 1), tr(f"revisión «{fm['revision']}»",
                                                                          f"revision «{fm['revision']}»"))
        secs = sections(lines, body)
        lang = index_lang(secs, self.man.lang)
        for name in INDEX_SECTIONS[lang]:
            if name not in secs:
                self.err("section-missing", rel, body + 1, tr(f"falta «## {name}»", f"«## {name}» missing"))
        n = words(lines[body:])
        self.pieces.insert(0, {"file": rel, "kind": "index", "words": n, "cap": CAPS["index"]})
        if n > CAPS["index"]:
            self.err("cap-words", rel, 1, tr(f"{n} palabras; el tope es {CAPS['index']}",
                                             f"{n} words; the cap is {CAPS['index']}"))
        gaps = INDEX_SECTIONS[lang][5]
        if gaps in secs:
            self.check_gaps(rel, lines, secs[gaps])
        pname = INDEX_SECTIONS[lang][3]
        by_file = {pg["file"]: pg for pg in pages}
        listed = set()
        if pname in secs:
            start, end = secs[pname]
            header, rows = table(lines, start + 1, end)
            if header is not None and header != INDEX_HEADERS[lang]:
                self.err("index-mismatch", rel, start + 2, tr(f"cabecera de la tabla: «{' | '.join(INDEX_HEADERS[lang])}»",
                                                              f"table header: «{' | '.join(INDEX_HEADERS[lang])}»"))
            for i, cells in rows:
                cells = cells + [""] * (5 - len(cells))
                code, title, st, frel = cells[0], cells[1], cells[2], cells[3]
                target = self.man.root / frel if frel else None
                if not target or not target.is_file():
                    self.err("index-file-missing", rel, i + 1, tr(f"{code}: no existe «{frel}»", f"{code}: «{frel}» does not exist"))
                    continue
                pg = by_file.get(self.man.rel(target))
                if not pg:
                    continue
                listed.add(pg["file"])
                if code != pg["process"]:
                    self.err("index-mismatch", rel, i + 1, tr(f"código {code}, la página dice {pg['process']}",
                                                              f"code {code}, the page says {pg['process']}"))
                want = f"{pg['status']} · rev. {pg['revision']}"
                if st != want:
                    self.err("index-mismatch", rel, i + 1, tr(f"{code}: estado «{st}», la página dice «{want}»",
                                                              f"{code}: status «{st}», the page says «{want}»"))
                if title != pg["title"]:
                    self.warn("title-mismatch", rel, i + 1, tr(f"{code}: «{title}» en el índice, «{pg['title']}» en la página",
                                                               f"{code}: «{title}» in the index, «{pg['title']}» on the page"))
        for pg in pages:
            if pg["file"] not in listed:
                self.err("index-row-missing", rel, 0, tr(f"{pg['file']} no tiene fila en «## {pname}»",
                                                         f"{pg['file']} has no row in «## {pname}»"))

    def report(self):
        return {"manual": str(self.man.root), "company": self.man.company, "language": self.man.lang,
                "ok": not self.errors, "errors": self.errors, "warnings": self.warnings,
                "assumptions": self.assumptions, "pieces": self.pieces, "ok_by": self.ok_by}


def check_manual(man, skills_dir, strict=False):
    """Every rule of docs/MANUAL-FORMAT.md. Returns the report dict (ok = no errors)."""
    set_language(man.lang)
    c = Checker(man, skills_dir, strict)
    if not man.root.is_dir():
        c.err("manual-missing", str(man.root), 0, tr("no existe la carpeta del manual: corre init",
                                                     "the manual folder does not exist: run init"))
        return c.report()
    if man.mixed:
        c.warn("layout-mixed", "", 0, tr("están NEGOCIO.md y BUSINESS.md: se usa " + LAYOUT[man.lang]["index"],
                                         "both NEGOCIO.md and BUSINESS.md: using " + LAYOUT[man.lang]["index"]))
    c.load_scope()
    c.load_logbook()
    pages = []
    for d in man.all("processes"):
        for p in sorted(d.glob("*.md")):
            pages.append(c.check_page(p))
    c.check_index(pages)
    if c.scope_state == "missing":
        msg = tr(f"no hay {LAYOUT[man.lang]['scope']}: {c.docs_unverified} origen(es) documento sin verificar",
                 f"no {LAYOUT[man.lang]['scope']}: {c.docs_unverified} document source(s) not verified")
        (c.err if strict else c.warn)("scope-missing", LAYOUT[man.lang]["scope"], 0, msg)
    if c.capped:
        c.warn("document-search-capped", c.scope_rel, 0, tr(f"búsqueda cortada a {SEARCH_CAP} archivos: "
                                                            f"escribe la ruta relativa a la carpeta read",
                                                            f"search stopped at {SEARCH_CAP} files: write the path "
                                                            f"relative to the read folder"))
    if skills_dir is None and c.skill_refs:
        c.warn("skills-unchecked", "", 0, tr(f"instalada fuera del repo: {c.skill_refs} → `skill` sin verificar",
                                             f"installed outside the repo: {c.skill_refs} → `skill` not verified"))
    return c.report()


def print_report(rep):
    mark = tr("SUPUESTO", "ASSUMPTION")
    print(f"manual · {rep['company']} ({rep['language']}) · {rep['manual']}")
    for p in rep["pieces"]:
        line = f"  {p['file']:<26} {p['words']:>4} / {p['cap']} {tr('palabras', 'words')}"
        if p["kind"] == "process":
            line += f" · {p['status']} · rev. {p['revision']} · {p['steps']} {tr('pasos', 'steps')}"
        if p["words"] > p["cap"]:
            line += tr("  ← SOBRE EL TOPE", "  ← OVER THE CAP")
        print(line)
    print(tr(f"errores {len(rep['errors'])} · avisos {len(rep['warnings'])} · supuestos {len(rep['assumptions'])}",
             f"errors {len(rep['errors'])} · warnings {len(rep['warnings'])} · assumptions {len(rep['assumptions'])}"))
    for e in rep["errors"][:15]:
        print(f"  [X] {e['code']} · {e['file']}:{e['line']} · {e['message']}")
    for w in rep["warnings"][:8]:
        print(f"  [!] {w['code']} · {w['file']}:{w['line']} · {w['message']}")
    for a in rep["assumptions"][:8]:
        print(f"  {mark} · {a['step']} · {a['why']}")
    hidden = max(0, len(rep["errors"]) - 15) + max(0, len(rep["warnings"]) - 8) + max(0, len(rep["assumptions"]) - 8)
    if hidden:
        print(tr(f"  … {hidden} más: detalle con --json", f"  … {hidden} more: detail with --json"))
    print("OK" if rep["ok"] else tr(f"FALLA · {len(rep['errors'])} error(es): la página no está lista",
                                    f"FAIL · {len(rep['errors'])} error(s): the manual is not done"))


# ---------------------------------------------------------------- test
def run_test():
    """Runs the case in its own mn- temp folder and removes that folder afterwards (repo rule 8: a
    script may remove what it created itself). METHODIC_KEEP_TEMP=1 keeps it for inspection."""
    exp = json.loads((SKILL / "tests" / "expected.json").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp(prefix="mn-"))
    try:
        fails = _run_test(tmp, exp)
    finally:
        set_language("es")
        if os.environ.get("METHODIC_KEEP_TEMP") == "1":
            print(f"\ntemp kept (METHODIC_KEEP_TEMP=1): {tmp}")
        elif tmp.name.startswith("mn-") and Path(tempfile.gettempdir()).resolve() in tmp.resolve().parents:
            shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        print("FAIL")
        for f in fails:
            print(f"   [X] {f}")
        return 1
    print(f"OK · data folder order, init/new-process/revise in es and en, the sample passes and "
          f"{len(exp['broken'])} broken copies fail with their code")
    return 0


def _run_test(tmp, exp):
    sample = SKILL / "tests" / "sample"
    fails = []
    D = "16-10-2026"

    def same(a, b, what):
        if a != b:
            fails.append(f"{what}: got {a!r}, expected {b!r}")

    def refuses(fn, what):
        try:
            fn()
            fails.append(f"{what}: it did not refuse")
        except UsageError:
            pass

    def history_revs(page):
        _, _, _, lines, body = parse_doc(read_text(page))
        secs = sections(lines, body)
        name = "Historial" if "Historial" in secs else "History"
        return [c[0] for _, c in table(lines, secs[name][0] + 1, secs[name][1])[1]]

    def index_status(man, code):
        _, _, _, lines, body = parse_doc(read_text(man.find("index")))
        secs = sections(lines, body)
        name = "Procesos" if "Procesos" in secs else "Processes"
        return next((c[2] for _, c in table(lines, secs[name][0] + 1, secs[name][1])[1] if c[0] == code), None)

    skills = tmp / "k"   # a fake skills/ folder: the test does not depend on where the script is installed
    for n in ("procurement", "manual"):
        write_text(skills / n / "SKILL.md", f"---\nname: {n}\n---\n")

    # 0 · data folder: --data · $METHODIC_DATA · $INGENIERO_DATOS · ../methodic-data · ../ingeniero-agentico-datos
    r = tmp / "r"
    repo = r / "repo"
    repo.mkdir(parents=True)
    refuses(lambda: resolve_data(None, repo, {}), "no data folder at all")
    (r / "ingeniero-agentico-datos").mkdir()
    same(resolve_data(None, repo, {})[0], r / "ingeniero-agentico-datos", "legacy sibling")
    (r / "methodic-data").mkdir()
    same(resolve_data(None, repo, {})[0], r / "methodic-data", "sibling before legacy sibling")
    env = {"INGENIERO_DATOS": str(r / "i")}
    same(resolve_data(None, repo, env)[0], r / "i", "$INGENIERO_DATOS before siblings")
    env["METHODIC_DATA"] = str(r / "m")
    same(resolve_data(None, repo, env)[0], r / "m", "$METHODIC_DATA before $INGENIERO_DATOS")
    same(resolve_data(str(r / "a"), repo, env)[0], r / "a", "--data first")

    # 1 · lifecycle in Spanish: init, new-process, revise, approve
    data = tmp / "d"
    write_text(data / "profiles" / "ferreteria-andes.yaml", "language: es\ncompany:\n  name: Ferretería Andes\n")
    write_text(data / "perfiles" / "andes-en.yaml", "idioma: en\nempresa:\n  nombre: Ferretería Andes\n")
    man, created, kept = cmd_init(data, "ferreteria-andes", date=D)
    for piece in LAYOUT["es"].values():
        if not (man.root / piece).exists():
            fails.append(f"[es] init did not create {piece}")
    before = read_text(man.find("index"))
    _, created2, _ = cmd_init(data, "ferreteria-andes", date="17-10-2026")
    same(created2, [], "[es] a second init creates nothing")
    same(read_text(man.find("index")), before, "[es] a second init does not overwrite the index")
    same(read_text(man.find("logbook")), "", "[es] the logbook starts empty")
    page = cmd_new_process(man, "COMPRAS", "Comprar material", owner="dueña", date=D)
    fm = parse_doc(read_text(page))[0]
    same((fm["status"], fm["revision"], fm["owner"]), ("Borrador", "A", "dueña"), "[es] new page")
    same(index_status(man, "COMPRAS"), "Borrador · rev. A", "[es] index row of the new page")
    rep = check_manual(man, skills)
    same([e["code"] for e in rep["errors"]], [], "[es] a fresh manual has no errors")
    refuses(lambda: cmd_new_process(man, "COMPRAS", "Otra vez", date=D), "[es] new-process over an existing page")
    refuses(lambda: cmd_new_process(man, "compras-2", "Minúsculas", date=D), "[es] a lowercase code")
    cmd_revise(man, "COMPRAS", "Pasos levantados en la entrevista", date=D, skills_dir=skills)
    refuses(lambda: cmd_revise(man, "COMPRAS", "Aprobado", approve=True, date=D, skills_dir=skills),
            "[es] --approve without --by")
    cmd_revise(man, "COMPRAS", "Aprobado por la dueña", by="dueña", approve=True, date=D, skills_dir=skills)
    refuses(lambda: cmd_revise(man, "COMPRAS", "Cambio sin OK", date=D, skills_dir=skills),
            "[es] a change to an approved page without --approve")
    cmd_revise(man, "COMPRAS", "Monto de aprobación confirmado", by="dueña", approve=True, date=D, skills_dir=skills)
    fm = parse_doc(read_text(page))[0]
    same(history_revs(page), exp["lifecycle"]["revisions"], "[es] history revisions")
    same((fm["status"], fm["revision"]), tuple(exp["lifecycle"]["final"]), "[es] final status and revision")
    same(index_status(man, "COMPRAS"), " · rev. ".join(exp["lifecycle"]["final"]), "[es] index row after approval")
    rep = check_manual(man, skills)
    same([e["code"] for e in rep["errors"]], [], "[es] the approved page has no errors")
    same(Manual(data, "ferreteria-andes", "en").lang, "es", "[es] a manual keeps its names under an en profile")

    # 2 · English layout from an English profile (Spanish profile keys)
    man_en, _, _ = cmd_init(data, "andes-en", date=D)
    for piece in LAYOUT["en"].values():
        if not (man_en.root / piece).exists():
            fails.append(f"[en] init did not create {piece}")
    page_en = cmd_new_process(man_en, "SALES", "Sell over the counter", owner="owner", date=D)
    same(parse_doc(read_text(page_en))[0]["status"], "Draft", "[en] new page status")
    same(index_status(man_en, "SALES"), "Draft · rev. A", "[en] index row")
    cmd_revise(man_en, "SALES", "Steps from the interview", date=D, skills_dir=skills)
    same(index_status(man_en, "SALES"), "In review · rev. B", "[en] index row after revise")
    same([e["code"] for e in check_manual(man_en, skills)["errors"]], [], "[en] the English manual has no errors")
    set_language("es")

    # 3 · the sample manual (tests/sample) with its scope and the document it cites
    emp = tmp / "emp"
    write_text(emp / "Compras" / "comparativo-agosto.xlsx", "fictitious\n")
    write_text(emp / "Sueldos" / "sueldos.txt", "fictitious\n")
    sample_files = {p.relative_to(sample).as_posix(): read_text(p) for p in sorted(sample.rglob("*")) if p.is_file()}
    scope = (f'read:\n  - "{emp.as_posix()}"\nwrite_with_ok:\n  - "{(emp / "Compras").as_posix()}"\n'
             f'never:\n  - "{(emp / "Sueldos").as_posix()}"\nsensitive:\n  - RUT y sueldos del personal\n'
             f'ok_by:\n  - dueña\n')

    def build(folder, case=None):
        files = dict(sample_files)
        files["alcance.yaml"] = scope
        for o in (case or {}).get("omit", []):
            files.pop(o, None)
        if case and "old" in case:
            t = files[case["file"]]
            if t.count(case["old"]) != 1:
                fails.append(f"broken case «{case['name']}»: the text to replace appears {t.count(case['old'])} times")
            new = case.get("new")
            if new is None:
                new = " ".join(["palabra"] * case["pad_words"]) + "\n\n" + case["old"]
            files[case["file"]] = t.replace(case["old"], new)
        root = folder / "manual" / "fa"
        for rel, text in files.items():
            write_text(root / rel, text)
        for d in ("respaldos", "trabajo"):
            (root / d).mkdir(parents=True, exist_ok=True)
        return Manual(folder, "fa", "es")

    sm = build(tmp / "s")
    rep = check_manual(sm, skills)
    json.dumps(rep)   # --json must serialize
    se = exp["sample"]
    same([e["code"] for e in rep["errors"]], [], "[sample] errors")
    same(sorted(w["code"] for w in rep["warnings"]), se["warnings"], "[sample] warnings")
    same(len(rep["assumptions"]), se["assumptions"], "[sample] assumptions")
    same({p["file"]: p["words"] for p in rep["pieces"]}, se["words"], "[sample] words per piece")
    same(next(p["steps"] for p in rep["pieces"] if p["kind"] == "process"), se["steps"], "[sample] steps")
    same(rep["ok_by"], ["dueña"], "[sample] scope ok_by")
    print_report(rep)
    rep_copy = check_manual(sm, None)
    same([w["code"] for w in rep_copy["warnings"]], ["skills-unchecked"], "[sample] installed copy skips skills")
    same(rep_copy["ok"], True, "[sample] installed copy still passes")
    real = repo_skills_dir()
    if real is not None:
        same(check_manual(sm, real)["ok"], True, "[sample] against the repo's skills/")

    # 4 · broken copies: each must fail with its code
    print()
    for k, case in enumerate(exp["broken"], 1):
        bm = build(tmp / "b" / str(k), case)
        rep = check_manual(bm, skills, strict=case.get("strict", False))
        codes = sorted({e["code"] for e in rep["errors"]})
        hit = case["expect"] in codes
        if not hit:
            fails.append(f"broken «{case['name']}»: expected {case['expect']}, got {codes or 'no error'}")
        print(f"  {'ok ' if hit else 'BAD'} {case['name']:<34} → {case['expect']}")
    return fails


# ---------------------------------------------------------------- main
def open_manual(a, must_exist=True):
    data, _ = resolve_data(a.data)
    company = resolve_company(data, a.company)
    prof = profile_info(data, company)
    man = Manual(data, company, prof["language"])
    set_language(man.lang)
    if must_exist and not man.root.is_dir():
        raise UsageError(tr(f"No hay manual en {man.root}: corre init.", f"No manual at {man.root}: run init."))
    return man, prof


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    hide = argparse.SUPPRESS
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--company", help="profile name (file name without .yaml)")
    common.add_argument("--empresa", dest="company", help=hide)
    common.add_argument("--data", help="data folder (default: $METHODIC_DATA, $INGENIERO_DATOS, ../methodic-data)")
    common.add_argument("--datos", dest="data", help=hide)
    common.add_argument("--date", help="date to record, DD-MM-AAAA (default: today)")
    ap = argparse.ArgumentParser(description="Write and check the operator's traceable manual.")
    ap.add_argument("--test", action="store_true", help="run the fictitious case (Ferretería Andes)")
    ap.add_argument("--probar", dest="test", action="store_true", help=hide)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("init", parents=[common], help="create the manual folder")
    p = sub.add_parser("new-process", parents=[common], help="create a process page and its index row")
    p.add_argument("code")
    p.add_argument("title")
    p.add_argument("--owner", help="role that owns the process")
    p = sub.add_parser("revise", parents=[common], help="record a revision (history row, revision, index)")
    p.add_argument("code")
    p.add_argument("--change", required=True, help="what changed")
    p.add_argument("--by", help="role that approved (required with --approve)")
    p.add_argument("--approve", action="store_true", help="the operator approved: revision 0, then 1, 2…")
    p.add_argument("--strict", action="store_true", help=hide)
    p = sub.add_parser("check", parents=[common], help="check every rule of the contract")
    p.add_argument("--strict", action="store_true", help="a missing scope is an error")
    p.add_argument("--json", action="store_true", help="print the full report as JSON")
    a = ap.parse_args(argv)
    try:
        if a.test:
            return run_test()
        if not a.cmd:
            ap.print_help()
            return 2
        if a.date and not valid_date(a.date):
            raise UsageError(f"--date «{a.date}»: DD-MM-AAAA")
        if a.cmd == "init":
            data, how = resolve_data(a.data)
            if not a.company:
                raise UsageError(tr("init necesita --company <nombre>", "init needs --company <name>"))
            company = resolve_company(data, a.company)
            prof = profile_info(data, company)
            man, created, kept = cmd_init(data, company, a.date, prof)
            print(f"manual · {company} ({man.lang}) · {man.root}  [{how}]")
            if prof["path"] is None:
                print(tr(f"  SUPUESTO · no hay profiles/{company}.yaml: idioma es por defecto",
                         f"  ASSUMPTION · no profiles/{company}.yaml: language es by default"))
            for c in created:
                print(tr(f"  creado   {c}", f"  created  {c}"))
            for k in kept:
                print(tr(f"  se queda {k}", f"  kept     {k}"))
            print(tr(f"Siguiente: llenar {LAYOUT[man.lang]['scope']} con el operador y registrar la entrevista.",
                     f"Next: fill {LAYOUT[man.lang]['scope']} with the operator and record the interview."))
            return 0
        man, _ = open_manual(a)
        if a.cmd == "new-process":
            page = cmd_new_process(man, a.code, a.title, a.owner, a.date)
            print(tr(f"creado {man.rel(page)} · {status_of('draft', man.lang)} · rev. A · fila agregada al índice",
                     f"created {man.rel(page)} · {status_of('draft', man.lang)} · rev. A · row added to the index"))
            return 0
        if a.cmd == "revise":
            old, new, status = cmd_revise(man, a.code, a.change, a.by, a.approve, a.date, repo_skills_dir(), a.strict)
            print(f"{a.code} · rev. {old} → {new} · {status}")
            return 0
        if a.cmd == "check":
            rep = check_manual(man, repo_skills_dir(), a.strict)
            if a.json:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            else:
                print_report(rep)
            return 0 if rep["ok"] else 1
    except UsageError as e:
        for i, line in enumerate(str(e).splitlines()):
            print(f"[X] {line}" if i == 0 else f"    {line}")
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
