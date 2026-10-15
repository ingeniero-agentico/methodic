#!/usr/bin/env python3
"""Installs the ingeniero-agentico skills on an agent platform.

Usage:
    python install/install.py --platform claude-code|claude-desktop|codex|cursor|gemini|hermes|agents
                              [--target <folder>] [--link] [--force]
    python install/install.py --platform <p> --uninstall [--target <folder>]
    python install/install.py --list [--platform <p>] [--target <folder>]
    python install/install.py --test [--no-scripts]

The paths of each platform are in install/platforms.json (with the URL of the documentation that
backs them). --target replaces the user's folder ({HOME}): use it to install into a test folder
without touching the real configuration. On claude-desktop, --target is the folder where the ZIP
files go (default install/output/claude-desktop).

Standard library only. It never edits any platform's configuration file (settings.json,
config.yaml, config.toml): it only copies or links folders and leaves a manifest of what it
installed, which is the only thing --uninstall removes.

The old Spanish flags (--plataforma, --destino, --enlazar, --forzar, --desinstalar, --listar,
--probar, --sin-scripts) are still accepted as hidden aliases.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONFIG = HERE / "platforms.json"
MANIFEST_FOLDER = ".ingeniero-agentico"
VALID_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024  # https://agentskills.io/specification
AGENT_FIELDS = {"cursor-md": ("name", "description"), "gemini-md": ("name", "description")}
PROFILE_FOLDERS = ("profiles", "perfiles")  # perfiles/ is where v1.0 put the template

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


class InstallError(Exception):
    pass


# ---------------------------------------------------------------- configuration and inventory

def load_config() -> dict:
    with open(CONFIG, encoding="utf-8") as fh:
        return json.load(fh)


def read_frontmatter(path: Path) -> tuple[dict, str]:
    """Returns (fields, body). Reads the YAML subset the repo uses: `key: value` and lists
    `  - item`. Fails if the file has a BOM or does not open with `---`."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InstallError(f"{path}: has a BOM; the frontmatter is not recognized")
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise InstallError(f"{path}: does not open with '---'")
    end = text.find("\n---", 4)
    if end < 0:
        raise InstallError(f"{path}: the frontmatter does not close with '---'")
    fields: dict = {}
    key = None
    for line in text[4:end].split("\n"):
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = value if value else []
        elif key and re.match(r"^\s+-\s+", line):
            if not isinstance(fields.get(key), list):
                fields[key] = []
            fields[key].append(re.sub(r"^\s+-\s+", "", line).strip())
    body = text[end + 4:].lstrip("\n")
    return fields, body


def inventory() -> dict:
    skills = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
    agents = sorted((REPO / "agents").glob("*.md"))
    commands = sorted((REPO / "commands").glob("*.md"))
    return {"skills": skills, "agents": agents, "commands": commands}


def validate_skill(folder: Path) -> list[str]:
    """Hard errors against the Agent Skills specification. Warnings go through skill_warnings()."""
    errors = []
    try:
        fields, _ = read_frontmatter(folder / "SKILL.md")
    except (InstallError, OSError, UnicodeDecodeError) as e:
        return [str(e)]
    name = fields.get("name", "")
    if not name:
        errors.append(f"{folder.name}: name is missing")
    elif name != folder.name:
        errors.append(f"{folder.name}: name '{name}' does not match the folder")
    elif not VALID_NAME.match(name) or len(name) > MAX_NAME:
        errors.append(f"{folder.name}: invalid name (lowercase, digits and hyphens, max. {MAX_NAME})")
    if not fields.get("description"):
        errors.append(f"{folder.name}: description is missing")
    return errors


def skill_warnings(folder: Path) -> list[str]:
    fields, _ = read_frontmatter(folder / "SKILL.md")
    length = len(fields.get("description", ""))
    if length > MAX_DESCRIPTION:
        return [f"{folder.name}: description of {length} characters (the Agent Skills standard and claude.ai "
                f"accept {MAX_DESCRIPTION}; a strict platform may reject or truncate it)"]
    return []


# ---------------------------------------------------------------- paths

