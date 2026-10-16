# -*- coding: utf-8 -*-
"""
intervene · change a file on the operator's computer through the cycle of docs/MANUAL-FORMAT.md:
plan -> OK of the operator -> backup -> execute -> verify -> logbook.

    python intervene.py check <path> [--write] [--json]
    python intervene.py plan --file P --change "..." --why "..." --verify "..." [--step CODE]
    python intervene.py backup <path>
    python intervene.py log --step CODE|— --file P --change "..." --backup PATH --verified "..." --ok WHO
                            [--corrects N] [--new-file]
    python intervene.py permissions --platform claude-code [--out FILE]
    python intervene.py --test

Common options (every subcommand): --data DIR · --company NAME · --json.

What each subcommand does:

- check        verdict of a path against the scope: out-of-scope · never · read-only ·
               write-needs-ok · work-area-free. Symlinks, junctions and `..` are resolved first;
               the requested path and the path it resolves to are both judged and the more
               restrictive verdict wins (a path that escapes through a link is out of scope).
               Comparison is case-insensitive on Windows.
- plan         validates the path for writing, appends a numbered plan block to the work folder
               and prints it compactly so the operator can say yes or no to that one action.
- backup       copies one file into the backups folder as name_YYYY-MM-DD_HHMM.ext (then HHMMSS,
               then HHMMSS-2...). A backup is created in exclusive mode: it never overwrites one.
- log          appends exactly one logbook line in the contract's format and prints its number
               (the logbook has no header: entry N is physical line N). Earlier lines are never
               rewritten; --corrects N adds "corrige línea N". It warns when --ok is not a role
               listed in the scope's ok_by (an empty ok_by accepts any role and warns).
- permissions  writes a Claude Code permissions file built from the scope into the work folder.
               It never edits the operator's real agent configuration: the person installs it.

Data folder: --data · $METHODIC_DATA · $INGENIERO_DATOS · ../methodic-data · ../ingeniero-agentico-datos
(the last two next to the repo). Company = the profile's file stem; the profile's `language`
(es by default) chooses file names and labels, unless the manual already has files with the other
name set (a manual keeps the names it was created with).

Standard library only. No network, no subprocess. It never deletes nor overwrites an operator's
file; the self-test removes only the ivn-* folder it created inside the system temp folder (kept
when METHODIC_KEEP_TEMP=1).
"""
import argparse
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve()
SKILL = HERE.parents[1]
REPO = HERE.parents[3] if len(HERE.parents) > 3 else SKILL

LANG = "es"            # language of console messages; set from the profile
NOW = datetime.now     # the self-test replaces it with a fixed instant

OUT, NEVER, READ_ONLY, WRITE_OK, WORK = ("out-of-scope", "never", "read-only", "write-needs-ok",
                                         "work-area-free")
RANK = {WORK: 0, WRITE_OK: 1, READ_ONLY: 2, OUT: 3, NEVER: 4}

# File names of the manual, per name set (docs/MANUAL-FORMAT.md, "The layout").
NAMES = {
    "es": {"index": "NEGOCIO.md", "scope": "alcance.yaml", "logbook": "bitacora.md", "backups": "respaldos",
           "work": "trabajo", "plans": "planes.md", "perm": "permisos-claude-code.json"},
    "en": {"index": "BUSINESS.md", "scope": "scope.yaml", "logbook": "logbook.md", "backups": "backups",
           "work": "work", "plans": "plans.md", "perm": "claude-code-permissions.json"},
}
# Labels of a logbook line, per name set.
LABELS = {
    "es": {"backup": "respaldo", "verified": "verificado", "corrects": "corrige línea", "new": "— (archivo nuevo)",
           "cite": "observado · bitácora, línea {n}"},
    "en": {"backup": "backup", "verified": "verified", "corrects": "corrects line", "new": "— (new file)",
           "cite": "observed · logbook, line {n}"},
}
SCOPE_ALIASES = {"leer": "read", "escribir_con_ok": "write_with_ok", "nunca": "never", "sensible": "sensitive",
                 "ok_por": "ok_by"}
STEP_RE = re.compile(r"^[A-ZÁÉÍÓÚÜÑ0-9][A-ZÁÉÍÓÚÜÑ0-9-]*-\d{2}(\.\d+)?$")
SEP = " · "
VAGUE = {"ok", "bien", "listo", "hecho", "se ve bien", "funciona", "todo bien", "revisado", "verificado",
         "looks fine", "looks good", "fine", "done", "works", "checked", "verified", "all good"}

# Commands the operator's agent may never run (Claude Code rule syntax, checked against
# code.claude.com/docs/en/permissions on 16-10-2026). A Bash or PowerShell rule matches the command
# text Claude writes; it is not a boundary around the program (see GUIDE.md).
DENY_DELETE = ["Bash(rm *)", "Bash(rmdir *)", "Bash(del *)", "Bash(rd *)", "Bash(erase *)", "Bash(unlink *)",
               "Bash(shred *)", "Bash(find * -delete*)", "Bash(git clean *)", "Bash(git rm *)",
               "PowerShell(Remove-Item *)", "PowerShell(Clear-Content *)", "PowerShell(Clear-RecycleBin *)"]
DENY_NETWORK = ["Bash(curl *)", "Bash(wget *)", "Bash(ssh *)", "Bash(scp *)", "Bash(sftp *)", "Bash(ftp *)",
                "PowerShell(Invoke-WebRequest *)", "PowerShell(Invoke-RestMethod *)", "PowerShell(curl *)",
                "PowerShell(curl.exe *)", "PowerShell(wget *)", "PowerShell(Start-BitsTransfer *)",
                "PowerShell(Send-MailMessage *)", "WebFetch", "WebSearch"]
DENY_INSTALL = ["Bash(pip install *)", "Bash(pip3 install *)", "Bash(python -m pip install *)",
                "Bash(python3 -m pip install *)", "Bash(py -m pip install *)", "Bash(npm install *)",
                "Bash(npm i *)", "Bash(npx *)", "Bash(winget *)", "Bash(choco *)", "Bash(msiexec *)",
                "Bash(brew install *)", "Bash(apt install *)", "Bash(apt-get install *)", "Bash(sudo *)",
                "PowerShell(pip install *)", "PowerShell(py -m pip install *)", "PowerShell(npm install *)",
                "PowerShell(winget *)", "PowerShell(choco *)", "PowerShell(msiexec *)",
                "PowerShell(Install-Module *)", "PowerShell(Install-Package *)"]
DENY_PUSH = ["Bash(git push *)", "PowerShell(git push *)"]
COMMAND_DENY = DENY_DELETE + DENY_NETWORK + DENY_INSTALL + DENY_PUSH
ASK_ALWAYS = ["mcp__*"]   # every MCP tool (mail, chat, payments...) asks before each call


