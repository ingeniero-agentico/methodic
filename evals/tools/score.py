"""Precision and recall per skill from a `claude plugin eval` result.

    python evals/tools/score.py                         # latest evals/results/<timestamp>/
    python evals/tools/score.py path/to/aggregate-result.json
    python evals/tools/score.py results.json --md out.md

Reads the graders written by build_cases.py, run by run (with-arm only):

- `fires-<skill>` passed = true positive · failed = false negative
- `silent-<skill>` failed = false positive · passed = true negative

precision = TP / (TP + FP) · recall = TP / (TP + FN). A run that ended on an API error has no
grader results; it is counted apart as `ungraded`, never as a miss.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

EVALS = Path(__file__).resolve().parent.parent


def find_result(arg: str | None) -> Path:
    if arg:
        p = Path(arg)
        return p / "aggregate-result.json" if p.is_dir() else p
    runs = sorted((EVALS / "results").glob("*/aggregate-result.json"))
    if not runs:
        sys.exit("No results found under evals/results/. Pass the path to aggregate-result.json.")
    return runs[-1]


def pct(a: int, b: int) -> str:
    return "n/a" if b == 0 else f"{a / b:.0%}"


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    md_out = None
    if "--md" in sys.argv:
        md_out = Path(sys.argv[sys.argv.index("--md") + 1])
        args = [a for a in args if Path(a) != md_out]
    path = find_result(args[0] if args else None)
    data = json.loads(path.read_text(encoding="utf-8"))

    stats = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0, "tn": 0})
    by_lang = defaultdict(lambda: {"tp": 0, "fn": 0})
    misses = defaultdict(list)     # skill -> cases where it should have fired and did not
    intrusions = defaultdict(list) # skill -> cases where it fired and should not
    ungraded = 0

    for case in data.get("cases", []):
        name = case["name"]
        lang = "es" if "-es-" in name else "en" if "-en-" in name else "?"
        for run in case.get("arms", {}).get("with", []):
            graders = run.get("graders") or []
            if not graders:
                ungraded += 1
                continue
            fired_wrong = [g["name"][len("silent-"):] for g in graders
                           if g.get("name", "").startswith("silent-") and not g.get("passed")]
            for g in graders:
                gname, ok = g.get("name", ""), bool(g.get("passed"))
                if gname.startswith("fires-"):
                    skill = gname[len("fires-"):]
                    stats[skill]["tp" if ok else "fn"] += 1
                    by_lang[(skill, lang)]["tp" if ok else "fn"] += 1
                    if not ok:
                        instead = ", ".join(fired_wrong) or "none"
                        misses[skill].append(f"{name} (fired instead: {instead})")
                elif gname.startswith("silent-"):
                    skill = gname[len("silent-"):]
                    stats[skill]["tn" if ok else "fp"] += 1
                    if not ok:
                        intrusions[skill].append(name)

    lines = [f"# Trigger results · {path}", "",
             f"Model under test: {data.get('suite', {}).get('model', 'default')} · "
             f"Claude Code {data.get('claudeVersion', '?')} · cost ${data.get('costUsd', 0):.2f}"
             + (f" · PARTIAL ({data.get('partialReason')})" if data.get("partial") else ""), "",
             "| Skill | TP | FN | FP | TN | Precision | Recall | Recall es | Recall en |",
             "|---|---|---|---|---|---|---|---|---|"]
    for skill in sorted(stats):
        s = stats[skill]
        es, en = by_lang[(skill, "es")], by_lang[(skill, "en")]
        lines.append(f"| {skill} | {s['tp']} | {s['fn']} | {s['fp']} | {s['tn']} | "
                     f"{pct(s['tp'], s['tp'] + s['fp'])} | {pct(s['tp'], s['tp'] + s['fn'])} | "
                     f"{pct(es['tp'], es['tp'] + es['fn'])} | {pct(en['tp'], en['tp'] + en['fn'])} |")
    lines += ["", f"Ungraded runs (API error, no grader results): {ungraded}", ""]
    for skill in sorted(set(misses) | set(intrusions)):
        lines.append(f"## {skill}")
        for m in misses.get(skill, []):
            lines.append(f"- missed: {m}")
        for i in intrusions.get(skill, []):
            lines.append(f"- fired where it should not: {i}")
        lines.append("")
    text = "\n".join(lines)
    print(text)
    if md_out:
        md_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