def base_env(target: Path | None) -> dict:
    if target is not None:
        home = target.resolve()
        return {"HOME": home, "LOCALAPPDATA": home / "AppData" / "Local", "use_variables": False}
    local = os.environ.get("LOCALAPPDATA", "").strip()
    return {"HOME": Path.home(),
            "LOCALAPPDATA": Path(local) if local else Path.home() / "AppData" / "Local",
            "use_variables": True}


def resolve_root(spec: dict, base: dict) -> Path:
    variable = spec.get("variable")
    if variable and base["use_variables"] and os.environ.get(variable, "").strip():
        return Path(os.path.expanduser(os.environ[variable].strip()))
    template = spec.get("default_windows") if os.name == "nt" and spec.get("default_windows") else spec["default"]
    text = template.replace("{HOME}", str(base["HOME"])).replace("{LOCALAPPDATA}", str(base["LOCALAPPDATA"]))
    return Path(text)


def platform_paths(plat: dict, base: dict) -> dict:
    """Destination folder of each component (or None if the platform does not use it)."""
    paths = {}
    for comp in ("skills", "agents", "commands"):
        spec = plat.get(comp)
        paths[comp] = resolve_root(spec["root"], base) / spec["folder"] if spec else None
    paths["root"] = paths["skills"].parent if paths["skills"] else None
    return paths


# ---------------------------------------------------------------- file operations

def is_link(p: Path) -> bool:
    if os.path.islink(p):
        return True
    if hasattr(os.path, "isjunction") and os.path.isjunction(p):
        return True
    try:
        attributes = os.lstat(p).st_file_attributes  # Windows only
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def remove(p: Path) -> None:
    """Removes a file, a folder or a link. From a link or junction it removes ONLY the link:
    it never goes into the target."""
    if is_link(p):
        if os.name == "nt" and p.is_dir():
            os.rmdir(p)  # on Windows, rmdir of a junction or folder symlink removes the link
        else:
            os.unlink(p)
    elif p.is_dir():
        shutil.rmtree(p)
    elif p.exists():
        p.unlink()


def ignore(patterns: list[str]):
    def _ignore(_folder, names):
        return {n for n in names if any(fnmatch.fnmatch(n, pat) for pat in patterns)}
    return _ignore