def set_language(lang):
    global LANG
    LANG = "en" if str(lang or "es").strip().lower() == "en" else "es"


def tr(es, en):
    return en if LANG == "en" else es


class SetupError(Exception):
    """The data folder, the profile, the manual or the scope cannot be used. Exit 2."""


class Refused(Exception):
    """The action is outside what the cycle allows. Exit 3."""


# ---------------------------------------------------------------- minimal YAML (same subset as procurement)
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


def read_yaml(text):
    """The YAML subset profiles and scopes use: nested maps, lists and scalars."""
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
                if ":" in rest and not rest.startswith(("\"", "'")) and not re.match(r"^[A-Za-z]:[\\/]", rest):
                    sub_ind = ind + 2
                    rows[i] = (sub_ind, rest)
                    val, i = block(i, sub_ind)
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
    return data or {}


# ---------------------------------------------------------------- paths
def pkey(p):
    """Comparison key: absolute, normalized, case-folded on Windows."""
    return os.path.normcase(os.path.normpath(str(p)))


def under(child, root):
    """True when the key `child` is `root` or inside it."""
    if child == root:
        return True
    return child.startswith(root if root.endswith(os.sep) else root + os.sep)


class Root:
    """A scope folder, known by the path written and by the path it resolves to."""

    def __init__(self, label, kind=""):
        self.label = str(label)
        self.kind = kind
        lit = os.path.abspath(self.label)
        real = os.path.realpath(self.label)
        self.paths = [lit] if pkey(lit) == pkey(real) else [lit, real]
        self.keys = [pkey(p) for p in self.paths]

    def match(self, key):
        """The alias path that contains `key` (longest first), or None."""
        best = None
        for p, k in zip(self.paths, self.keys):
            if under(key, k) and (best is None or len(k) > len(pkey(best))):
                best = p
        return best

    def depth(self):
        return max(len(k) for k in self.keys)


def is_absolute(s):
    return Path(s).is_absolute()


# ---------------------------------------------------------------- data folder, profile and manual
def data_candidates(arg):
    out = []
    if arg:
        out.append(("--data", Path(arg), True))
    for var in ("METHODIC_DATA", "INGENIERO_DATOS"):
        v = os.environ.get(var)
        if v:
            out.append(("$" + var, Path(v), True))
    out.append(("../methodic-data", REPO.parent / "methodic-data", False))
    out.append(("../ingeniero-agentico-datos", REPO.parent / "ingeniero-agentico-datos", False))
    return out


def resolve_data(arg):
    """Return (data folder, profile file or None, where it came from)."""
    for src, p, explicit in data_candidates(arg):
        if p.is_file():                       # a profile file given directly (legacy $INGENIERO_DATOS)
            data = p.parent.parent if p.parent.name.lower() in ("profiles", "perfiles") else p.parent
            return data, p, src
        if p.is_dir():
            return p, None, src
        if explicit:
            raise SetupError(tr(f"{src} apunta a una carpeta que no existe: {p}",
                                f"{src} points to a folder that does not exist: {p}"))
    raise SetupError(tr("No hay carpeta de datos: usa --data, $METHODIC_DATA o ../methodic-data/",
                        "No data folder: use --data, $METHODIC_DATA or ../methodic-data/"))


def resolve_company(data, profile_file, company):
    """Return (company, profile file or None). Company = the profile's file stem."""
    if profile_file and not company:
        return profile_file.stem, profile_file
    yamls = []
    for d in (data / "profiles", data / "perfiles"):
        if d.is_dir():
            yamls += sorted(p for p in d.glob("*.yaml") if not p.name.startswith("_"))
    if company:
        for p in yamls:
            if p.stem.lower() == company.lower():
                return p.stem, p
        if (data / "manual" / company).is_dir():
            return company, None
        raise SetupError(tr(f"No hay perfil ni manual «{company}». Perfiles: {', '.join(p.stem for p in yamls) or 'ninguno'}",
                            f"No profile nor manual «{company}». Profiles: {', '.join(p.stem for p in yamls) or 'none'}"))
    if len(yamls) == 1:
        return yamls[0].stem, yamls[0]
    if len(yamls) > 1:
        raise SetupError(tr("Hay varios perfiles; elige uno con --company: ",
                            "There are several profiles; pick one with --company: ")
                         + ", ".join(p.stem for p in yamls))
    mans = sorted(d for d in (data / "manual").iterdir() if d.is_dir()) if (data / "manual").is_dir() else []
    if len(mans) == 1:
        return mans[0].name, None
    raise SetupError(tr("No hay perfil en profiles/ y no se sabe qué manual usar: usa --company",
                        "No profile in profiles/ and no single manual: use --company"))


