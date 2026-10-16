"""Build the trigger suite for `claude plugin eval` from tools/cases.json.

    python evals/tools/build_cases.py          # rewrite every case folder
    python evals/tools/build_cases.py --check  # only validate cases.json, write nothing

Each case gets one grader per skill of the plugin, all of type `tool_used` on the Skill tool
(free: no judge model):

- `fires-<skill>`: the expected skill was invoked at least once (weight 7, so a miss costs half
  the case score instead of 1/8).
- `silent-<skill>`: that skill was never invoked (min 0, max 0).

A case that expects `orchestrate` only gets `fires-orchestrate`: orchestrate may legitimately
load the other skills of its chain afterwards, so silence is not required there.

The skill folders of evals/ (one per skill) are fully generated: this script deletes and
rewrites them. Edit cases.json, never the generated files.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVALS = HERE.parent
SOURCE = HERE / "cases.json"

FRONTMATTER = """---
name: {name}
description: {description}
tags: {tags}
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: {expected}
---

{prompt}
"""

GRADER = """---
type: tool_used
tool: Skill
input_match: '{pattern}'
min: {min}
{max_line}weight: {weight}
---
"""


def pattern_for(aliases: list[str]) -> str:
    # Matches {"skill": "procurement"} and any namespaced form: {"skill": "methodic:procurement"} and the
    # legacy {"skill": "ingeniero-agentico:procurement"}. The old Spanish name is accepted while the
    # translation is in progress.
    names = "|".join(aliases)  # plain [a-z-] names, nothing to escape
    return r'"skill"\s*:\s*"(?:[\w-]+:)?(?:' + names + r')"'


def load() -> tuple[dict, list[dict]]:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    skills, cases = data["skills"], data["cases"]
    errors = []
    seen = set()
    counts: dict[tuple[str, str], int] = {}
    for c in cases:
        for key in ("owner", "kind", "lang", "slug", "prompt"):
            if not c.get(key):
                errors.append(f"case without {key}: {c}")
        if c["owner"] not in skills:
            errors.append(f"unknown owner {c['owner']}")
        if c["expect"] is not None and c["expect"] not in skills:
            errors.append(f"unknown expect {c['expect']}")
        if c["kind"] == "pos" and c["expect"] != c["owner"]:
            errors.append(f"positive case must expect its owner: {c['slug']}")
        if c["kind"] == "neg" and c["expect"] == c["owner"]:
            errors.append(f"negative case cannot expect its owner: {c['slug']}")
        if c["kind"] == "neg" and c["expect"] == "orchestrate":
            errors.append(f"a negative cannot expect orchestrate (its chain may load the owner): {c['slug']}")
        key = (c["owner"], c["kind"])
        counts[key] = counts.get(key, 0) + 1
        c["name"] = f"{c['owner']}-{c['kind'][0]}{counts[key]}-{c['lang']}-{c['slug']}"
        if c["name"] in seen:
            errors.append(f"duplicate name {c['name']}")
        seen.add(c["name"])
    for s in skills:
        pos = [c for c in cases if c["owner"] == s and c["kind"] == "pos"]
        neg = [c for c in cases if c["owner"] == s and c["kind"] == "neg"]
        langs = {lang: sum(1 for c in pos if c["lang"] == lang) for lang in ("es", "en")}
        if len(pos) < 6 or langs["es"] < 3 or langs["en"] < 3:
            errors.append(f"{s}: needs 6 positives (3 es + 3 en), has {langs}")
        if len(neg) < 4:
            errors.append(f"{s}: needs 4 negatives, has {len(neg)}")
    if errors:
        sys.exit("cases.json is not valid:\n  " + "\n  ".join(errors))
    return skills, cases


def write_case(c: dict, skills: dict) -> int:
    folder = EVALS / c["owner"] / c["name"]
    (folder / "graders").mkdir(parents=True, exist_ok=True)
    tags = ["trigger", c["owner"], "positive" if c["kind"] == "pos" else "negative", c["lang"]]
    if c.get("near_miss"):
        tags.append("near-miss")
    if c.get("borderline"):
        tags.append("borderline")
    expect = c["expect"]
    if c["kind"] == "pos":
        expected = f"The {expect} skill fires; no other skill of the plugin does."
    elif expect:
        expected = f"{c['owner']} stays silent; the neighbour {expect} fires instead."
    else:
        expected = f"{c['owner']} stays silent; no skill of this plugin fires."
    if expect == "orchestrate":
        expected = "orchestrate fires (the skills of its chain may follow)."
    description = f"{'positive' if c['kind'] == 'pos' else 'negative'} {c['lang']} for {c['owner']}; expects {expect or 'no skill'}"
    (folder / "prompt.md").write_text(
        FRONTMATTER.format(
            name=c["name"],
            description=json.dumps(description, ensure_ascii=False),
            tags=json.dumps(tags),
            expected=json.dumps(expected, ensure_ascii=False),
            prompt=c["prompt"].strip(),
        ),
        encoding="utf-8",
        newline="\n",
    )
    graders = 0
    silent_ones = [] if expect == "orchestrate" else [s for s in skills if s != expect]
    if expect:
        (folder / "graders" / f"fires-{expect}.md").write_text(
            GRADER.format(pattern=pattern_for(skills[expect]), min=1, max_line="",
                          weight=max(1, len(silent_ones))),
            encoding="utf-8", newline="\n")
        graders += 1
    for s in silent_ones:
        (folder / "graders" / f"silent-{s}.md").write_text(
            GRADER.format(pattern=pattern_for(skills[s]), min=0, max_line="max: 0\n", weight=1),
            encoding="utf-8", newline="\n")
        graders += 1
    return graders


def main() -> None:
    skills, cases = load()
    if "--check" in sys.argv:
        print(f"OK · {len(cases)} cases")
        return
    for s in skills:
        target = EVALS / s
        if target.exists():
            shutil.rmtree(target)
    total = sum(write_case(c, skills) for c in cases)
    for s in skills:
        pos = sum(1 for c in cases if c["owner"] == s and c["kind"] == "pos")
        neg = sum(1 for c in cases if c["owner"] == s and c["kind"] == "neg")
        print(f"{s:22} {pos} positive · {neg} negative")
    print(f"OK · {len(cases)} cases · {total} graders")


if __name__ == "__main__":
    main()