def link_folder(source: Path, target: Path) -> None:
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(target), str(source)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise InstallError(f"could not create the junction {target}: {r.stdout}{r.stderr}")
    else:
        os.symlink(source, target, target_is_directory=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:  # no BOM
        fh.write(text)


# ---------------------------------------------------------------- agent conversion

def toml_string(text: str) -> str:
    if "'''" not in text and not text.startswith("\n"):
        return "'''\n" + text.rstrip("\n") + "\n'''"
    return json.dumps(text, ensure_ascii=False)


def convert_agent(source: Path, fmt: str) -> tuple[str, str]:
    """Returns (file_name, content) of the agent in the platform's format."""
    if fmt == "claude-md":
        return source.name, source.read_text(encoding="utf-8")
    fields, body = read_frontmatter(source)
    name = fields.get("name") or source.stem
    description = fields.get("description", "")
    if fmt == "codex-toml":
        text = (f"# Generated by install.py from agents/{source.name} of ingeniero-agentico.\n"
                f"# No 'model': it inherits the one of the agent that launches it.\n"
                f"name = {json.dumps(name, ensure_ascii=False)}\n"
                f"description = {json.dumps(description, ensure_ascii=False)}\n"
                f"developer_instructions = {toml_string(body)}\n")
        return f"{name}.toml", text
    if fmt in AGENT_FIELDS:
        front = (f"---\nname: {name}\n"
                 f"description: {json.dumps(description, ensure_ascii=False)}\n---\n\n")
        notice = (f"<!-- Generated by install.py from agents/{source.name}: tools, model and skills were "
                  f"removed because they use Claude Code names. -->\n\n")
        return source.name, front + notice + body
    raise InstallError(f"unknown agent format: {fmt}")


# ---------------------------------------------------------------- manifests

def manifest_folder(paths: dict) -> Path:
    return paths["root"] / MANIFEST_FOLDER


def manifest_paths(m: dict) -> list[str]:
    return m.get("paths", m.get("rutas", []))  # "rutas": manifests written by v1.0


def read_manifest(paths: dict, key: str) -> dict | None:
    path = manifest_folder(paths) / f"{key}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def paths_of_others(paths: dict, key: str) -> set[str]:
    """Paths another manifest in the same root claims (e.g. codex and agents share
    ~/.agents/skills): those are not removed."""
    owned = set()
    folder = manifest_folder(paths)
    if folder.is_dir():
        for m in folder.glob("*.json"):
            if m.stem == key:
                continue
            with open(m, encoding="utf-8") as fh:
                owned.update(manifest_paths(json.load(fh)))
    return owned


def all_installed_paths(paths: dict) -> set[str]:
    return paths_of_others(paths, "\0")


# ---------------------------------------------------------------- install into folders

def check_integrity() -> None:
    """Refuses to install from a tree whose files do not match security/MANIFEST.sha256.
    Runs before anything is written; --force never skips it (see SECURITY.md)."""
    sys.path.insert(0, str(REPO / "security"))
    try:
        from manifest import verify_tree
    except ImportError as e:
        raise InstallError(f"security/manifest.py is missing, nothing is installed ({e})")
    ok, problems = verify_tree(REPO)
    if not ok:
        raise InstallError("the repo does not match security/MANIFEST.sha256, nothing is installed:\n  "
                           + "\n  ".join(problems[:20]))


def check_copy(dest: Path, skill: str, extras: list[str]) -> None:
    """After copying a skill, its files must match the manifest; only the configured extras are allowed."""
    from manifest import verify_copy
    ok, problems = verify_copy(dest, f"skills/{skill}/", REPO)
    allowed = {f"added: {p}" for x in extras for p in (Path(x).name, f"skills/{skill}/{Path(x).name}")}
    real = [p for p in problems if p not in allowed]
    if not ok and real:
        raise InstallError(f"the installed copy of {skill} does not match the manifest:\n  "
                           + "\n  ".join(real[:20]))


def install_folders(key: str, plat: dict, cfg: dict, base: dict, link: bool, force: bool,
                    quiet: bool = False) -> dict:
    check_integrity()
    inv = inventory()
    paths = platform_paths(plat, base)
    exclude = cfg.get("exclude", [])
    say = (lambda *_: None) if quiet else print

    errors = [e for s in inv["skills"] for e in validate_skill(REPO / "skills" / s)]
    if errors:
        raise InstallError("invalid skills, nothing is installed:\n  " + "\n  ".join(errors))
    for s in inv["skills"]:
        for w in skill_warnings(REPO / "skills" / s):
            say(f"  warning: {w}")

    # Full plan before writing anything.
    plan: list[tuple[str, Path, object]] = []
    for s in inv["skills"]:
        plan.append(("skill", paths["skills"] / s, REPO / "skills" / s))
    if paths["agents"]:
        fmt = plat["agents"]["format"]
        for a in inv["agents"]:
            name, content = convert_agent(a, fmt)
            plan.append(("agent", paths["agents"] / name, content))
    if paths["commands"]:
        for c in inv["commands"]:
            plan.append(("command", paths["commands"] / c.name, c.read_text(encoding="utf-8")))
    template_target = paths["root"] / cfg["profile_template"]
    if not link:
        plan.append(("template", template_target, REPO / cfg["profile_template"]))

    previous = read_manifest(paths, key) or {"paths": []}
    ours = set(manifest_paths(previous)) | all_installed_paths(paths)
    foreign = [str(d) for kind, d, _ in plan
               if kind != "template" and (d.exists() or is_link(d)) and str(d) not in ours]
    if foreign and not force:
        raise InstallError("these already exist and were not installed by this installer (use --force to "
                           "replace them):\n  " + "\n  ".join(foreign))

    installed: list[str] = []
    for kind, d, source in plan:
        if kind == "template":
            if d.exists() and str(d) not in ours:
                if d.read_bytes() != Path(source).read_bytes():
                    say(f"  warning: {d} already exists and is different; it is left as it is")
                continue  # not ours: not overwritten nor recorded (uninstall will not remove it)
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, d)
            installed.append(str(d))
            continue
        if d.exists() or is_link(d):
            remove(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        if kind == "skill":
            if link:
                link_folder(Path(source), d)
            else:
                shutil.copytree(source, d, ignore=ignore(exclude))
                extras = cfg.get("extras", {}).get(d.name, [])
                for extra in extras:
                    shutil.copyfile(REPO / extra, d / Path(extra).name)
                check_copy(d, d.name, extras)
        else:
            write(d, source)
        installed.append(str(d))

    manifest = {"platform": key, "repo": "ingeniero-agentico", "version": plugin_version(),
                "mode": "link" if link else "copy",
                "date": datetime.now().strftime("%d-%m-%Y %H:%M"), "paths": installed}
    write(manifest_folder(paths) / f"{key}.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    say(f"{plat['name']}: {len(inv['skills'])} skills in {paths['skills']}"
        + (f" ({'links' if link else 'copies'})"))
    if paths["agents"]:
        say(f"  agents ({plat['agents']['format']}) in {paths['agents']}")
    if paths["commands"]:
        say(f"  commands in {paths['commands']}")
    if not link:
        say(f"  profile template in {template_target}")
    say(f"  orchestration: {plat.get('orchestration', '')}")
    if plat.get("note"):
        say(f"  note: {plat['note']}")
    return paths


def uninstall_folders(key: str, plat: dict, base: dict, quiet: bool = False) -> int:
    paths = platform_paths(plat, base)
    say = (lambda *_: None) if quiet else print
    manifest = read_manifest(paths, key)
    if manifest is None:
        say(f"{plat['name']}: no installation recorded in {manifest_folder(paths)}")
        return 0
    shared = paths_of_others(paths, key)
    removed = 0
    for r in manifest_paths(manifest):
        p = Path(r)
        if r in shared:
            say(f"  kept (another installation uses it): {p}")
            continue
        if p.exists() or is_link(p):
            remove(p)
            removed += 1
    (manifest_folder(paths) / f"{key}.json").unlink()
    for empty in (manifest_folder(paths), *(paths["root"] / f for f in PROFILE_FOLDERS)):
        try:
            empty.rmdir()
        except OSError:
            pass
    say(f"{plat['name']}: {removed} items removed")
    return removed


# ---------------------------------------------------------------- claude-desktop (ZIP)

def plugin_version() -> str:
    try:
        with open(REPO / ".claude-plugin" / "plugin.json", encoding="utf-8") as fh:
            return json.load(fh).get("version", "")
    except OSError:
        return ""


def add_tree(z: zipfile.ZipFile, source: Path, prefix: str, exclude: list[str]) -> None:
    for root, folders, files in os.walk(source):
        folders[:] = sorted(c for c in folders if not any(fnmatch.fnmatch(c, p) for p in exclude))
        for a in sorted(files):
            if any(fnmatch.fnmatch(a, p) for p in exclude):
                continue
            path = Path(root) / a
            z.write(path, prefix + path.relative_to(source).as_posix())


def build_zips(plat: dict, cfg: dict, out: Path, quiet: bool = False) -> list[Path]:
    check_integrity()
    inv = inventory()
    exclude = cfg.get("exclude", [])
    say = (lambda *_: None) if quiet else print
    errors = [e for s in inv["skills"] for e in validate_skill(REPO / "skills" / s)]
    if errors:
        raise InstallError("invalid skills:\n  " + "\n  ".join(errors))
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for s in inv["skills"]:
        target = out / f"{s}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            add_tree(z, REPO / "skills" / s, f"{s}/", exclude)
            for extra in cfg.get("extras", {}).get(s, []):
                z.write(REPO / extra, f"{s}/{Path(extra).name}")
        made.append(target)
        for w in skill_warnings(REPO / "skills" / s):
            say(f"  warning: {w}")
    target = out / plat["plugin_zip"]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for item in plat["plugin_zip_includes"]:
            p = REPO / item
            if p.is_dir():
                add_tree(z, p, f"ingeniero-agentico/{item}/", exclude)
            elif p.exists():
                z.write(p, f"ingeniero-agentico/{item}")
    made.append(target)
    say(f"{plat['name']}: {len(made) - 1} skill ZIPs + 1 plugin ZIP in {out}")
    say("  skills: Customize > Skills > upload each <skill>.zip (needs code execution)")
    say(f"  plugin: Customize > Plugins > Add > Upload plugin > {plat['plugin_zip']}")
    return made


def zip_output(plat: dict, target: Path | None) -> Path:
    return target.resolve() if target else REPO / plat["output"]


# ---------------------------------------------------------------- list

def list_platforms(cfg: dict, key: str | None, target: Path | None) -> None:
    inv = inventory()
    print(f"Repo: {len(inv['skills'])} skills ({', '.join(inv['skills'])}), "
          f"{len(inv['agents'])} agents, {len(inv['commands'])} commands · version {plugin_version()}")
    base = base_env(target)
    for k, plat in cfg["platforms"].items():
        if key and k != key:
            continue
        print(f"\n[{k}] {plat['name']}")
        if plat["kind"] == "zip":
            out = zip_output(plat, target)
            zips = sorted(out.glob("*.zip")) if out.is_dir() else []
            print(f"  ZIP in {out}: {len(zips)} built")
            continue
        paths = platform_paths(plat, base)
        print(f"  skills   -> {paths['skills']}")
        print(f"  agents   -> {paths['agents'] or 'not applicable'}")
        print(f"  commands -> {paths['commands'] or 'not applicable'}")
        m = read_manifest(paths, k)
        if m:
            present = [s for s in inv["skills"] if (paths["skills"] / s / "SKILL.md").exists()]
            print(f"  installed ({m.get('mode', m.get('modo'))}, {m.get('date', m.get('fecha'))}, "
                  f"v{m.get('version', '')}): {len(present)}/{len(inv['skills'])} skills present")
        else:
            print("  not installed by this installer")


# ---------------------------------------------------------------- test

def scripts_to_test(skill_folder: Path) -> list[str]:
    text = (skill_folder / "SKILL.md").read_text(encoding="utf-8")
    return sorted(set(re.findall(r"python3?\s+scripts/([\w.-]+\.py)\s+--(?:test|probar)\b", text)))


def run_tests(skill_folder: Path, home: Path) -> list[str]:
    failures = []
    # The interpreter keeps the real environment: overriding USERPROFILE (or LOCALAPPDATA) breaks the
    # Microsoft Store Python, whose sys.executable is an app execution alias that only launches with
    # the real user profile (a script that spawns sys.executable, like audit/rerun.py, then fails with
    # FileNotFoundError). Only what the scripts read is changed: no INGENIERO_DATOS, so they never reach
    # the real data folder (their sibling-folder lookup is relative to the installed copy, never ~).
    env = {k: v for k, v in os.environ.items() if k != "INGENIERO_DATOS"}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    if os.name != "nt":
        env["HOME"] = str(home)
    for script in scripts_to_test(skill_folder):
        r = subprocess.run([sys.executable, str(skill_folder / "scripts" / script), "--test"],
                           cwd=skill_folder, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        if r.returncode != 0 or "OK" not in tail:
            detail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            failures.append(f"{skill_folder.name}/{script}: exit {r.returncode} · " + " | ".join(detail))
    return failures


def junk(folder: Path, exclude: list[str]) -> list[str]:
    bad = []
    for root, folders, files in os.walk(folder):
        for n in folders + files:
            if any(fnmatch.fnmatch(n, p) for p in exclude):
                bad.append(str(Path(root) / n))
    return bad


def check_folders(key: str, plat: dict, cfg: dict, paths: dict, home: Path, linked: bool,
                  with_scripts: bool) -> list[str]:
    inv = inventory()
    failures = []
    for s in inv["skills"]:
        d = paths["skills"] / s
        if not (d / "SKILL.md").is_file():
            failures.append(f"missing {d / 'SKILL.md'}")
            continue
        failures += validate_skill(d)
        if linked:
            if not is_link(d):
                failures.append(f"{d} should be a link")
            elif Path(os.path.realpath(d)) != (REPO / "skills" / s).resolve():
                failures.append(f"{d} does not resolve to the repo ({os.path.realpath(d)})")
        else:
            failures += [f"junk installed: {m}" for m in junk(d, cfg.get("exclude", []))]
            for extra in cfg.get("extras", {}).get(s, []):
                if not (d / Path(extra).name).is_file():
                    failures.append(f"missing extra {extra} in {d}")
    if not linked and not (paths["root"] / cfg["profile_template"]).is_file():
        failures.append(f"missing the template in {paths['root'] / cfg['profile_template']}")
    if paths["agents"]:
        fmt = plat["agents"]["format"]
        for a in inv["agents"]:
            name, _ = convert_agent(a, fmt)
            p = paths["agents"] / name
            if not p.is_file():
                failures.append(f"missing agent {p}")
                continue
            if p.read_bytes().startswith(b"\xef\xbb\xbf"):
                failures.append(f"{p} has a BOM")
            if fmt == "codex-toml":
                try:
                    import tomllib
                    data = tomllib.loads(p.read_text(encoding="utf-8"))
                    for field in ("name", "description", "developer_instructions"):
                        if not data.get(field):
                            failures.append(f"{p}: missing {field}")
                except ImportError:
                    pass
                except Exception as e:  # noqa: BLE001 (any TOML error is a failure)
                    failures.append(f"{p}: invalid TOML ({e})")
            elif fmt in AGENT_FIELDS:
                fields, _ = read_frontmatter(p)
                extra_fields = set(fields) - set(AGENT_FIELDS[fmt])
                if extra_fields or not fields.get("name") or not fields.get("description"):
                    failures.append(f"{p}: frontmatter {sorted(fields)}")
            else:
                read_frontmatter(p)
    if paths["commands"]:
        for c in inv["commands"]:
            if not (paths["commands"] / c.name).is_file():
                failures.append(f"missing command {paths['commands'] / c.name}")
    if with_scripts:
        for s in inv["skills"]:
            failures += run_tests(paths["skills"] / s, home)
    return failures


def check_zips(plat: dict, cfg: dict, zips: list[Path]) -> list[str]:
    inv = inventory()
    failures = []
    exclude = cfg.get("exclude", [])
    by_name = {z.stem: z for z in zips}
    for s in inv["skills"]:
        z = by_name.get(s)
        if z is None:
            failures.append(f"missing {s}.zip")
            continue
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
            if zf.testzip() is not None:
                failures.append(f"{z.name}: corrupt ZIP")
        if any("\\" in n for n in names):
            failures.append(f"{z.name}: paths with backslashes")
        if not all(n.startswith(f"{s}/") for n in names):
            failures.append(f"{z.name}: entries outside {s}/")
        if f"{s}/SKILL.md" not in names:
            failures.append(f"{z.name}: {s}/SKILL.md missing at the first level of the folder")
        if "SKILL.md" in names:
            failures.append(f"{z.name}: loose SKILL.md at the root of the ZIP")
        if any(any(fnmatch.fnmatch(part, p) for p in exclude) for n in names for part in n.split("/")):
            failures.append(f"{z.name}: contains excluded files")
        for extra in cfg.get("extras", {}).get(s, []):
            if f"{s}/{Path(extra).name}" not in names:
                failures.append(f"{z.name}: missing the extra {extra}")
    zp = by_name.get(Path(plat["plugin_zip"]).stem)
    if zp is None:
        failures.append("missing the plugin ZIP")
    else:
        with zipfile.ZipFile(zp) as zf:
            names = zf.namelist()
        top = {n.split("/")[0] for n in names}
        if top != {"ingeniero-agentico"}:
            failures.append(f"{zp.name}: more than one top-level folder ({sorted(top)})")
        required = ["ingeniero-agentico/.claude-plugin/plugin.json",
                    f"ingeniero-agentico/{cfg['profile_template']}"]
        required += [f"ingeniero-agentico/skills/{s}/SKILL.md" for s in inv["skills"]]
        with open(REPO / ".claude-plugin" / "plugin.json", encoding="utf-8") as fh:
            servers = json.load(fh).get("mcpServers", {})
        for srv in servers.values():  # every script the plugin launches with ${CLAUDE_PLUGIN_ROOT} must travel
            for arg in srv.get("args", []):
                if "${CLAUDE_PLUGIN_ROOT}/" in arg:
                    required.append("ingeniero-agentico/" + arg.split("${CLAUDE_PLUGIN_ROOT}/", 1)[1])
        failures += [f"{zp.name}: missing {r}" for r in required if r not in names]
        if any(n.startswith("ingeniero-agentico/bin/") for n in names):
            failures.append(f"{zp.name}: contains bin/ (claude.ai rejects the plugin)")
    return failures


def run_self_test(cfg: dict, with_scripts: bool) -> int:
    results = []
    with tempfile.TemporaryDirectory(prefix="ingeniero-agentico-test-") as tmp:
        tmp = Path(tmp)
        for key, plat in cfg["platforms"].items():
            home = tmp / key
            home.mkdir()
            base = base_env(home)
            try:
                if plat["kind"] == "zip":
                    zips = build_zips(plat, cfg, home / "output", quiet=True)
                    failures = check_zips(plat, cfg, zips)
                    detail = f"{len(zips)} ZIP"
                else:
                    paths = install_folders(key, plat, cfg, base, link=False, force=False, quiet=True)
                    failures = check_folders(key, plat, cfg, paths, home, linked=False, with_scripts=with_scripts)
                    install_folders(key, plat, cfg, base, link=False, force=False, quiet=True)  # reinstall
                    uninstall_folders(key, plat, base, quiet=True)
                    leftovers = [str(p) for p in (paths["skills"], paths["agents"], paths["commands"])
                                 if p and p.is_dir() and any(p.iterdir())]
                    if (paths["root"] / cfg["profile_template"]).exists():
                        leftovers.append(str(paths["root"] / cfg["profile_template"]))
                    failures += [f"left after uninstall: {r}" for r in leftovers]
                    detail = str(paths["skills"].relative_to(home))
            except InstallError as e:
                failures, detail = [str(e)], "error"
            results.append((key, detail, failures))

        # Links: install, check they resolve to the repo, uninstall and check the repo is intact.
        home = tmp / "link"
        home.mkdir()
        plat = cfg["platforms"]["agents"]
        base = base_env(home)
        try:
            paths = install_folders("agents", plat, cfg, base, link=True, force=False, quiet=True)
            failures = check_folders("agents", plat, cfg, paths, home, linked=True, with_scripts=False)
            if with_scripts:
                failures += run_tests(paths["skills"] / "procurement", home)
            uninstall_folders("agents", plat, base, quiet=True)
            failures += [f"the repo lost {s}/SKILL.md" for s in inventory()["skills"]
                         if not (REPO / "skills" / s / "SKILL.md").is_file()]
            if paths["skills"].is_dir() and any(paths["skills"].iterdir()):
                failures.append("links left after uninstall")
        except InstallError as e:
            failures = [str(e)]
        results.append(("agents --link", "junction" if os.name == "nt" else "symlink", failures))

        # Two installations sharing a folder (codex and agents): removing one does not remove the other.
        home = tmp / "shared"
        home.mkdir()
        base = base_env(home)
        failures = []
        try:
            install_folders("codex", cfg["platforms"]["codex"], cfg, base, False, False, quiet=True)
            r_ag = install_folders("agents", cfg["platforms"]["agents"], cfg, base, False, False, quiet=True)
            uninstall_folders("codex", cfg["platforms"]["codex"], base, quiet=True)
            failures += [f"uninstalling codex removed {s} from agents" for s in inventory()["skills"]
                         if not (r_ag["skills"] / s / "SKILL.md").is_file()]
            uninstall_folders("agents", cfg["platforms"]["agents"], base, quiet=True)
            # A foreign folder is not overwritten without --force.
            foreign = r_ag["skills"] / "orchestrate"
            foreign.mkdir(parents=True)
            (foreign / "SKILL.md").write_text("---\nname: orchestrate\ndescription: foreign\n---\n", encoding="utf-8")
            try:
                install_folders("agents", cfg["platforms"]["agents"], cfg, base, False, False, quiet=True)
                failures.append("overwrote a foreign skill without --force")
            except InstallError:
                pass
            if "foreign" not in (foreign / "SKILL.md").read_text(encoding="utf-8"):
                failures.append("the foreign skill changed")
        except InstallError as e:
            failures.append(str(e))
        results.append(("codex + agents", "shared folder", failures))

    print("Installer test (temporary HOME, nothing touches the real configuration)")
    print(f"Each method's script: {'run with --test from the installed copy' if with_scripts else 'skipped (--no-scripts)'}\n")
    total = 0
    for key, detail, failures in results:
        state = "OK" if not failures else f"FAIL ({len(failures)})"
        print(f"  {key:<18} {detail:<34} {state}")
        for f in failures:
            print(f"      - {f}")
        total += len(failures)
    warnings = [w for s in inventory()["skills"] for w in skill_warnings(REPO / "skills" / s)]
    for w in warnings:
        print(f"  warning: {w}")
    print("\nOK" if total == 0 else f"\nFAIL: {total} problems")
    return 0 if total == 0 else 1


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    cfg = load_config()
    ap = argparse.ArgumentParser(description="Installs ingeniero-agentico on an agent platform.")
    hidden = argparse.SUPPRESS
    choices = sorted(cfg["platforms"])
    ap.add_argument("--platform", choices=choices)
    ap.add_argument("--plataforma", dest="platform", choices=choices, default=hidden, help=hidden)
    ap.add_argument("--target", type=Path, help="folder that replaces the user's folder (or the ZIP folder)")
    ap.add_argument("--destino", dest="target", type=Path, default=hidden, help=hidden)
    ap.add_argument("--link", action="store_true", help="links the skills to the repo instead of copying them")
    ap.add_argument("--enlazar", dest="link", action="store_true", default=hidden, help=hidden)
    ap.add_argument("--force", action="store_true", help="replaces same-name skills this installer did not install")
    ap.add_argument("--forzar", dest="force", action="store_true", default=hidden, help=hidden)
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--desinstalar", dest="uninstall", action="store_true", default=hidden, help=hidden)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--listar", dest="list", action="store_true", default=hidden, help=hidden)
    ap.add_argument("--test", action="store_true", help="installs into a temporary HOME and checks every platform")
    ap.add_argument("--probar", dest="test", action="store_true", default=hidden, help=hidden)
    ap.add_argument("--no-scripts", action="store_true", help="with --test, do not run each method's --test")
    ap.add_argument("--sin-scripts", dest="no_scripts", action="store_true", default=hidden, help=hidden)
    a = ap.parse_args(argv)

    try:
        if a.test:
            return run_self_test(cfg, with_scripts=not a.no_scripts)
        if a.list:
            list_platforms(cfg, a.platform, a.target)
            return 0
        if not a.platform:
            ap.error("--platform is missing (or use --list / --test)")
        plat = cfg["platforms"][a.platform]
        if plat["kind"] == "zip":
            out = zip_output(plat, a.target)
            if a.uninstall:
                removed = 0
                for z in sorted(out.glob("*.zip")) if out.is_dir() else []:
                    z.unlink()
                    removed += 1
                print(f"{plat['name']}: {removed} ZIPs removed from {out} (what was already uploaded to claude.ai "
                      "is removed in Customize)")
                return 0
            if a.link:
                print("warning: --link does not apply to claude-desktop; ZIPs are built")
            build_zips(plat, cfg, out)
            return 0
        base = base_env(a.target)
        if a.uninstall:
            uninstall_folders(a.platform, plat, base)
        else:
            install_folders(a.platform, plat, cfg, base, a.link, a.force)
        return 0
    except InstallError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