class Ctx:
    """The manual of one company and its scope."""

    def __init__(self, data_arg=None, company=None):
        data, pfile, self.data_source = resolve_data(data_arg)
        self.data = data
        self.company, self.profile = resolve_company(data, pfile, company)
        raw = read_yaml(self.profile.read_text(encoding="utf-8-sig")) if self.profile else {}
        set_language(raw.get("language") or raw.get("idioma") or "es")
        self.manual = data / "manual" / self.company
        if not self.manual.is_dir():
            raise SetupError(tr(f"No existe el manual {self.manual}: primero la entrevista (skill interview)",
                                f"Manual {self.manual} does not exist: run the interview first (skill interview)"))
        self.nameset = self._nameset()
        n = NAMES[self.nameset]
        self.scope_file = self.manual / n["scope"]
        self.logbook = self.manual / n["logbook"]
        self.backups = self.manual / n["backups"]
        self.work = self.manual / n["work"]
        self.plans = self.work / n["plans"]
        self.perm_name = n["perm"]
        self.labels = LABELS[self.nameset]
        self.warnings = []
        self._load_scope()

    def _nameset(self):
        """A manual keeps the names it was created with; a new one takes the profile's language."""
        for ns in ("es", "en"):
            if any((self.manual / NAMES[ns][k]).exists() for k in ("scope", "logbook", "backups", "work", "index")):
                return ns
        return LANG

    def _load_scope(self):
        if not self.scope_file.is_file():
            raise SetupError(tr(f"Falta el alcance {self.scope_file}: se escribe con la persona (tercera ronda "
                                f"de la entrevista). Sin alcance no se decide nada.",
                                f"Scope {self.scope_file} is missing: it is written with the person (third "
                                f"interview round). Without a scope nothing is decided."))
        raw = read_yaml(self.scope_file.read_text(encoding="utf-8-sig"))
        for es, en in SCOPE_ALIASES.items():
            if es in raw and en not in raw:
                raw[en] = raw[es]

        def roots(key):
            vals = raw.get(key) or []
            if isinstance(vals, str):
                vals = [vals]
            out = []
            for v in vals:
                s = str(v or "").strip()
                if not s:
                    continue
                if not is_absolute(s):
                    raise SetupError(tr(f"alcance · {key}: «{s}» no es una ruta absoluta",
                                        f"scope · {key}: «{s}» is not an absolute path"))
                out.append(Root(s, key))
            return out

        self.read, self.write, self.never = roots("read"), roots("write_with_ok"), roots("never")
        self.sensitive = [str(x) for x in (raw.get("sensitive") or [])]
        ok_by = raw.get("ok_by") or []
        self.ok_by = [str(x).strip() for x in ([ok_by] if isinstance(ok_by, str) else ok_by) if str(x or "").strip()]
        if not self.read:
            raise SetupError(tr("El alcance no tiene ninguna carpeta en «read»: no hay nada que leer",
                                "The scope has no folder under «read»: there is nothing to read"))
        self.manual_root = Root(str(self.manual), "manual")
        self.work_root = Root(str(self.work), "work")
        self.backup_root = Root(str(self.backups), "backups")
        for w in self.write:
            if not any(r.match(k) for r in self.read for k in w.keys):
                self.warnings.append(tr(
                    f"«{w.label}» está en write_with_ok pero no bajo ninguna carpeta «read»: el contrato lo deja "
                    f"fuera del alcance. Agrégala a «read» si se debe poder cambiar.",
                    f"«{w.label}» is under write_with_ok but not under any «read» folder: the contract leaves it "
                    f"out of scope. Add it to «read» if it must be changeable."))
            for nv in self.never:
                if any(nv.match(k) for k in w.keys):
                    self.warnings.append(tr(f"«{w.label}» está dentro de «never» ({nv.label}): manda never",
                                            f"«{w.label}» is inside «never» ({nv.label}): never wins"))

    # ------------------------------------------------------------ verdict
    @staticmethod
    def _best(roots, key):
        hits = [(r, r.match(key)) for r in roots]
        hits = [(r, p) for r, p in hits if p]
        return max(hits, key=lambda h: len(pkey(h[1]))) if hits else (None, None)

    def _classify(self, key):
        r, p = self._best(self.never, key)
        if r:
            return NEVER, r, p
        p = self.work_root.match(key)
        if p:
            return WORK, self.work_root, p
        p = self.manual_root.match(key)
        if p:
            return READ_ONLY, self.manual_root, p
        rr, rp = self._best(self.read, key)
        if not rr:
            return OUT, None, None
        wr, wp = self._best(self.write, key)
        if wr:
            return WRITE_OK, wr, wp
        return READ_ONLY, rr, rp

    def check(self, path, write=False):
        lit = os.path.abspath(str(path))
        real = os.path.realpath(str(path))
        v1, r1, p1 = self._classify(pkey(lit))
        v2, r2, p2 = self._classify(pkey(real))
        if RANK[v2] > RANK[v1]:
            verdict, root, rootpath, base = v2, r2, p2, real
        else:
            verdict, root, rootpath, base = v1, r1, p1, lit
        rel = None
        if rootpath:
            rel = os.path.relpath(base, rootpath).replace(os.sep, "/")
            if rel == ".":
                rel = os.path.basename(base)
        allowed = verdict in (WRITE_OK, WORK) if write else verdict in (READ_ONLY, WRITE_OK, WORK)
        return {"path": lit, "resolved": real, "escape": pkey(lit) != pkey(real), "verdict": verdict,
                "root": root.label if root else None, "root_kind": root.kind if root else None,
                "relative": rel, "action": "write" if write else "read", "allowed": allowed,
                "needs_ok": verdict == WRITE_OK and write, "reason": self.reason(verdict, root),
                "warnings": list(self.warnings)}

    def reason(self, verdict, root):
        if verdict == NEVER:
            return tr(f"está en «never» ({root.label}): no se lee ni se toca",
                      f"listed under «never» ({root.label}): not read nor touched")
        if verdict == OUT:
            return tr("fuera del alcance: no está bajo ninguna carpeta «read»",
                      "out of scope: not under any «read» folder")
        if verdict == WORK:
            return tr("área de trabajo del manual: se escribe sin pedir OK",
                      "the manual's work area: written without asking for an OK")
        if verdict == WRITE_OK:
            return tr(f"en write_with_ok ({root.label}): se cambia solo con plan, OK de la persona y respaldo",
                      f"under write_with_ok ({root.label}): changed only with a plan, the person's OK and a backup")
        if root is self.manual_root:
            return tr("carpeta del manual: la escriben los scripts y las skills, no un cambio a mano",
                      "the manual's folder: written by the scripts and skills, not by a hand change")
        return tr(f"se puede leer ({root.label}); no se cambia: no está en write_with_ok",
                  f"may be read ({root.label}); not changed: not under write_with_ok")


