# -*- coding: utf-8 -*-
"""
interview · understand a business by asking fixed questions in batches of 3 to 4.

    python interview.py next   [--company X] [--data D] [--round N] [--process CODE] [--gaps] [--json]
    python interview.py record (--answers <file.json|-> | --form <file.md>) [--who ROLE] [--process CODE]
    python interview.py status [--json]
    python interview.py form   --round N [--process CODE]
    python interview.py --test

What it does (the model asks and listens; the script decides what to ask and writes it down):

1. `next` picks the next batch from the fixed bank (templates/questions.<lang>.json): the first 3 to 4
   unanswered questions of the lowest open round, respecting each question's `when`. Round 2 repeats
   per process named in round 1.
2. `record` appends one block per batch to today's interview record
   (<data>/manual/<company>/entrevista/AAAA-MM-DD.md, or interview/YYYY-MM-DD.md in English), in the
   format of docs/MANUAL-FORMAT.md. «No sé» / «I don't know» is a gap with its date. Earlier blocks
   are never edited: the file is only appended to.
3. `status` reads every record back: coverage per round, open gaps with dates, processes named.
4. `form` prints a whole round as a fillable markdown form; `record --form` takes it back.

Data folder: --data · $METHODIC_DATA · $INGENIERO_DATOS (legacy) · ../methodic-data ·
../ingeniero-agentico-datos. Company = profile file stem (<data>/profiles/<company>.yaml, then
perfiles/); the profile `language` (es by default) chooses file names and texts.

Standard library only. No network, no subprocess; nothing is deleted.
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
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve()
SKILL = HERE.parents[1]
REPO = HERE.parents[3] if len(HERE.parents) > 3 else SKILL
TEMPLATES = SKILL / "templates"
TESTS = SKILL / "tests"

LANG = "es"   # output language; set from the profile
MAX_BATCH = 4
RECORD_DIRS = {"es": "entrevista", "en": "interview"}
RECORD_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
HEADER_RE = re.compile(r"^## (Tanda|Batch) (\d+) · (.+) · (\d{2}-\d{2}-\d{4}) (\d{2}:\d{2})\s*$")
WHO_RE = re.compile(r"^(Respondió|Answered by): (.*)$")
LINE_RE = re.compile(r"^(\d+)\. (?:\[([a-z]{3}-\d{2})\] )?(.+?) → (.*)$")
GAP_SUFFIXES = (" · HUECO", " · GAP")
CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]*$")
DONT_KNOW_RE = re.compile(r"^(no (lo )?se|no sabe(mos)?|i (don'?t|do not) know|(don'?t|do not) know|unknown)\b")
MAPS_PREFIX = ("index:", "process:", "scope:")


def set_language(lang):
    global LANG
    LANG = "en" if str(lang or "es").strip().lower() == "en" else "es"


def tr(es, en):
    """Pick the text for the output language."""
    return en if LANG == "en" else es


class InputError(Exception):
    """An error that prevents going on. Fix the input and run again."""


def norm(s):
    """Accent- and case-insensitive form, whitespace collapsed (to match texts)."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).casefold()
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- minimal YAML (same subset as procurement)
def _scalar(s):
    s = s.strip()
    if s in ("", "~", "null", "Null", "NULL"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
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
    """The YAML subset profiles use: nested maps, lists and scalars."""
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
                if ":" in rest and not rest.startswith(("\"", "'")):
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
    return data or {}


# ---------------------------------------------------------------- data folder, profile, manual
def resolve_data(arg=None, env=None, repo=None):
    """Return (data folder, profile file or None, where it came from).

    Order: --data · $METHODIC_DATA · $INGENIERO_DATOS (legacy) · ../methodic-data ·
    ../ingeniero-agentico-datos. An environment variable may point at a profile file (legacy)."""
    env = os.environ if env is None else env
    repo = REPO if repo is None else Path(repo)
    if arg:
        return Path(arg), None, "--data"
    for var in ("METHODIC_DATA", "INGENIERO_DATOS"):
        value = env.get(var)
        if not value:
            continue
        p = Path(value)
        if p.is_file():
            parent = p.parent
            data = parent.parent if parent.name in ("profiles", "perfiles") else parent
            return data, p, var
        return p, None, var
    for name in ("methodic-data", "ingeniero-agentico-datos"):
        p = repo.parent / name
        if p.is_dir():
            return p, None, f"../{name}"
    raise InputError(tr("No hay carpeta de datos. Usa --data, o define METHODIC_DATA, o crea ../methodic-data/ "
                        "junto al repo.",
                        "No data folder. Use --data, or set METHODIC_DATA, or create ../methodic-data/ next to "
                        "the repo."))


def profiles_in(data):
    found, seen = [], set()
    for d in (data / "profiles", data / "perfiles"):
        if d.is_dir():
            for p in sorted(d.glob("*.yaml")):
                if not p.name.startswith("_") and p.stem.lower() not in seen:
                    seen.add(p.stem.lower())
                    found.append(p)
    return found


def load_context(data_arg=None, company=None, env=None, repo=None):
    """Resolve data folder, company profile, language, manual folder and question bank."""
    data, profile_file, source = resolve_data(data_arg, env, repo)
    notes = []
    yamls = profiles_in(data)
    path = None
    if company:
        path = next((p for p in yamls if p.stem.lower() == company.lower()), None)
        if path is None and profile_file and profile_file.stem.lower() == company.lower():
            path = profile_file
        if path is None and yamls:
            raise InputError(tr(f"No hay perfil «{company}» en {data}. Hay: {', '.join(p.stem for p in yamls)}",
                                f"No profile «{company}» in {data}. Found: {', '.join(p.stem for p in yamls)}"))
    elif profile_file:
        path = profile_file
    elif len(yamls) == 1:
        path = yamls[0]
    elif len(yamls) > 1:
        raise InputError(tr("Hay varios perfiles; elige uno con --company: ",
                            "There are several profiles; pick one with --company: ")
                         + ", ".join(p.stem for p in yamls))
    else:
        raise InputError(tr(f"No hay perfiles en {data}/profiles/. Crea <empresa>.yaml desde "
                            f"profiles/_template.yaml o pasa --company.",
                            f"No profiles in {data}/profiles/. Create <company>.yaml from "
                            f"profiles/_template.yaml or pass --company."))
    raw = read_yaml(path.read_text(encoding="utf-8-sig")) if path else {}
    lang = raw.get("language") or raw.get("idioma") or "es"
    set_language(lang)
    stem = path.stem if path else company
    comp = raw.get("company") or raw.get("empresa") or {}
    name = (comp.get("name") or comp.get("nombre") or "") if isinstance(comp, dict) else ""
    if not path:
        notes.append(tr(f"SUPUESTO · no hay perfil «{company}»: idioma es por defecto",
                        f"ASSUMPTION · no profile «{company}»: language es by default"))
    return {"data": data, "source": source, "company": stem, "name": name or stem, "language": LANG,
            "profile": path, "manual": data / "manual" / stem, "bank": load_bank(LANG), "notes": notes}


def record_dir(manual, lang):
    """A manual keeps the names it was created with; a new one takes the profile's language."""
    own, other = RECORD_DIRS[lang], RECORD_DIRS["en" if lang == "es" else "es"]
    if (manual / own).is_dir():
        return manual / own
    if (manual / other).is_dir():
        return manual / other
    return manual / own


# ---------------------------------------------------------------- question bank
def bank_problems(bank):
    """Integrity of a bank: what the script relies on."""
    problems = []
    labels = bank.get("labels") or {}
    dk = labels.get("dont_know")
    for k in ("batch", "answered_by", "gap", "dont_know", "other", "round", "process"):
        if not labels.get(k):
            problems.append(f"labels.{k} missing")
    rounds = bank.get("rounds") or {}
    for r in ("1", "2", "3"):
        if not (rounds.get(r) or {}).get("title"):
            problems.append(f"rounds.{r}.title missing")
    seen = {}
    for q in bank.get("questions") or []:
        qid = q.get("id") or "?"
        if qid in seen:
            problems.append(f"{qid}: repeated id")
        if not re.fullmatch(r"[a-z]{3}-\d{2}", qid):
            problems.append(f"{qid}: id must look like abc-01")
        if q.get("round") not in (1, 2, 3):
            problems.append(f"{qid}: round must be 1, 2 or 3")
        if bool(q.get("per_process")) != (q.get("round") == 2):
            problems.append(f"{qid}: per_process must be true exactly in round 2")
        opts = q.get("options") or []
        if not 2 <= len(opts) <= 4:
            problems.append(f"{qid}: 2 to 4 options (AskUserQuestion takes at most 4)")
        if not opts or opts[-1] != dk:
            problems.append(f"{qid}: the last option must be «{dk}»")
        if any("," in o for o in opts):
            problems.append(f"{qid}: an option has a comma (multi answers are joined with commas)")
        if len(q.get("header") or "") > 12 or not q.get("header"):
            problems.append(f"{qid}: header must have 1 to 12 characters")
        if "→" in (q.get("text") or "") or not q.get("text"):
            problems.append(f"{qid}: text missing or contains →")
        maps = q.get("maps_to")
        maps = maps if isinstance(maps, list) else [maps]
        if not maps or not all(isinstance(m, str) and m.startswith(MAPS_PREFIX) for m in maps):
            problems.append(f"{qid}: maps_to must start with index:, process: or scope:")
        w = q.get("when")
        if w:
            dep = seen.get(w.get("id"))
            if not dep:
                problems.append(f"{qid}: when.id must be an earlier question")
            elif dep.get("round") != q.get("round"):
                problems.append(f"{qid}: when.id must be in the same round")
            if not set(w) - {"id"} or set(w) - {"id", "in", "not_in", "known"}:
                problems.append(f"{qid}: when takes in, not_in or known")
        seen[qid] = q
    return problems


def load_bank(lang):
    p = TEMPLATES / f"questions.{lang}.json"
    bank = json.loads(p.read_text(encoding="utf-8"))
    problems = bank_problems(bank)
    if problems:
        raise InputError(f"{p.name}: " + "; ".join(problems))
    bank["by_id"] = {q["id"]: q for q in bank["questions"]}
    return bank


def text_index():
    """Known ids, question text → id (fallback for old lines without id) and round titles → round,
    from both banks: a record is read whatever its language."""
    ids, idx, titles = set(), {}, {}
    for lang in ("es", "en"):
        p = TEMPLATES / f"questions.{lang}.json"
        if not p.is_file():
            continue
        b = json.loads(p.read_text(encoding="utf-8"))
        for q in b["questions"]:
            ids.add(q["id"])
            idx[norm(q["text"])] = q["id"]
        for r, v in b["rounds"].items():
            titles[norm(v["title"])] = int(r)
    return ids, idx, titles


def read_text_any(path):
    """UTF-8 (with or without BOM), or UTF-16 as Windows PowerShell 5.1 writes with «>»."""
    raw = Path(path).read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def is_dont_know(text):
    return bool(DONT_KNOW_RE.match(norm(text)))


# ---------------------------------------------------------------- reading the record
def record_files(manual):
    files = []
    for d in RECORD_DIRS.values():
        folder = manual / d
        if folder.is_dir():
            files += [p for p in folder.iterdir() if p.is_file() and RECORD_FILE_RE.match(p.name)]
    return sorted(files, key=lambda p: (p.name, p.parent.name))


def read_record(manual):
    """Every block of every record file, in order."""
    ids, idx, titles = text_index()
    blocks = []
    for f in record_files(manual):
        cur = None
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            m = HEADER_RE.match(line)
            if m:
                parts = m.group(3).split(" · ")
                title, process = parts[0], (parts[1].strip() if len(parts) > 1 else "")
                cur = {"n": int(m.group(2)), "title": title, "round": titles.get(norm(title)),
                       "process": process, "date": m.group(4), "time": m.group(5), "who": "",
                       "file": f"{f.parent.name}/{f.name}", "answers": [], "unmatched": []}
                blocks.append(cur)
                continue
            if cur is None:
                continue
            m = WHO_RE.match(line)
            if m and not cur["who"]:
                cur["who"] = m.group(2).strip()
                continue
            m = LINE_RE.match(line)
            if m:
                line_id, q, ans = m.group(2), m.group(3).strip(), m.group(4).strip()
                gap = False
                for suf in GAP_SUFFIXES:
                    if ans.endswith(suf):
                        ans, gap = ans[: -len(suf)].strip(), True
                # the id ties the answer to its question; the text is only a fallback for old lines
                qid = line_id if line_id in ids else (None if line_id else idx.get(norm(q)))
                if qid:
                    cur["answers"].append({"id": qid, "question": q, "answer": ans, "gap": gap})
                else:
                    cur["unmatched"].append(q)
    return blocks


def build_state(bank, blocks):
    """Latest answer per (id, process), and the processes named so far."""
    latest = {}
    for b in blocks:
        for a in b["answers"]:
            q = bank["by_id"].get(a["id"])
            if not q:
                continue
            key = (a["id"], b["process"] if q.get("per_process") else "")
            latest[key] = dict(a, round=q["round"], process=key[1], date=b["date"], time=b["time"],
                               who=b["who"], batch=b["n"], file=b["file"], maps_to=q["maps_to"])
    processes = {}
    skip = {norm(bank["labels"]["dont_know"]), norm(bank["labels"].get("none", ""))}
    for want_pain in (True, False):
        for q in bank["questions"]:
            if not q.get("names_processes") or bool(q.get("pain")) != want_pain:
                continue
            a = latest.get((q["id"], ""))
            if not a or a["gap"]:
                continue
            for item in re.split(r"[,;]", a["answer"]):
                item = item.strip()
                if not item or norm(item) in skip or is_dont_know(item):
                    continue
                code, name = process_code(item)
                if any(p["name"].lower() == name.lower() for p in processes.values()):
                    continue
                base, k = code, 2
                while code in processes:
                    code, k = f"{base}-{k}", k + 1
                processes[code] = {"code": code, "name": name, "pain": want_pain, "from": q["id"]}
    for b in blocks:
        if b["process"] and b["process"] not in processes:
            processes[b["process"]] = {"code": b["process"], "name": b["process"], "pain": False, "from": "record"}
    return latest, processes


def process_code(item):
    """«COMPRAS: Comprar material» or «COMPRAS (Comprar material)» keep their code; «Compras» → COMPRAS."""
    m = re.match(r"^([A-Z0-9][A-Z0-9-]*)\s*[:(]\s*(.+?)\)?\s*$", item)
    if m:
        return m.group(1), m.group(2).strip()
    first = norm(item).split(" ")[0]
    code = re.sub(r"[^A-Z0-9]+", "-", first.upper()).strip("-")[:20] or "PROCESO"
    return code, item


# ---------------------------------------------------------------- what to ask next
def applicable(q, process, latest):
    """yes · no (the condition is false) · pending (the question it depends on is unanswered)."""
    w = q.get("when")
    if not w:
        return "yes"
    dep = latest.get((w["id"], process if q.get("per_process") else ""))
    if dep is None:
        return "pending"
    ans = norm(dep["answer"])
    if w.get("known") and dep["gap"]:
        return "no"
    if "in" in w and (dep["gap"] or not any(norm(x) in ans for x in w["in"])):
        return "no"
    if "not_in" in w and any(norm(x) in ans for x in w["not_in"]):
        return "no"
    return "yes"


def round_questions(bank, rnd):
    return [q for q in bank["questions"] if q["round"] == rnd]


def candidates(bank, latest, rnd, process="", gaps=False):
    out = []
    for q in round_questions(bank, rnd):
        key = (q["id"], process if q.get("per_process") else "")
        a = latest.get(key)
        if gaps:
            if a and a["gap"] and applicable(q, process, latest) != "no":
                out.append(q)
        elif a is None and applicable(q, process, latest) == "yes":
            out.append(q)
    return out


def coverage(bank, latest, rnd, process=""):
    qs = round_questions(bank, rnd)
    answered = no = 0
    for q in qs:
        key = (q["id"], process if q.get("per_process") else "")
        if key in latest:
            answered += 1
        elif applicable(q, process, latest) == "no":
            no += 1
    return {"answered": answered, "applicable": len(qs) - no, "not_applicable": no,
            "pending": len(qs) - no - answered}


def pick_next(bank, latest, processes, rnd=None, process=None, gaps=False):
    """Return (round, process, questions) of the next batch, or (None, None, []) when nothing is left."""
    if process and not rnd:
        rnd = 2
    rounds = [rnd] if rnd else [1, 2, 3]
    for r in rounds:
        if r == 2:
            codes = [process] if process else list(processes)
            for code in codes:
                qs = candidates(bank, latest, 2, code, gaps)
                if qs:
                    return 2, code, qs[:MAX_BATCH]
            continue
        qs = candidates(bank, latest, r, "", gaps)
        if qs:
            return r, "", qs[:MAX_BATCH]
    return None, None, []


# ---------------------------------------------------------------- commands
def cmd_next(ctx, rnd=None, process=None, gaps=False, as_json=False):
    bank = ctx["bank"]
    blocks = read_record(ctx["manual"])
    latest, processes = build_state(bank, blocks)
    if process:
        process = check_code(process)
    if rnd == 2 and not process and not processes:
        raise InputError(tr("Ronda 2 sin procesos nombrados: responde neg-08 o usa --process CODIGO.",
                            "Round 2 with no process named: answer neg-08 or use --process CODE."))
    r, code, qs = pick_next(bank, latest, processes, rnd, process, gaps)
    if not qs:
        msg = (tr("No quedan huecos por volver a preguntar.", "No gaps left to ask again.") if gaps else
               tr("Entrevista completa para lo pedido. Sigue la skill manual (escribe las páginas).",
                  "Interview complete for what was asked. Next: the manual skill (it writes the pages)."))
        if as_json:
            print(json.dumps({"done": True, "message": msg}, ensure_ascii=False, separators=(",", ":")))
        else:
            print(msg)
        return 0
    title = bank["rounds"][str(r)]["title"]
    pname = processes.get(code, {}).get("name", code) if code else ""
    left = len(candidates(bank, latest, r, code, gaps))
    out = {"company": ctx["name"], "batch": len(blocks) + 1, "round": r, "title": title,
           "process": code or None, "process_name": pname or None, "left_in_round": left,
           "questions": [{"id": q["id"], "header": q["header"], "text": q["text"], "options": q["options"],
                          "multi": bool(q.get("multi")), "free": bool(q.get("free"))} for q in qs]}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
        return 0
    head = f"{ctx['name']} · {bank['labels']['batch']} {out['batch']} · {title}"
    if code:
        head += f" · {code}" + (f" ({pname})" if pname and pname != code else "")
    print(head)
    for q in qs:
        extra = tr(" (varias)", " (several)") if q.get("multi") else ""
        print(f"[{q['id']}] {q['text']}{extra}")
        opts = " · ".join(f"{i}) {o}" for i, o in enumerate(q["options"], 1))
        print(f"   {opts} · {tr('u otra respuesta', 'or another answer')}")
    print(tr(f"Registrar: interview.py record --answers <respuestas.json|-> --who <rol>"
             + (f" (proceso {code})" if code else ""),
             f"Record: interview.py record --answers <answers.json|-> --who <role>"
             + (f" (process {code})" if code else "")))
    for n in ctx["notes"]:
        print(n)
    return 0


def check_code(code):
    code = str(code).strip().upper()
    if not CODE_RE.match(code):
        raise InputError(tr(f"Código de proceso «{code}» no válido: mayúsculas, dígitos y «-».",
                            f"Invalid process code «{code}»: uppercase letters, digits and «-»."))
    return code


def answer_text(v):
    if isinstance(v, list):
        v = ", ".join(str(x).strip() for x in v if str(x).strip())
    v = re.sub(r"\s*[\r\n]+\s*", " / ", str(v if v is not None else "")).strip()
    return v


def parse_answers_json(raw):
    """Accepts {round, process, who, answers: {id: answer} | [{id, answer, gap}]} or a plain {id: answer}."""
    aliases = {"ronda": "round", "proceso": "process", "quien": "who", "respondio": "who",
               "respuestas": "answers", "respuesta": "answer", "hueco": "gap"}
    if isinstance(raw, dict):
        raw = {aliases.get(k, k): v for k, v in raw.items()}
    else:
        raise InputError(tr("La entrada debe ser un objeto JSON.", "The input must be a JSON object."))
    answers = raw.get("answers")
    if answers is None:
        answers = {k: v for k, v in raw.items() if re.fullmatch(r"[a-z]{3}-\d{2}", k)}
    items = []
    if isinstance(answers, dict):
        items = [{"id": k, "answer": v, "gap": False} for k, v in answers.items()]
    elif isinstance(answers, list):
        for a in answers:
            a = {aliases.get(k, k): v for k, v in (a or {}).items()}
            items.append({"id": a.get("id"), "answer": a.get("answer"), "gap": bool(a.get("gap"))})
    return {"round": raw.get("round"), "process": raw.get("process"), "who": raw.get("who"), "answers": items}


def parse_form(text):
    """A filled form back to {round, process, who, answers}."""
    rnd, process, who, items, cur = None, None, None, [], None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^#\s.*\b(Ronda|Round) (\d)\b", s)
        if m and rnd is None:
            rnd = int(m.group(2))
            continue
        m = re.match(r"^(Proceso|Process):\s*(.*)$", s)
        if m and cur is None:
            process = m.group(2).strip() or None
            continue
        m = re.match(r"^(Respondió|Answered by):\s*(.*)$", s)
        if m and cur is None:
            who = m.group(2).strip() or None
            continue
        m = re.match(r"^##\s+([a-z]{3}-\d{2})\b", s)
        if m:
            cur = {"id": m.group(1), "picked": [], "other": ""}
            items.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^- \[[xX]\]\s*(.+?)\s*$", s)
        if m:
            cur["picked"].append(m.group(1))
            continue
        m = re.match(r"^(Otra respuesta|Other answer):\s*(.*)$", s)
        if m:
            cur["other"] = m.group(2).strip()
    answers = [{"id": c["id"], "answer": c["picked"] + ([c["other"]] if c["other"] else []), "gap": False}
               for c in items if c["picked"] or c["other"]]
    return {"round": rnd, "process": process, "who": who, "answers": answers}


def cmd_record(ctx, answers_src=None, form_src=None, who=None, process=None, now=None):
    bank = ctx["bank"]
    labels = bank["labels"]
    if bool(answers_src) == bool(form_src):
        raise InputError(tr("Usa --answers <archivo.json|-> o --form <archivo.md> (uno de los dos).",
                            "Use --answers <file.json|-> or --form <file.md> (one of them)."))
    if form_src:
        payload = parse_form(read_text_any(form_src))
    else:
        if answers_src == "-":
            stdin = getattr(sys.stdin, "buffer", None)
            text = stdin.read().decode("utf-8-sig") if stdin else sys.stdin.read().lstrip(chr(0xFEFF))
        else:
            text = read_text_any(answers_src)
        try:
            payload = parse_answers_json(json.loads(text))
        except json.JSONDecodeError as e:
            raise InputError(tr(f"JSON no válido: {e}", f"Invalid JSON: {e}"))
    items = payload["answers"]
    if not items:
        raise InputError(tr("No hay respuestas que registrar.", "There are no answers to record."))
    if answers_src and len(items) > MAX_BATCH:
        raise InputError(tr(f"Una tanda tiene a lo más {MAX_BATCH} preguntas; vinieron {len(items)}. "
                            f"Para una ronda completa usa form y --form.",
                            f"A batch has at most {MAX_BATCH} questions; got {len(items)}. "
                            f"For a whole round use form and --form."))
    qs = []
    for a in items:
        q = bank["by_id"].get(a["id"])
        if not q:
            raise InputError(tr(f"Pregunta «{a['id']}» no existe en el banco.",
                                f"Question «{a['id']}» is not in the bank."))
        qs.append(q)
    rounds = {q["round"] for q in qs}
    if len(rounds) > 1:
        raise InputError(tr("Una tanda es de una sola ronda; vinieron preguntas de las rondas "
                            + ", ".join(map(str, sorted(rounds))),
                            "A batch belongs to one round; got questions of rounds "
                            + ", ".join(map(str, sorted(rounds)))))
    rnd = rounds.pop()
    if payload.get("round") not in (None, "", rnd):
        raise InputError(tr(f"La entrada dice ronda {payload['round']} pero las preguntas son de la ronda {rnd}.",
                            f"The input says round {payload['round']} but the questions are of round {rnd}."))
    code = process or payload.get("process") or ""
    if rnd == 2:
        if not code:
            raise InputError(tr("Ronda 2: falta el proceso (--process CODIGO o «process» en la entrada).",
                                "Round 2: the process is missing (--process CODE or «process» in the input)."))
        code = check_code(code)
    else:
        code = ""
    who = (who or payload.get("who") or "").strip()
    if not who:
        raise InputError(tr("Falta quién respondió (--who <rol>): el manual cita «entrevista · <rol> · fecha».",
                            "Who answered is missing (--who <role>): the manual cites «interview · <role> · date»."))
    who = re.sub(r"\s+", " ", who)
    now = now or datetime.now()
    blocks = read_record(ctx["manual"])
    n = len(blocks) + 1
    title = bank["rounds"][str(rnd)]["title"]
    header = f"## {labels['batch']} {n} · {title}" + (f" · {code}" if code else "") + f" · {now:%d-%m-%Y %H:%M}"
    lines, gaps = [header, f"{labels['answered_by']}: {who}", ""], 0
    for i, (a, q) in enumerate(zip(items, qs), 1):
        text = answer_text(a["answer"])
        if not text:
            raise InputError(tr(f"{q['id']}: respuesta vacía. Si no lo sabe, la respuesta es «{labels['dont_know']}».",
                                f"{q['id']}: empty answer. If it is not known, the answer is «{labels['dont_know']}»."))
        gap = a["gap"] or is_dont_know(text)
        if gap:
            gaps += 1
            text = f"{text} · {labels['gap']}"
        lines.append(f"{i}. [{q['id']}] {q['text']} → {text}")
    folder = record_dir(ctx["manual"], ctx["language"])
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{now:%Y-%m-%d}.md"
    sep = "\n" if dest.is_file() and dest.stat().st_size > 0 else ""
    with open(dest, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(sep + "\n".join(lines) + "\n")
    rel = f"{folder.name}/{dest.name}"
    print(tr(f"{labels['batch']} {n} registrada en {rel} · {len(items)} respuesta(s) · {gaps} hueco(s)",
             f"{labels['batch']} {n} recorded in {rel} · {len(items)} answer(s) · {gaps} gap(s)"))
    for nline in ctx["notes"]:
        print(nline)
    return 0


def collect_status(ctx):
    bank = ctx["bank"]
    blocks = read_record(ctx["manual"])
    latest, processes = build_state(bank, blocks)
    rounds = {"1": coverage(bank, latest, 1), "3": coverage(bank, latest, 3),
              "2": {code: coverage(bank, latest, 2, code) for code in processes}}
    order = sorted(latest.values(), key=lambda a: (a["batch"], a["id"]))
    gaps = [{"id": a["id"], "round": a["round"], "process": a["process"] or None, "question": a["question"],
             "date": a["date"], "who": a["who"], "batch": a["batch"]} for a in order if a["gap"]]
    answers = [{"id": a["id"], "round": a["round"], "process": a["process"] or None, "maps_to": a["maps_to"],
                "question": a["question"], "answer": a["answer"], "gap": a["gap"], "who": a["who"],
                "date": a["date"], "batch": a["batch"], "file": a["file"]} for a in order]
    unmatched = [{"batch": b["n"], "question": q} for b in blocks for q in b["unmatched"]]
    r, code, qs = pick_next(bank, latest, processes)
    return {"company": ctx["name"], "language": ctx["language"], "batches": len(blocks),
            "last": f"{blocks[-1]['date']} {blocks[-1]['time']}" if blocks else None,
            "rounds": rounds, "gaps": gaps, "processes": list(processes.values()),
            "next": {"round": r, "process": code or None, "ids": [q["id"] for q in qs]},
            "unmatched": unmatched, "answers": answers}


def cmd_status(ctx, as_json=False):
    st = collect_status(ctx)
    if as_json:
        print(json.dumps(st, ensure_ascii=False, separators=(",", ":")))
        return 0
    bank = ctx["bank"]
    t = {k: bank["rounds"][k]["title"] for k in ("1", "2", "3")}
    rl = bank["labels"]["round"]

    def cov(c):
        s = f"{c['answered']}/{c['applicable']}"
        if c["not_applicable"]:
            s += tr(f" ({c['not_applicable']} no aplica)", f" ({c['not_applicable']} not applicable)")
        return s

    print(f"{st['company']} · {tr('entrevista', 'interview')} · {st['batches']} "
          + tr("tanda(s)", "batch(es)") + (f" · {tr('última', 'last')} {st['last']}" if st["last"] else ""))
    print(f"{rl} 1 · {t['1']}: {cov(st['rounds']['1'])}")
    if st["processes"]:
        print(f"{rl} 2 · {t['2']}:")
        for p in st["processes"]:
            pain = tr(" · duele", " · hurts") if p["pain"] else ""
            print(f"   {p['code']} ({p['name']}){pain}: {cov(st['rounds']['2'][p['code']])}")
    else:
        print(f"{rl} 2 · {t['2']}: " + tr("sin procesos nombrados", "no process named"))
    print(f"{rl} 3 · {t['3']}: {cov(st['rounds']['3'])}")
    print(tr(f"Huecos abiertos ({len(st['gaps'])}):", f"Open gaps ({len(st['gaps'])}):"))
    for g in st["gaps"]:
        where = f" [{g['process']}]" if g["process"] else ""
        print(f"   - {g['id']}{where} · {g['question']} · " + tr(f"declarado el {g['date']}", f"declared on {g['date']}"))
    if st["unmatched"]:
        print(tr(f"AVISO · {len(st['unmatched'])} línea(s) del registro no calzan con el banco "
                 f"(un id que no existe, o una línea antigua sin id cuyo texto cambió)",
                 f"WARNING · {len(st['unmatched'])} record line(s) do not match the bank "
                 f"(an unknown id, or an old line without id whose text changed)"))
    nx = st["next"]
    if nx["ids"]:
        print(tr("Siguiente: ", "Next: ") + f"{rl} {nx['round']}"
              + (f" · {nx['process']}" if nx["process"] else "") + " · " + ", ".join(nx["ids"]))
    else:
        print(tr("Siguiente: nada por preguntar; pasa a la skill manual.",
                 "Next: nothing left to ask; go to the manual skill."))
    return 0


def cmd_form(ctx, rnd, process=None):
    bank = ctx["bank"]
    L = bank["labels"]
    if rnd not in (1, 2, 3):
        raise InputError(tr("--round debe ser 1, 2 o 3.", "--round must be 1, 2 or 3."))
    code = ""
    if rnd == 2:
        if process:
            code = check_code(process)
        else:
            latest, processes = build_state(bank, read_record(ctx["manual"]))
            code = next((c for c in processes if candidates(bank, latest, 2, c)), next(iter(processes), ""))
    out = [f"# {L['form_title']} · {L['round']} {rnd} · {bank['rounds'][str(rnd)]['title']}",
           f"{L['company']}: {ctx['name']}"]
    if rnd == 2:
        out.append(f"{L['process']}: {code}")
    out += [f"{L['answered_by']}: ", "", L["form_help"], ""]
    for q in round_questions(bank, rnd):
        out.append(f"## {q['id']} · {q['header']}")
        cond = f" ({L['only_if']} {q['when']['id']})" if q.get("when") else ""
        out.append(q["text"] + (f" {L['multi_hint']}" if q.get("multi") else "") + cond)
        out += [f"- [ ] {o}" for o in q["options"]]
        out += [f"{L['other']}: ", ""]
    print("\n".join(out).rstrip() + "\n")
    return 0


# ---------------------------------------------------------------- test
def run_test():
    failures = []

    def same(got, exp, what):
        if got != exp:
            failures.append(f"{what}: got {got!r}, expected {exp!r}")

    def call(args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(args)
        return rc, buf.getvalue()

    expected = json.loads((TESTS / "expected.json").read_text(encoding="utf-8"))

    # 0 · both banks are sound and say the same thing in two languages
    banks = {}
    for lang in ("es", "en"):
        b = json.loads((TEMPLATES / f"questions.{lang}.json").read_text(encoding="utf-8"))
        for p in bank_problems(b):
            failures.append(f"[bank {lang}] {p}")
        banks[lang] = b
    shape = lambda b: [(q["id"], q["round"], bool(q.get("per_process")), json.dumps(q["maps_to"]),  # noqa: E731
                        (q.get("when") or {}).get("id"), len(q["options"]), bool(q.get("multi")),
                        bool(q.get("names_processes"))) for q in b["questions"]]
    same(shape(banks["en"]), shape(banks["es"]), "es and en banks have the same questions")
    count = {r: sum(1 for q in banks["es"]["questions"] if q["round"] == r) for r in (1, 2, 3)}
    same(count, {int(k): v for k, v in expected["questions_per_round"].items()}, "questions per round")
    for s, gap in (("No sé", True), ("no se, lo ve el contador", True), ("I don't know", True),
                   ("No sería posible", False), ("Nosotros", False)):
        same(is_dont_know(s), gap, f"is_dont_know({s!r})")

    tmp = Path(tempfile.mkdtemp(prefix="iv-"))
    try:
        # 1 · data folder resolution order
        a, b, c = tmp / "a", tmp / "b", tmp / "c"
        for d in (a, b, c):
            d.mkdir()
        same(resolve_data(str(c), {"METHODIC_DATA": str(a), "INGENIERO_DATOS": str(b)}, tmp / "r0" / "repo")[0],
             c, "--data wins")
        same(resolve_data(None, {"METHODIC_DATA": str(a), "INGENIERO_DATOS": str(b)}, tmp / "r0" / "repo")[0],
             a, "METHODIC_DATA before INGENIERO_DATOS")
        same(resolve_data(None, {"INGENIERO_DATOS": str(b)}, tmp / "r0" / "repo")[0], b, "INGENIERO_DATOS (legacy)")
        for sub in ("methodic-data", "ingeniero-agentico-datos"):
            (tmp / "r1" / sub).mkdir(parents=True)
        (tmp / "r2" / "ingeniero-agentico-datos").mkdir(parents=True)
        same(resolve_data(None, {}, tmp / "r1" / "repo")[0].name, "methodic-data", "sibling ../methodic-data")
        same(resolve_data(None, {}, tmp / "r2" / "repo")[0].name, "ingeniero-agentico-datos", "legacy sibling")
        try:
            resolve_data(None, {}, tmp / "r3" / "repo")
            failures.append("no data folder did not stop")
        except InputError:
            pass

        # 2 · Ferretería Andes, es: two batches with a «No sé»
        data = tmp / "d"
        (data / "profiles").mkdir(parents=True)
        (data / "profiles" / "ferreteria-andes.yaml").write_text(
            "language: es\ncompany:\n  name: Ferretería Andes\n  currency: CLP\n", encoding="utf-8")
        base = ["--data", str(data)]
        ex = expected["next"]

        def next_ids(*extra):
            rc, out = call(["next", *base, "--json", *extra])
            got = json.loads(out)
            return got.get("process"), [q["id"] for q in got.get("questions", [])]

        same(next_ids()[1], ex["start"], "first batch")
        rc, _ = call(["record", *base, "--answers", str(TESTS / "batch-1.json")])
        same(rc, 0, "record batch 1")
        rec_dir = data / "manual" / "ferreteria-andes" / expected["record_dir"]
        files = sorted(rec_dir.glob("*.md")) if rec_dir.is_dir() else []
        same(len(files), 1, "one record file for today")
        before = files[0].read_text(encoding="utf-8") if files else ""
        same(next_ids()[1], ex["after_batch_1"], "second batch")
        rc, _ = call(["record", *base, "--answers", str(TESTS / "batch-2.json"), "--who", "vendedor"])
        same(rc, 0, "record batch 2")
        after = files[0].read_text(encoding="utf-8") if files else ""
        if not after.startswith(before) or len(after) <= len(before):
            failures.append("the second batch did not append (an earlier block changed)")
        same(next_ids()[1], ex["after_batch_2"], "third batch skips neg-09 (when is false)")
        same(list(next_ids("--round", "2")), [ex["round_2"]["process"], ex["round_2"]["ids"]], "round 2 batch")
        same(list(next_ids("--gaps")), [None, ex["gaps"]], "gaps asked again")

        # the record file, block by block (structure, not timestamps)
        if "\r" in after or after.startswith(chr(0xFEFF)):
            failures.append("record file must be UTF-8 without BOM and LF line ends")
        got_blocks, cur = [], None
        for line in after.splitlines():
            m = HEADER_RE.match(line)
            if m:
                cur = {"header": line[: line.rfind(" · ")], "who": "", "lines": []}
                got_blocks.append(cur)
            elif cur is not None and WHO_RE.match(line):
                cur["who"] = line
            elif cur is not None and LINE_RE.match(line):
                cur["lines"].append(line)
        same(got_blocks, expected["blocks"], "record blocks")

        # status
        rc, out = call(["status", *base, "--json"])
        st = json.loads(out)
        es = expected["status"]
        same(st["batches"], es["batches"], "status batches")
        same(st["rounds"]["1"], es["round_1"], "status round 1 coverage")
        same([g["id"] for g in st["gaps"]], es["gaps"], "status gaps")
        same([{k: p[k] for k in ("code", "name", "pain")} for p in st["processes"]], es["processes"],
             "status processes")
        same(all(g["date"] == st["gaps"][0]["date"] for g in st["gaps"]) and bool(re.fullmatch(
            r"\d{2}-\d{2}-\d{4}", st["gaps"][0]["date"] if st["gaps"] else "")), True, "gap carries its date")
        rc, out = call(["status", *base])
        for frag in expected["status_text_contains"]:
            if frag not in out:
                failures.append(f"status text lacks «{frag}»")

        # 3 · the form: round 3 printed, filled and recorded back
        rc, form = call(["form", *base, "--round", "3"])
        ids_in_form = re.findall(r"(?m)^## ([a-z]{3}-\d{2})", form)
        same(ids_in_form, [q["id"] for q in banks["es"]["questions"] if q["round"] == 3], "form has the round")
        fill = expected["form_round_3"]["fill"]
        lines, cur = [], None
        for line in form.splitlines():
            m = re.match(r"^## ([a-z]{3}-\d{2})", line)
            if m:
                cur = m.group(1)
            if line.startswith("Respondió:"):
                line = "Respondió: dueña"
            spec = fill.get(cur or "", {})
            if line.startswith("- [ ] ") and line[6:] in spec.get("tick", []):
                line = "- [x] " + line[6:]
            if line.startswith("Otra respuesta:") and spec.get("other"):
                line = "Otra respuesta: " + spec["other"]
            lines.append(line)
        # written as UTF-16, the way Windows PowerShell 5.1 saves «form ... > file.md»
        (tmp / "form3.md").write_text("\n".join(lines) + "\n", encoding="utf-16")
        rc, _ = call(["record", *base, "--form", str(tmp / "form3.md")])
        same(rc, 0, "record the filled form")
        txt = files[0].read_text(encoding="utf-8") if files else ""
        block3 = txt[txt.rfind("\n## ") + 1:].splitlines() or [""]
        same(block3[0][: block3[0].rfind(" · ")], expected["form_round_3"]["header"], "form block header")
        same(sum(1 for ln in block3 if LINE_RE.match(ln)), expected["form_round_3"]["answered"],
             "form answers recorded")
        rc, out = call(["status", *base, "--json"])
        st = json.loads(out)
        same(st["rounds"]["3"]["answered"], expected["form_round_3"]["answered"], "round 3 coverage after form")
        same(len(st["gaps"]), expected["form_round_3"]["gaps_total"], "gaps after form")

        # 4 · what record refuses
        bad = tmp / "bad.json"
        for payload, what in (({"who": "x", "answers": {"neg-01": "a", "neg-02": "b", "neg-03": "c",
                                                        "neg-04": "d", "neg-05": "e"}}, "five answers"),
                              ({"who": "x", "answers": {"zzz-99": "a"}}, "unknown id"),
                              ({"who": "x", "answers": {"pro-01": "a"}}, "round 2 without process"),
                              ({"answers": {"neg-10": "a"}}, "no who"),
                              ({"who": "x", "answers": {"neg-10": " "}}, "empty answer")):
            bad.write_text(json.dumps(payload), encoding="utf-8")
            rc, _ = call(["record", *base, "--answers", str(bad)])
            same(rc, 2, f"record refuses {what}")

        # 5 · English profile: interview/ folder, Batch, GAP
        data_en = tmp / "e"
        (data_en / "profiles").mkdir(parents=True)
        (data_en / "profiles" / "ferreteria-andes.yaml").write_text(
            "language: en\ncompany:\n  name: Ferretería Andes\n", encoding="utf-8")
        (tmp / "en.json").write_text(json.dumps({"who": "owner", "answers": {
            "neg-01": ["Products it buys and resells"], "neg-02": "I don't know"}}), encoding="utf-8")
        rc, _ = call(["record", "--data", str(data_en), "--answers", str(tmp / "en.json")])
        same(rc, 0, "record in English")
        en_files = sorted((data_en / "manual" / "ferreteria-andes" / expected["en"]["record_dir"]).glob("*.md"))
        en_txt = en_files[0].read_text(encoding="utf-8") if en_files else ""
        first = en_txt.splitlines()[:2] if en_txt else ["", ""]
        same(first[0][: first[0].rfind(" · ")], expected["en"]["header"], "English header")
        same(first[1], expected["en"]["who"], "English answered by")
        if not any(ln.endswith(expected["en"]["gap_suffix"]) for ln in en_txt.splitlines()):
            failures.append("English gap line not found")
        rc, out = call(["status", "--data", str(data_en), "--json"])
        same([g["id"] for g in json.loads(out)["gaps"]], ["neg-02"], "English gaps")

        # 6 · the id ties a line to its question; the text is only a fallback for lines without id
        old = tmp / "o" / "entrevista"
        old.mkdir(parents=True)
        (old / "2026-01-05.md").write_text(
            "## Tanda 1 · El negocio · 05-01-2026 10:00\nRespondió: dueña\n\n"
            "1. [neg-01] Una redacción antigua de la pregunta → Servicios u obras\n"
            "2. ¿En qué tipo de negocio está? → Taller o fábrica\n"
            "3. Una pregunta que ya no existe → algo\n"
            "4. [zzz-99] ¿En qué tipo de negocio está? → otra cosa\n", encoding="utf-8")
        blk = read_record(tmp / "o")
        same([a["id"] for a in blk[0]["answers"]], ["neg-01", "neg-02"], "lines mapped by id, then by text")
        same(len(blk[0]["unmatched"]), 2, "unknown id and unknown text are unmatched")
    finally:
        if tmp.name.startswith("iv-") and Path(tempfile.gettempdir()) in tmp.parents:
            shutil.rmtree(tmp, ignore_errors=True)

    print("Bank: " + " · ".join(f"round {r}: {n} questions" for r, n in count.items())
          + " (round 2 repeats per process)")
    if failures:
        print("FAIL")
        for f in failures:
            print(f"   [X] {f}")
        return 1
    print("OK · Ferretería Andes: two batches with a «No sé» match tests/expected.json, the form round-trips, "
          "record refuses five bad inputs, English writes interview/ with GAP")
    return 0


# ---------------------------------------------------------------- main
def main(argv=None):
    hide = argparse.SUPPRESS
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", help="data folder (else METHODIC_DATA, INGENIERO_DATOS, ../methodic-data)")
    common.add_argument("--datos", dest="data", help=hide)
    common.add_argument("--company", help="profile name (file stem) when there are several")
    common.add_argument("--empresa", dest="company", help=hide)
    ap = argparse.ArgumentParser(description="Understand a business by asking fixed questions in batches.")
    ap.add_argument("--test", action="store_true", help="run the fictitious case (Ferretería Andes)")
    ap.add_argument("--probar", dest="test", action="store_true", help=hide)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("next", aliases=["siguiente"], parents=[common], help="print the next batch")
    p.add_argument("--round", "--ronda", dest="round", type=int, choices=(1, 2, 3))
    p.add_argument("--process", "--proceso", dest="process")
    p.add_argument("--gaps", "--huecos", dest="gaps", action="store_true", help="ask the gaps again")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("record", aliases=["registrar"], parents=[common], help="append a batch to the record")
    p.add_argument("--answers", "--respuestas", dest="answers", help="answers JSON file, or - for stdin")
    p.add_argument("--form", "--formulario", dest="form", help="a filled form (from the form command)")
    p.add_argument("--who", "--quien", dest="who", help="role of who answered (never a real name in the repo)")
    p.add_argument("--process", "--proceso", dest="process")
    p = sub.add_parser("status", aliases=["estado"], parents=[common], help="coverage, gaps and processes")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("form", aliases=["formulario"], parents=[common], help="print a round as a form")
    p.add_argument("--round", "--ronda", dest="round", type=int, required=True, choices=(1, 2, 3))
    p.add_argument("--process", "--proceso", dest="process")
    a = ap.parse_args(argv)
    try:
        if a.test:
            return run_test()
        if not a.cmd:
            ap.print_help()
            return 1
        ctx = load_context(a.data, a.company)
        if a.cmd in ("next", "siguiente"):
            return cmd_next(ctx, a.round, a.process, a.gaps, a.json)
        if a.cmd in ("record", "registrar"):
            return cmd_record(ctx, a.answers, a.form, a.who, a.process)
        if a.cmd in ("status", "estado"):
            return cmd_status(ctx, a.json)
        return cmd_form(ctx, a.round, a.process)
    except InputError as e:
        print(tr("ERROR · no se registró nada:", "ERROR · nothing was recorded:"))
        for line in str(e).splitlines():
            print(f"   [X] {line}")
        return 2


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stdin):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")
    sys.exit(main())
