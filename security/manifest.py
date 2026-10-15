#!/usr/bin/env python3
"""SHA-256 manifest of every distributable file of ingeniero-agentico. Standard library only.

Usage:
    python security/manifest.py write  [--root DIR]          regenerate security/MANIFEST.sha256
    python security/manifest.py verify [--root DIR] [--json] exit 1 on any added, removed or changed file
    python security/manifest.py --test

What is covered (DISTRIBUTABLE): skills/, agents/, commands/, mcp/, install/, .claude-plugin/,
profiles/_template.yaml, ARCHITECTURE.md, AGENTS.md, and the checker itself (security/scan.py,
security/manifest.py, security/policy.json, security/allowlist.json): a tampered checker is a threat
of its own. Generated files are left out with exactly the same patterns install.py excludes
(GENERATED_PATTERNS); verify reports it if install/platforms.json starts excluding anything else,
because a file the manifest ignores but the installer copies would be an unverified file.

Hashes are taken over the content with CRLF normalised to LF for text files (no NUL byte), so a
checkout with Windows line endings verifies the same as one with LF. Binary files are hashed as is.
The file format is the one of sha256sum: "<hex>  <posix path>", sorted, with # comment lines.

Importable API (for install/install.py and mcp/server.py):
    from manifest import verify_tree, verify_copy
    ok, problems = verify_tree(repo_root)                       # the source tree before installing
    ok, problems = verify_copy(copy_dir, "skills/<name>/", repo_root_or_manifest_file)  # an installed copy
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent
MANIFEST_REL = "security/MANIFEST.sha256"
DISTRIBUTABLE_DIRS = ("skills", "agents", "commands", "mcp", "install", ".claude-plugin")
DISTRIBUTABLE_FILES = ("profiles/_template.yaml", "ARCHITECTURE.md", "AGENTS.md", "security/scan.py",
                       "security/manifest.py", "security/policy.json", "security/allowlist.json")
GENERATED_PATTERNS = ("__pycache__", "*.pyc", "*.pyo", ".DS_Store", "Thumbs.db", "outputs", "salidas")
GENERATED_PATHS = ("install/output", "install/salida", "instalar/salida")   # installer output folders
HEADER = ("# ingeniero-agentico · SHA-256 of every distributable file (CRLF normalised to LF in text files)\n"
          "# Regenerate after any change: python security/manifest.py write · check: python security/manifest.py verify\n")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _excluded(parts: tuple[str, ...]) -> bool:
    if any(fnmatch.fnmatch(p, pat) for p in parts for pat in GENERATED_PATTERNS):
        return True
    rel = "/".join(parts)
    return any(rel == g or rel.startswith(g + "/") for g in GENERATED_PATHS)


def file_hash(path: Path) -> str:
    data = path.read_bytes()
    if b"\0" not in data[:8192]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def distributable(root: Path) -> list[str]:
    """Sorted posix paths (relative to root) of every distributable file present."""
    root = Path(root)
    out = []
    for d in DISTRIBUTABLE_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            rel_dir = Path(dirpath).relative_to(root).parts
            dirnames[:] = sorted(x for x in dirnames if not _excluded(rel_dir + (x,)))
            for f in filenames:
                parts = rel_dir + (f,)
                if not _excluded(parts):
                    out.append("/".join(parts))
    for f in DISTRIBUTABLE_FILES:
        if (root / f).is_file():
            out.append(f)
    return sorted(set(out))


def compute(root: Path) -> dict[str, str]:
    root = Path(root)
    return {rel: file_hash(root / rel) for rel in distributable(root)}


def render(entries: dict[str, str]) -> str:
    return HEADER + "".join(f"{h}  {rel}\n" for rel, h in sorted(entries.items()))


def parse(text: str) -> tuple[dict[str, str], list[str]]:
    entries, problems = {}, []
    for n, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if not line.strip() or line.startswith("#"):
            continue
        h, sep, rel = line.partition("  ")
        rel = rel.strip()
        pp = PurePosixPath(rel)
        if not sep or len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
            problems.append(f"manifest line {n}: malformed")
        elif not rel or pp.is_absolute() or ".." in pp.parts or "\\" in rel or ":" in rel:
            problems.append(f"manifest line {n}: unsafe path")
        elif rel in entries:
            problems.append(f"manifest line {n}: duplicate {rel}")
        else:
            entries[rel] = h
    return entries, problems


def load(manifest_file: Path) -> tuple[dict[str, str], list[str]]:
    if not manifest_file.is_file():
        return {}, [f"manifest missing: {manifest_file.name} (run python security/manifest.py write)"]
    return parse(manifest_file.read_text(encoding="utf-8"))


def _install_excludes(root: Path) -> list[str]:
    for rel, key in (("install/platforms.json", "exclude"), ("instalar/plataformas.json", "excluir")):
        p = root / rel
        if p.is_file():
            try:
                return list(json.loads(p.read_text(encoding="utf-8")).get(key, []))
            except ValueError:
                return ["<unparseable platforms file>"]
    return []


def verify_tree(root, manifest_file=None, parts=None) -> tuple[bool, list[str]]:
    """Verify the distributable files of `root` against its manifest.
    `parts` (optional) limits the check to entries starting with one of these prefixes, e.g.
    ("skills/", "agents/", "commands/", "mcp/", ".claude-plugin/") for a plugin ZIP that does not ship
    install/ or AGENTS.md. Files under those prefixes that the manifest does not list still fail.
    Returns (ok, problems); problems are 'added: x', 'removed: x', 'changed: x' or manifest errors."""
    root = Path(root).resolve()
    mf = Path(manifest_file) if manifest_file else root / MANIFEST_REL
    expected, problems = load(mf)
    if not expected and problems:
        return False, problems
    actual = compute(root)
    if parts:
        keep = tuple(parts)
        expected = {k: v for k, v in expected.items() if k.startswith(keep)}
        actual = {k: v for k, v in actual.items() if k.startswith(keep)}
        if not expected:
            return False, problems + [f"manifest has no entries under {', '.join(keep)}"]
    for rel in sorted(set(actual) - set(expected)):
        problems.append(f"added: {rel}")
    for rel in sorted(set(expected) - set(actual)):
        problems.append(f"removed: {rel}")
    for rel in sorted(set(actual) & set(expected)):
        if actual[rel] != expected[rel]:
            problems.append(f"changed: {rel}")
    extra = [e for e in _install_excludes(root) if e not in GENERATED_PATTERNS]
    if extra:
        problems.append(f"install excludes {extra} which the manifest does not: unverified files would be skipped")
    return not problems, problems


def verify_copy(copy_dir, prefix: str, source) -> tuple[bool, list[str]]:
    """Verify an installed copy of one part of the tree (e.g. copy_dir=~/.claude/skills/audit,
    prefix='skills/audit/'). `source` is the repo root or a manifest file. Every manifest entry under
    `prefix` must exist in the copy with the same hash, and the copy must hold nothing else (generated
    files aside)."""
    src = Path(source)
    mf = src if src.is_file() else src / MANIFEST_REL
    entries, problems = load(mf)
    if not entries and problems:
        return False, problems
    prefix = prefix.rstrip("/") + "/"
    wanted = {rel[len(prefix):]: h for rel, h in entries.items() if rel.startswith(prefix)}
    if not wanted:
        return False, problems + [f"manifest has no entries under {prefix}"]
    copy_dir = Path(copy_dir)
    present = {}
    for dirpath, dirnames, filenames in os.walk(copy_dir):
        rel_dir = Path(dirpath).relative_to(copy_dir).parts
        dirnames[:] = [d for d in dirnames if not _excluded(rel_dir + (d,))]
        for f in filenames:
            parts = rel_dir + (f,)
            if not _excluded(parts):
                present["/".join(parts)] = file_hash(Path(dirpath) / f)
    for rel in sorted(set(present) - set(wanted)):
        problems.append(f"added: {prefix}{rel}")
    for rel in sorted(set(wanted) - set(present)):
        problems.append(f"removed: {prefix}{rel}")
    for rel in sorted(set(wanted) & set(present)):
        if wanted[rel] != present[rel]:
            problems.append(f"changed: {prefix}{rel}")
    return not problems, problems


def write(root) -> Path:
    root = Path(root).resolve()
    mf = root / MANIFEST_REL
    mf.parent.mkdir(parents=True, exist_ok=True)
    text = render(compute(root))
    with open(mf, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return mf


def self_test() -> int:
    failures = []
    tmp = Path(tempfile.mkdtemp(prefix="ia-manifest-test-"))

    def check(label: str, cond: bool) -> None:
        print(f"  {'ok  ' if cond else 'FAIL'} {label}")
        if not cond:
            failures.append(label)
    try:
        root = tmp / "repo"
        files = {"skills/a/SKILL.md": "---\nname: a\n---\n", "skills/a/scripts/a.py": "print(1)\n",
                 "agents/x.md": "x\n", "mcp/server.py": "s\n", "install/install.py": "i\n",
                 "profiles/_template.yaml": "t: 1\n", "AGENTS.md": "a\n", "ARCHITECTURE.md": "b\n",
                 "README.md": "not distributable\n", "skills/a/__pycache__/a.cpython-311.pyc": "junk",
                 "install/output/claude-desktop/x.zip": "junk"}
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content.encode())
        write(root)
        ok, probs = verify_tree(root)
        check("fresh manifest verifies", ok and not probs)
        listed = parse((root / MANIFEST_REL).read_text(encoding="utf-8"))[0]
        check("generated files and installer output are not listed",
              not any("__pycache__" in r or r.startswith("install/output") for r in listed))
        check("README.md is not distributable", "README.md" not in listed)
        (root / "skills/a/scripts/a.py").write_bytes(b"print(1)\r\n")
        check("CRLF checkout still verifies", verify_tree(root)[0])
        (root / "skills/a/scripts/a.py").write_text("print('pwned')\n", encoding="utf-8")
        ok, probs = verify_tree(root)
        check("changed file is detected", not ok and "changed: skills/a/scripts/a.py" in probs)
        (root / "skills/a/scripts/a.py").write_text("print(1)\n", encoding="utf-8")
        (root / "skills/a/scripts/evil.py").write_text("x\n", encoding="utf-8")
        ok, probs = verify_tree(root)
        check("added file is detected", not ok and "added: skills/a/scripts/evil.py" in probs)
        (root / "skills/a/scripts/evil.py").unlink()
        (root / "agents/x.md").unlink()
        ok, probs = verify_tree(root)
        check("removed file is detected", not ok and "removed: agents/x.md" in probs)
        (root / "agents/x.md").write_text("x\n", encoding="utf-8")
        mf = root / MANIFEST_REL
        good = mf.read_text(encoding="utf-8")
        mf.write_text(good + "0" * 64 + "  ../../etc/passwd\n", encoding="utf-8")
        ok, probs = verify_tree(root)
        check("path traversal in the manifest is rejected", not ok and any("unsafe path" in p for p in probs))
        mf.unlink()
        ok, probs = verify_tree(root)
        check("missing manifest fails", not ok and "manifest missing" in probs[0])
        mf.write_text(good, encoding="utf-8")
        (root / "install" / "install.py").unlink()
        ok, probs = verify_tree(root, parts=("skills/", "agents/", "mcp/"))
        check("partial tree (plugin ZIP) verifies its own parts", ok)
        (root / "skills/a/extra.md").write_text("x\n", encoding="utf-8")
        check("partial check still catches an added file", not verify_tree(root, parts=("skills/",))[0])
        (root / "skills/a/extra.md").unlink()
        (root / "install" / "install.py").write_bytes(b"i\n")
        copy = tmp / "installed" / "a"
        shutil.copytree(root / "skills" / "a", copy)
        check("installed copy verifies", verify_copy(copy, "skills/a/", root)[0])
        (copy / "scripts" / "a.py").write_text("tampered\n", encoding="utf-8")
        ok, probs = verify_copy(copy, "skills/a/", root)
        check("tampered installed copy is detected", not ok and "changed: skills/a/scripts/a.py" in probs)
        (root / "install" / "platforms.json").write_text(json.dumps({"exclude": ["__pycache__", "*.py"]}),
                                                         encoding="utf-8")
        write(root)
        ok, probs = verify_tree(root)
        check("installer excluding more than the manifest is reported", not ok and any("install excludes" in p for p in probs))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok, probs = verify_tree(DEFAULT_ROOT)
    mid = (DEFAULT_ROOT / "_TRANSLATION-CONTRACT.md").exists()
    state = "ok  " if ok else ("WARN" if mid else "INFO")
    print(f"  {state} current repo manifest: {'verifies' if ok else f'{len(probs)} problem(s), run manifest.py verify'}"
          + (" · translation in progress" if not ok and mid else ""))
    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print("OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SHA-256 manifest of the distributable files.")
    ap.add_argument("command", nargs="?", choices=("write", "verify"))
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--test", "--probar", action="store_true", dest="test")
    a = ap.parse_args(argv)
    if a.test:
        return self_test()
    if not a.command:
        ap.print_help()
        return 2
    root = Path(a.root)
    if a.command == "write":
        mf = write(root)
        n = len(parse(mf.read_text(encoding="utf-8"))[0])
        print(f"manifest: {n} files written to {MANIFEST_REL} (sha256 of the manifest {file_hash(mf)[:16]}…)")
        return 0
    ok, problems = verify_tree(root)
    if a.json:
        print(json.dumps({"ok": ok, "problems": problems}, ensure_ascii=False, indent=2))
    else:
        for p in problems:
            print(f"  {p}")
        print("manifest: OK" if ok else f"manifest: FAILED ({len(problems)} problem(s)). If the change is yours, "
              "run python security/manifest.py write and commit the manifest with it.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