# ---------------------------------------------------------------- output helpers
def emit(a, payload, human):
    if getattr(a, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        for line in human:
            print(line)


def require_text(value, flag):
    s = (value or "").strip()
    if not s:
        raise Refused(tr(f"{flag} está vacío: cada campo se llena", f"{flag} is empty: every field is filled"))
    if "\n" in s or "\r" in s:
        raise Refused(tr(f"{flag} tiene saltos de línea: una acción es una línea",
                         f"{flag} has line breaks: one action is one line"))
    if SEP.strip() in s:
        raise Refused(tr(f"{flag} contiene «·», que separa los campos de la bitácora",
                         f"{flag} contains «·», which separates the logbook fields"))
    return s


def norm_step(step, allow_dash=True):
    s = (step or "").strip()
    if allow_dash and s in ("—", "-", "--"):
        return "—"
    if not STEP_RE.match(s):
        raise Refused(tr(f"--step «{s}» no es un código del manual (PROCESO-NN, p. ej. COMPRAS-05) ni «—»",
                         f"--step «{s}» is not a manual code (PROCESS-NN, e.g. COMPRAS-05) nor «—»"))
    return s


def text_lines(path):
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8-sig").splitlines()


def append_text(path, text):
    """Append-only write. A file that does not end in a newline gets one first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = ""
    if path.is_file() and path.stat().st_size:
        with open(path, "rb") as f:
            f.seek(-1, os.SEEK_END)
            if f.read(1) != b"\n":
                prefix = "\n"
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(prefix + text)


# ---------------------------------------------------------------- subcommands
def cmd_check(ctx, a):
    res = ctx.check(a.path, write=a.write)
    human = [f"{res['verdict']} · {res['path']}", f"   {res['reason']}"]
    if res["escape"]:
        human.append(tr(f"   se resuelve a {res['resolved']} (enlace o «..»): se juzgaron las dos rutas",
                        f"   resolves to {res['resolved']} (link or «..»): both paths were judged"))
    if a.write:
        human.append(tr("   escribir: " + ("sí, con plan, OK y respaldo" if res["needs_ok"] else
                                          "sí, libre" if res["allowed"] else "NO"),
                        "   write: " + ("yes, with plan, OK and backup" if res["needs_ok"] else
                                       "yes, free" if res["allowed"] else "NO")))
    for w in res["warnings"]:
        human.append(tr("   aviso: ", "   warning: ") + w)
    emit(a, res, human)
    return 0 if res["allowed"] else 3


def cmd_plan(ctx, a):
    change = require_text(a.change, "--change")
    why = require_text(a.why, "--why")
    verify = require_text(a.verify, "--verify")
    step = norm_step(a.step) if a.step else "—"
    res = ctx.check(a.file, write=True)
    if not res["allowed"]:
        raise Refused(tr(f"no se planifica: {res['verdict']} · {res['reason']}",
                         f"not planned: {res['verdict']} · {res['reason']}"))
    if os.path.isdir(res["path"]):
        raise Refused(tr("un plan cubre un archivo; una carpeta se ordena archivo por archivo",
                         "a plan covers one file; a folder is reorganized file by file"))
    n = 1 + sum(1 for ln in text_lines(ctx.plans) if ln.startswith("## Plan "))
    when = NOW().strftime("%d-%m-%Y %H:%M")
    needs = res["verdict"] == WRITE_OK
    exists = os.path.isfile(res["path"])
    L = (lambda es, en: en if ctx.nameset == "en" else es)
    block = [f"## Plan {n} · {when}", "",
             f"- {L('Archivo', 'File')}: {res['path']}",
             f"- {L('Veredicto', 'Verdict')}: {res['verdict']}",
             f"- {L('Paso', 'Step')}: {step}",
             f"- {L('Cambio', 'Change')}: {change}",
             f"- {L('Por qué', 'Why')}: {why}",
             f"- {L('Verificación', 'Verification')}: {verify}",
             f"- {L('Respaldo', 'Backup')}: " + (L("antes de cambiar, `intervene.py backup`",
                                                  "before changing, `intervene.py backup`") if needs and exists else
                                                L("archivo nuevo, no hay qué respaldar", "new file, nothing to back up")
                                                if needs else L("no aplica (área de trabajo)", "not needed (work area)")),
             f"- OK: " + (L("pendiente", "pending") if needs else L("no se pide (área de trabajo)", "not asked (work area)")),
             "", ""]
    append_text(ctx.plans, "\n".join(block))
    head = f"Plan {n} · {step} · " + (tr("pide OK", "needs OK") if needs else tr("área de trabajo, sin OK", "work area, no OK"))
    human = [head,
             f"   {tr('Archivo  ', 'File     ')} {res['path']}",
             f"   {tr('Cambio   ', 'Change   ')} {change}",
             f"   {tr('Por qué  ', 'Why      ')} {why}",
             f"   {tr('Verificar', 'Verify   ')} {verify}"]
    if needs:
        human.append(f"   {tr('Antes    ', 'Before   ')} " + (tr("respaldo en ", "backup in ") + ctx.backups.name + "/"
                                                              if exists else tr("archivo nuevo", "new file")))
        human.append(tr("¿Lo hago? Responde sí o no (este OK cubre solo esta acción).",
                        "Shall I do it? Answer yes or no (this OK covers only this action)."))
    payload = {"plan": n, "file": res["path"], "verdict": res["verdict"], "step": step, "change": change,
               "why": why, "verify": verify, "needs_ok": needs, "plans_file": str(ctx.plans)}
    emit(a, payload, human)
    return 0


def make_backup(src, folder, now):
    """Copy `src` into `folder` with a timestamp suffix. Exclusive create: never overwrites a backup."""
    folder.mkdir(parents=True, exist_ok=True)
    stem, ext = src.stem, src.suffix
    minute, second = now.strftime("%Y-%m-%d_%H%M"), now.strftime("%Y-%m-%d_%H%M%S")
    names = [f"{stem}_{minute}{ext}", f"{stem}_{second}{ext}"] + [f"{stem}_{second}-{i}{ext}" for i in range(2, 1000)]
    for name in names:
        dest = folder / name
        try:
            with open(dest, "xb") as out, open(src, "rb") as inp:
                shutil.copyfileobj(inp, out)
        except FileExistsError:
            continue
        shutil.copystat(src, dest)
        if dest.stat().st_size != src.stat().st_size:
            raise Refused(tr(f"el respaldo {dest} no tiene el tamaño del original: no sigas",
                             f"backup {dest} does not match the original's size: do not go on"))
        return dest
    raise Refused(tr("más de 999 respaldos del mismo archivo en el mismo segundo", "over 999 backups of one file in one second"))


def cmd_backup(ctx, a):
    res = ctx.check(a.path, write=False)
    if res["verdict"] in (NEVER, OUT):
        raise Refused(tr(f"no se respalda: {res['verdict']} · {res['reason']}",
                         f"not backed up: {res['verdict']} · {res['reason']}"))
    src = Path(res["path"])
    if not src.is_file():
        raise Refused(tr(f"no existe o no es un archivo: {src}", f"does not exist or is not a file: {src}"))
    if ctx.backup_root.match(pkey(os.path.realpath(src))):
        raise Refused(tr("eso ya es un respaldo", "that is already a backup"))
    dest = make_backup(src, ctx.backups, NOW())
    rel = f"{ctx.backups.name}/{dest.name}"
    emit(a, {"backup": rel, "absolute": str(dest), "source": str(src), "bytes": dest.stat().st_size},
         [tr(f"Respaldo: {rel}", f"Backup: {rel}"), f"   {dest}"])
    return 0


def cmd_log(ctx, a):
    step = norm_step(require_text(a.step, "--step"))
    require_text(a.file, "--file")
    change = require_text(a.change, "--change")
    verified = require_text(a.verified, "--verified")
    ok = require_text(a.ok, "--ok")
    backup = require_text(a.backup, "--backup")
    if ok in ("—", "-", "--"):
        raise Refused(tr("--ok dice quién dio el OK; sin OK no hubo ciclo", "--ok says who gave the OK; no OK, no cycle"))
    if re.sub(r"[^\w\s]", "", verified.lower()).strip() in VAGUE:
        raise Refused(tr("--verified pide un hecho (un total recalculado, un archivo reabierto, un conteo), no «se ve bien»",
                         "--verified needs a fact (a total recomputed, a file reopened, a count), not «looks fine»"))
    res = ctx.check(a.file, write=True)
    if not res["allowed"]:
        raise Refused(tr(f"no se anota: {res['verdict']} · {res['reason']}. Si se cambió algo ahí, avísale a la persona.",
                         f"not logged: {res['verdict']} · {res['reason']}. If something was changed there, tell the person."))
    L = ctx.labels
    if a.new_file:
        if backup not in ("—", "-", "--"):
            raise Refused(tr("con --new-file, --backup va «—»", "with --new-file, --backup is «—»"))
        if not os.path.isfile(res["path"]):
            raise Refused(tr("--new-file pero el archivo no existe: no hay qué anotar",
                             "--new-file but the file does not exist: nothing to log"))
        backup_field = L["new"]
    else:
        bp = Path(backup)
        if not bp.is_absolute():
            bp = ctx.manual / bp
        if not bp.is_file():
            raise Refused(tr(f"el respaldo no existe: {bp}. Primero `intervene.py backup`.",
                             f"the backup does not exist: {bp}. Run `intervene.py backup` first."))
        if not ctx.backup_root.match(pkey(os.path.realpath(bp))):
            raise Refused(tr(f"{bp} no está en {ctx.backups.name}/: no es un respaldo de este ciclo",
                             f"{bp} is not in {ctx.backups.name}/: it is not a backup of this cycle"))
        backup_field = f"{ctx.backups.name}/{bp.name}"
    lines = text_lines(ctx.logbook)
    fields = [NOW().strftime("%d-%m-%Y %H:%M"), step, res["relative"] or os.path.basename(res["path"]), change,
              f"{L['backup']}: {backup_field}", f"{L['verified']}: {verified}", f"OK: {ok}"]
    if a.corrects is not None:
        if not 1 <= a.corrects <= len(lines):
            raise Refused(tr(f"--corrects {a.corrects}: la bitácora tiene {len(lines)} líneas",
                             f"--corrects {a.corrects}: the logbook has {len(lines)} lines"))
        fields.append(f"{L['corrects']} {a.corrects}")
    warnings = []
    if not ctx.ok_by:
        warnings.append(tr("el alcance no tiene «ok_by»: se acepta cualquier rol. Anota con la persona quién puede dar el OK.",
                           "the scope has no «ok_by»: any role is accepted. Write down with the person who may give the OK."))
    elif ok.casefold() not in {r.casefold() for r in ctx.ok_by}:
        warnings.append(tr(f"«{ok}» no está en ok_by ({', '.join(ctx.ok_by)}): confirma que podía dar el OK",
                           f"«{ok}» is not in ok_by ({', '.join(ctx.ok_by)}): confirm they could give the OK"))
    line = SEP.join(fields)
    append_text(ctx.logbook, line + "\n")      # no header, ever: entry N is physical line N
    n = len(lines) + 1
    cite = L["cite"].format(n=n)
    emit(a, {"line": n, "text": line, "cite": cite, "logbook": str(ctx.logbook), "warnings": warnings},
         [tr(f"Bitácora, línea {n}:", f"Logbook, line {n}:"), f"   {line}", tr(f"Se cita: {cite}", f"Cite it as: {cite}")]
         + [tr("   aviso: ", "   warning: ") + w for w in warnings])
    return 0


# ---------------------------------------------------------------- permissions
def rule_path(p):
    """A native absolute path as a Claude Code absolute path pattern: C:\\x -> //c/x, /x -> //x."""
    s = str(p).replace("\\", "/")
    m = re.match(r"^([A-Za-z]):(/.*)?$", s)
    if m:
        s = "/" + m.group(1).lower() + (m.group(2) or "")
    s = s.rstrip("/") or ""
    s = re.sub(r"([\[\]*?])", r"\\\1", s)
    return "/" + s


def build_claude_code(ctx):
    allow, ask, deny = [], [], []

    def add(lst, rule):
        if rule not in lst:
            lst.append(rule)

    for r in ctx.read:
        for p in r.paths:
            add(allow, f"Read({rule_path(p)}/**)")
    for p in ctx.manual_root.paths:
        add(allow, f"Read({rule_path(p)}/**)")
    for p in ctx.work_root.paths:
        add(allow, f"Edit({rule_path(p)}/**)")
    for w in ctx.write:
        for p in w.paths:
            add(ask, f"Edit({rule_path(p)}/**)")
    for p in Root(str(ctx.scope_file)).paths:
        add(ask, f"Edit({rule_path(p)})")
    for rule in ASK_ALWAYS:
        add(ask, rule)
    for nv in ctx.never:
        for p in nv.paths:
            for tool in ("Read", "Edit"):
                add(deny, f"{tool}({rule_path(p)})")
                add(deny, f"{tool}({rule_path(p)}/**)")
    for p in ctx.backup_root.paths:
        add(deny, f"Edit({rule_path(p)}/**)")
    for p in Root(str(ctx.logbook)).paths:
        add(deny, f"Edit({rule_path(p)})")
    inner = [k for x in ctx.write + [ctx.work_root, ctx.manual_root] for k in x.keys]
    for r in ctx.read:                       # a read root with nothing writable inside is denied for Edit
        if not any(under(k, rk) for k in inner for rk in r.keys):
            for p in r.paths:
                add(deny, f"Edit({rule_path(p)}/**)")
    for rule in COMMAND_DENY:
        add(deny, rule)
    # No "$schema" line: the generated file carries only the permissions block (templates/ has the
    # commented generic version with the schema line).
    return {"permissions": {"defaultMode": "default", "disableBypassPermissionsMode": "disable",
                            "disableAutoMode": "disable", "allow": allow, "ask": ask, "deny": deny}}


def cmd_permissions(ctx, a):
    if a.platform != "claude-code":
        raise Refused(tr(f"«{a.platform}»: solo se genera para claude-code. Para codex, cursor y gemini-cli lee "
                         f"templates/<plataforma>.md (lo verificado y lo que no).",
                         f"«{a.platform}»: only claude-code is generated. For codex, cursor and gemini-cli read "
                         f"templates/<platform>.md (what was verified and what was not)."))
    out = Path(a.out) if a.out else ctx.work / ctx.perm_name
    res = ctx.check(out, write=True)
    if res["verdict"] != WORK:
        raise Refused(tr(f"el archivo de permisos se escribe solo en {ctx.work}: la persona lo instala",
                         f"the permissions file is written only in {ctx.work}: the person installs it"))
    data = build_claude_code(ctx)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    pm = data["permissions"]
    emit(a, {"file": str(out), "allow": len(pm["allow"]), "ask": len(pm["ask"]), "deny": len(pm["deny"])},
         [tr(f"Permisos: {out}", f"Permissions: {out}"),
          f"   allow {len(pm['allow'])} · ask {len(pm['ask'])} · deny {len(pm['deny'])}",
          tr("   No se instaló nada. Para una sesión: claude --settings <archivo>. Ver GUIA.md, «Instalar los permisos».",
             "   Nothing was installed. For one session: claude --settings <file>. See GUIDE.md, «Install the permissions».")])
    return 0


# ---------------------------------------------------------------- CLI
def build_parser():
    hide = argparse.SUPPRESS
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", dest="data", help="data folder (default: $METHODIC_DATA, $INGENIERO_DATOS, ../methodic-data)")
    common.add_argument("--datos", dest="data", help=hide)
    common.add_argument("--company", dest="company", help="profile name when there are several")
    common.add_argument("--empresa", dest="company", help=hide)
    common.add_argument("--json", action="store_true", help="output as JSON")
    ap = argparse.ArgumentParser(description="Change an operator's file through plan, OK, backup, verification and logbook.")
    ap.add_argument("--test", action="store_true", help="run the fictitious case (Ferretería Andes)")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("check", parents=[common], help="verdict of a path against the scope")
    p.add_argument("path")
    p.add_argument("--write", action="store_true", help="judge it for writing, not only reading")
    p = sub.add_parser("plan", parents=[common], help="write and show the plan of one action")
    p.add_argument("--file", required=True)
    p.add_argument("--change", required=True)
    p.add_argument("--why", required=True)
    p.add_argument("--verify", required=True)
    p.add_argument("--step")
    p = sub.add_parser("backup", parents=[common], help="copy one file into the backups folder")
    p.add_argument("path")
    p = sub.add_parser("log", parents=[common], help="append one logbook line")
    p.add_argument("--step", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--change", required=True)
    p.add_argument("--backup", required=True)
    p.add_argument("--verified", required=True)
    p.add_argument("--ok", required=True)
    p.add_argument("--corrects", type=int)
    p.add_argument("--new-file", dest="new_file", action="store_true", help="the action created the file")
    p = sub.add_parser("permissions", parents=[common], help="generate a permissions file from the scope")
    p.add_argument("--platform", required=True)
    p.add_argument("--out")
    return ap


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.test:
        return run_test()
    if not a.cmd:
        ap.print_help()
        return 1
    try:
        ctx = Ctx(a.data, a.company)
        return {"check": cmd_check, "plan": cmd_plan, "backup": cmd_backup, "log": cmd_log,
                "permissions": cmd_permissions}[a.cmd](ctx, a)
    except SetupError as e:
        emit(a, {"ok": False, "error": str(e)}, [tr("NO SE PUEDE · ", "CANNOT · ") + str(e)])
        return 2
    except Refused as e:
        emit(a, {"ok": False, "refused": True, "error": str(e)}, [tr("RECHAZADO · ", "REFUSED · ") + str(e)])
        return 3


# ---------------------------------------------------------------- self-test
def run_test():
    global NOW
    expected = json.loads((SKILL / "tests" / "expected.json").read_text(encoding="utf-8"))
    tpl_files = sorted((SKILL / "templates").glob("claude-code-*.json"))   # the generic permissions template
    template = json.loads(tpl_files[0].read_text(encoding="utf-8")) if tpl_files else {}
    fixed = datetime(2026, 10, 16, 15, 42, 0)
    saved_now, saved_env, saved_lang = NOW, dict(os.environ), LANG
    NOW = lambda: fixed  # noqa: E731
    failures, notes = [], []
    root = Path(tempfile.mkdtemp(prefix="ivn-"))

    def same(got, exp, what):
        if got != exp:
            failures.append(f"{what}: got {got!r}, expected {exp!r}")
        else:
            print(f"   ok   {what}")

    def run(*args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(list(args))
        out = buf.getvalue()
        try:
            data = json.loads(out)
        except ValueError:
            data = None
        return code, data, out

    try:
        for var in ("METHODIC_DATA", "INGENIERO_DATOS"):
            os.environ.pop(var, None)
        R = Path(os.path.realpath(root))
        # the operator's computer (fictitious): a company folder with three zones, and a folder outside
        emp, fuera, suelto = R / "emp", R / "fuera", R / "suelto"
        for d in (emp / "docs", emp / "plan", emp / "sueldos", fuera, suelto):
            d.mkdir(parents=True)
        (emp / "docs" / "manual-ventas.txt").write_text("Ventas por mesón y por despacho.\n", encoding="utf-8")
        planilla = emp / "plan" / "plantilla-oc.csv"
        original = "neto;iva;total\n100000;0;100000\n"
        planilla.write_text(original, encoding="utf-8")
        (emp / "sueldos" / "sueldos.csv").write_text("rol;sueldo\nvendedor;1\n", encoding="utf-8")
        (fuera / "secreto.txt").write_text("fuera del alcance\n", encoding="utf-8")
        (suelto / "x.csv").write_text("a\n", encoding="utf-8")
        # the data folder: profile and manual of Ferretería Andes
        datos = R / "datos"
        (datos / "profiles").mkdir(parents=True)
        (datos / "profiles" / "ferreteria-andes.yaml").write_text("language: es\ncompany:\n  name: Ferretería Andes\n",
                                                                  encoding="utf-8")
        man = datos / "manual" / "ferreteria-andes"
        man.mkdir(parents=True)
        fw = lambda p: str(p).replace("\\", "/")  # noqa: E731
        (man / "alcance.yaml").write_text(
            f"read:\n  - {fw(emp)}\nwrite_with_ok:\n  - {fw(emp / 'plan')}\n  - {fw(suelto)}\n"
            f"never:\n  - {fw(emp / 'sueldos')}\nsensitive:\n  - sueldos del personal\nok_by:\n  - dueña\n",
            encoding="utf-8")
        (man / "trabajo").mkdir()
        (man / "trabajo" / "nota.md").write_text("borrador\n", encoding="utf-8")
        (man / "respaldos").mkdir()
        (man / "respaldos" / "viejo_2026-10-01_0900.csv").write_text("x\n", encoding="utf-8")
        (man / "NEGOCIO.md").write_text("# Ferretería Andes\n", encoding="utf-8")
        D = ["--data", str(datos)]

        # 1 · verdicts
        print("1 · verdicts")
        cases = {
            "doc": emp / "docs" / "manual-ventas.txt",
            "planilla": planilla,
            "sueldos": emp / "sueldos" / "sueldos.csv",
            "fuera": fuera / "secreto.txt",
            "escape_dotdot_out": str(emp / "plan") + os.sep + ".." + os.sep + ".." + os.sep + "fuera" + os.sep + "secreto.txt",
            "escape_dotdot_never": str(emp / "plan") + os.sep + ".." + os.sep + "sueldos" + os.sep + "sueldos.csv",
            "trabajo": man / "trabajo" / "nota.md",
            "respaldo": man / "respaldos" / "viejo_2026-10-01_0900.csv",
            "manual_page": man / "NEGOCIO.md",
            "write_root_outside_read": suelto / "x.csv",
        }
        if os.name == "nt":
            cases["case_windows"] = str(planilla).upper()
        link = emp / "plan" / "enlace"
        made = None
        try:
            os.symlink(str(fuera), str(link), target_is_directory=True)
            made = "symlink"
        except (OSError, NotImplementedError, AttributeError):
            try:
                import _winapi
                _winapi.CreateJunction(str(fuera), str(link))
                made = "junction"
            except (ImportError, OSError, AttributeError):
                notes.append("symlink escape skipped: this OS does not let a normal user create a link")
        if made:
            cases["symlink_escape"] = link / "secreto.txt"
            notes.append(f"link escape tested with a {made}")
        for name, path in cases.items():
            code, data, _ = run("check", str(path), *D, "--json")
            same(data["verdict"] if data else None, expected["verdicts"][name], f"check {name}")
        for name, exp in expected["write_allowed"].items():
            code, data, _ = run("check", str(cases[name]), "--write", *D, "--json")
            same((data["allowed"], code), (exp, 0 if exp else 3), f"check --write {name}")
        code, data, _ = run("check", str(suelto / "x.csv"), *D, "--json")
        same(bool(data and data["warnings"]), True, "warning for a write_with_ok root outside read")

        # 2 · data folder resolution: --data > $METHODIC_DATA > $INGENIERO_DATOS
        print("2 · data folder")
        datos2 = R / "datos2"
        (datos2 / "profiles").mkdir(parents=True)
        (datos2 / "profiles" / "hardware-andes.yaml").write_text("language: en\n", encoding="utf-8")
        man2 = datos2 / "manual" / "hardware-andes"
        man2.mkdir(parents=True)
        (man2 / "scope.yaml").write_text(f"read:\n  - {fw(emp)}\nwrite_with_ok:\n  - {fw(emp / 'plan')}\n", encoding="utf-8")
        os.environ["METHODIC_DATA"] = str(datos2)
        os.environ["INGENIERO_DATOS"] = str(datos)
        same(Ctx().company, "hardware-andes", "$METHODIC_DATA before $INGENIERO_DATOS")
        same(Ctx(str(datos)).company, "ferreteria-andes", "--data before $METHODIC_DATA")
        os.environ.pop("METHODIC_DATA")
        same(Ctx().company, "ferreteria-andes", "$INGENIERO_DATOS (legacy)")
        os.environ.pop("INGENIERO_DATOS")
        same(Ctx(str(datos)).scope_file.name, "alcance.yaml", "es file names")

        # 3 · the full cycle: plan -> (OK) -> backup -> execute -> verify -> logbook
        print("3 · cycle")
        code, data, _ = run("plan", "--file", str(planilla), "--step", "COMPRAS-05", "--change", "columna IVA corregida",
                            "--why", "la OC salía sin IVA", "--verify", "total = neto × 1,19", *D, "--json")
        same((code, data["plan"], data["needs_ok"]), (0, expected["plan_number"], True), "plan of the planilla")
        same((man / "trabajo" / "planes.md").is_file(), True, "plan written to trabajo/planes.md")
        code, data, _ = run("backup", str(planilla), *D, "--json")
        b1 = data["backup"] if data else None
        same(b1, "respaldos/" + expected["backups"][0], "first backup name")
        planilla.write_text("neto;iva;total\n100000;19000;119000\n", encoding="utf-8")        # execute
        row = planilla.read_text(encoding="utf-8").splitlines()[1].split(";")                # verify: a fact
        same(int(row[2]) == round(int(row[0]) * 1.19), True, "verification recomputes the total")
        code, data, _ = run("log", "--step", "COMPRAS-05", "--file", str(planilla), "--change", "columna IVA corregida",
                            "--backup", b1, "--verified", "total 119000 = 100000 × 1,19", "--ok", "dueña", *D, "--json")
        same((code, data["line"] if data else None), (0, 1), "log returns line 1")
        same(data["text"] if data else None, expected["log_line_1"], "logbook line format")
        same(data["cite"] if data else None, "observado · bitácora, línea 1", "citation of the line")

        # 4 · two more backups in the same minute (and second): none overwrites another
        print("4 · backups never overwrite")
        names = [b1]
        for _ in range(2):
            code, data, _ = run("backup", str(planilla), *D, "--json")
            names.append(data["backup"] if data else None)
        same([n.split("/")[-1] if n else None for n in names], expected["backups"], "backup names in the same minute")
        same((man / b1).read_text(encoding="utf-8"), original, "the first backup still holds the original")

        # 5 · what is refused
        print("5 · refusals")
        before = text_lines(man / "bitacora.md")
        refusals = {
            "log_missing_backup": ("log", "--step", "COMPRAS-05", "--file", str(planilla), "--change", "x",
                                   "--backup", "respaldos/no-existe.csv", "--verified", "total 1 = 1", "--ok", "dueña"),
            "log_backup_outside_backups": ("log", "--step", "COMPRAS-05", "--file", str(planilla), "--change", "x",
                                           "--backup", str(planilla), "--verified", "total 1 = 1", "--ok", "dueña"),
            "log_empty_change": ("log", "--step", "COMPRAS-05", "--file", str(planilla), "--change", " ",
                                 "--backup", b1, "--verified", "total 1 = 1", "--ok", "dueña"),
            "log_vague_verification": ("log", "--step", "—", "--file", str(planilla), "--change", "x",
                                       "--backup", b1, "--verified", "se ve bien", "--ok", "dueña"),
            "log_bad_step": ("log", "--step", "compras5", "--file", str(planilla), "--change", "x",
                             "--backup", b1, "--verified", "total 1 = 1", "--ok", "dueña"),
            "log_no_ok": ("log", "--step", "—", "--file", str(planilla), "--change", "x",
                          "--backup", b1, "--verified", "total 1 = 1", "--ok", "—"),
            "log_read_only_file": ("log", "--step", "—", "--file", str(cases["doc"]), "--change", "x",
                                   "--backup", b1, "--verified", "total 1 = 1", "--ok", "dueña"),
            "log_corrects_missing_line": ("log", "--step", "—", "--file", str(planilla), "--change", "x",
                                          "--backup", b1, "--verified", "total 1 = 1", "--ok", "dueña", "--corrects", "9"),
            "plan_read_only": ("plan", "--file", str(cases["doc"]), "--change", "x", "--why", "y", "--verify", "z"),
            "plan_never": ("plan", "--file", str(cases["sueldos"]), "--change", "x", "--why", "y", "--verify", "z"),
            "plan_out_of_scope": ("plan", "--file", str(cases["fuera"]), "--change", "x", "--why", "y", "--verify", "z"),
            "backup_out_of_scope": ("backup", str(cases["fuera"])),
            "backup_never": ("backup", str(cases["sueldos"])),
            "backup_of_a_backup": ("backup", str(man / b1)),
            "permissions_outside_work": ("permissions", "--platform", "claude-code", "--out", str(fuera / "p.json")),
            "permissions_other_platform": ("permissions", "--platform", "codex"),
        }
        got = sorted(k for k, args in refusals.items() if run(*args, *D)[0] == 3)
        same(got, sorted(expected["refused"]), "every refusal exits 3")
        same(text_lines(man / "bitacora.md"), before, "refusals leave the logbook untouched")
        code, data, _ = run("log", "--step", "COMPRAS-05", "--file", str(planilla), "--change", "columna IVA corregida",
                            "--backup", names[1], "--verified", "total 119000 = 100000 × 1,19 (reabierto)",
                            "--ok", "dueña", "--corrects", "1", *D, "--json")
        same(data["text"] if data else None, expected["log_line_2"], "correction cites the old line")
        lines = text_lines(man / "bitacora.md")
        same((len(lines), lines[0]), (2, expected["log_line_1"]), "line 1 never rewritten")
        same(bool(data and not data["warnings"]), True, "an OK from a role in ok_by gives no warning")
        code, data, _ = run("log", "--step", "COMPRAS-05", "--file", str(planilla), "--change", "formato de fecha",
                            "--backup", names[2], "--verified", "3 fechas releídas en DD-MM-AAAA", "--ok", "bodega",
                            *D, "--json")
        same((code, data["line"] if data else None, len(data["warnings"]) if data else 0), (0, 3, 1),
             "an OK from a role outside ok_by is logged with a warning")
        same(text_lines(man / "bitacora.md")[0], expected["log_line_1"], "no header: entry 1 is physical line 1")
        code, data, _ = run("plan", "--file", str(man / "trabajo" / "resumen.md"), "--change", "resumen",
                            "--why", "para la dueña", "--verify", "se abre y tiene 3 secciones", *D, "--json")
        same((code, data["plan"], data["needs_ok"]), (0, 2, False), "plan in the work area needs no OK")

        # 6 · permissions
        print("6 · permissions")
        code, data, _ = run("permissions", "--platform", "claude-code", *D, "--json")
        perm_file = man / "trabajo" / "permisos-claude-code.json"
        same((code, perm_file.is_file()), (0, True), "permissions written to the work folder")
        perm = json.loads(perm_file.read_text(encoding="utf-8"))
        pm = perm.get("permissions", {})
        same(sorted(perm), expected["permissions"]["top_keys"], "permissions file keys")
        same(sorted(pm), expected["permissions"]["permissions_keys"], "permissions block keys")
        same(all(isinstance(pm[k], list) and all(isinstance(x, str) for x in pm[k]) for k in ("allow", "ask", "deny")),
             True, "allow, ask and deny are lists of strings")
        rule_re = re.compile(r"^(Read|Edit|Bash|PowerShell|WebFetch|WebSearch|mcp__\*)(\(.+\))?$")
        bad = [x for k in ("allow", "ask", "deny") for x in pm[k] if not rule_re.match(x)]
        same(bad, [], "every rule has the Tool(specifier) shape")
        missing = [x for x in expected["permissions"]["deny_includes"] if x not in pm["deny"]]
        same(missing, [], "deny has deletions, network, installs and git push")
        missing = [x for x in expected["permissions"]["ask_includes"] if x not in pm["ask"]]
        same(missing, [], "ask has every MCP tool")
        nv, wr, wk = rule_path(emp / "sueldos"), rule_path(emp / "plan"), rule_path(man / "trabajo")
        same([f"Read({nv}/**)" in pm["deny"], f"Edit({nv}/**)" in pm["deny"], f"Edit({wr}/**)" in pm["ask"],
              f"Edit({wk}/**)" in pm["allow"], f"Read({rule_path(emp)}/**)" in pm["allow"],
              f"Edit({rule_path(emp)}/**)" in pm["deny"]],
             [True, True, True, True, True, False], "path rules: never denied, write asks, work allowed, read allowed")
        same(nv.startswith("//"), True, "absolute paths use the // prefix")
        same(rule_path("C:\\Users\\usuario\\Docs"), "//c/Users/usuario/Docs", "Windows path to //c/...")
        same(rule_path("/home/usuario/Docs"), "//home/usuario/Docs", "POSIX path to //...")
        tpl = template.get("permissions", {})
        same([x for x in COMMAND_DENY if x not in tpl.get("deny", [])], [], "the template denies what the generator denies")
        same(sorted(x for x in ("Edit", "Write") if x in tpl.get("ask", [])), ["Edit", "Write"], "the template asks Edit and Write")

        # 7 · en profile: English names and labels
        print("7 · en")
        D2 = ["--data", str(datos2)]
        code, data, _ = run("backup", str(planilla), *D2, "--json")
        same(data["backup"].split("/")[0] if data else None, "backups", "en backups folder")
        code, data, _ = run("log", "--step", "—", "--file", str(planilla), "--change", "IVA column fixed",
                            "--backup", data["backup"], "--verified", "total 119000 = 100000 × 1.19",
                            "--ok", "owner", *D2, "--json")
        same(data["text"] if data else None, expected["en"]["log_line"], "en logbook line")
        same(len(data["warnings"]) if data else 0, 1, "a scope without ok_by accepts the role and warns")
        same(sorted(p.name for p in man2.iterdir()), expected["en"]["files"], "en manual files")
    finally:
        NOW = saved_now
        os.environ.clear()
        os.environ.update(saved_env)
        set_language(saved_lang)
        # Repo rule 8: remove only what this test created, and only inside the system temp folder.
        tmp_base = pkey(os.path.realpath(tempfile.gettempdir()))
        mine = pkey(os.path.realpath(root))
        if os.environ.get("METHODIC_KEEP_TEMP") == "1":
            notes.append(f"temporary folder kept (METHODIC_KEEP_TEMP=1): {root}")
        elif root.name.startswith("ivn-") and under(mine, tmp_base) and mine != tmp_base:
            shutil.rmtree(root, ignore_errors=True)
        else:
            notes.append(f"temporary folder not removed (outside the system temp folder): {root}")

    print()
    for n in notes:
        print("   note: " + n)
    if failures:
        print("FAIL")
        for f in failures:
            print(f"   [X] {f}")
        return 1
    print("OK · verdicts (with .. and link escapes), the full cycle, backups that never overwrite, refusals "
          "and the permissions file match tests/expected.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
