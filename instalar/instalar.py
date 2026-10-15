#!/usr/bin/env python3
"""Instala las skills de ingeniero-agentico en una plataforma de agentes.

Uso:
    python instalar/instalar.py --plataforma claude-code|claude-desktop|codex|cursor|gemini|hermes|agents
                                [--destino <carpeta>] [--enlazar] [--forzar]
    python instalar/instalar.py --plataforma <p> --desinstalar [--destino <carpeta>]
    python instalar/instalar.py --listar [--plataforma <p>] [--destino <carpeta>]
    python instalar/instalar.py --probar [--sin-scripts]

Las rutas de cada plataforma están en instalar/plataformas.json (con la URL de la documentación que
las respalda). --destino reemplaza la carpeta del usuario ({HOME}): sirve para instalar en una
carpeta de prueba sin tocar la configuración real. En claude-desktop, --destino es la carpeta donde
quedan los ZIP (por defecto instalar/salida/claude-desktop).

Solo biblioteca estándar. No modifica archivos de configuración de ninguna plataforma (settings.json,
config.yaml, config.toml): solo copia o enlaza carpetas y deja un manifiesto de lo que instaló, que
es lo único que --desinstalar borra.
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

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
CONFIG = AQUI / "plataformas.json"
CARPETA_MANIFIESTOS = ".ingeniero-agentico"
NOMBRE_VALIDO = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NOMBRE = 64
MAX_DESCRIPCION = 1024  # https://agentskills.io/specification
CAMPOS_AGENTE = {"cursor-md": ("name", "description"), "gemini-md": ("name", "description")}

for flujo in (sys.stdout, sys.stderr):
    try:
        flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


class ErrorInstalacion(Exception):
    pass


# ---------------------------------------------------------------- configuración e inventario

def cargar_config() -> dict:
    with open(CONFIG, encoding="utf-8") as fh:
        return json.load(fh)


def leer_frontmatter(ruta: Path) -> tuple[dict, str]:
    """Devuelve (campos, cuerpo). Lee el subconjunto de YAML que usa el repo: `clave: valor` y listas
    `  - item`. Falla si el archivo trae BOM o no abre con `---`."""
    crudo = ruta.read_bytes()
    if crudo.startswith(b"\xef\xbb\xbf"):
        raise ErrorInstalacion(f"{ruta}: trae BOM; el frontmatter no se reconoce")
    texto = crudo.decode("utf-8").replace("\r\n", "\n")
    if not texto.startswith("---\n"):
        raise ErrorInstalacion(f"{ruta}: no abre con '---'")
    fin = texto.find("\n---", 4)
    if fin < 0:
        raise ErrorInstalacion(f"{ruta}: el frontmatter no cierra con '---'")
    campos: dict = {}
    clave = None
    for linea in texto[4:fin].split("\n"):
        if not linea.strip():
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", linea)
        if m:
            clave, valor = m.group(1), m.group(2).strip()
            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
                valor = valor[1:-1]
            campos[clave] = valor if valor else []
        elif clave and re.match(r"^\s+-\s+", linea):
            if not isinstance(campos.get(clave), list):
                campos[clave] = []
            campos[clave].append(re.sub(r"^\s+-\s+", "", linea).strip())
    cuerpo = texto[fin + 4:].lstrip("\n")
    return campos, cuerpo


def inventario() -> dict:
    skills = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
    agentes = sorted((REPO / "agents").glob("*.md"))
    comandos = sorted((REPO / "commands").glob("*.md"))
    return {"skills": skills, "agentes": agentes, "comandos": comandos}


def validar_skill(carpeta: Path) -> list[str]:
    """Errores duros contra la especificación Agent Skills. Los avisos van por avisos_skill()."""
    errores = []
    try:
        campos, _ = leer_frontmatter(carpeta / "SKILL.md")
    except (ErrorInstalacion, OSError, UnicodeDecodeError) as e:
        return [str(e)]
    nombre = campos.get("name", "")
    if not nombre:
        errores.append(f"{carpeta.name}: falta name")
    elif nombre != carpeta.name:
        errores.append(f"{carpeta.name}: name '{nombre}' no coincide con la carpeta")
    elif not NOMBRE_VALIDO.match(nombre) or len(nombre) > MAX_NOMBRE:
        errores.append(f"{carpeta.name}: name inválido (minúsculas, números y guiones, máx. {MAX_NOMBRE})")
    if not campos.get("description"):
        errores.append(f"{carpeta.name}: falta description")
    return errores


def avisos_skill(carpeta: Path) -> list[str]:
    campos, _ = leer_frontmatter(carpeta / "SKILL.md")
    largo = len(campos.get("description", ""))
    if largo > MAX_DESCRIPCION:
        return [f"{carpeta.name}: description de {largo} caracteres (el estándar Agent Skills y claude.ai "
                f"admiten {MAX_DESCRIPCION}; una plataforma estricta puede rechazarla o cortarla)"]
    return []


# ---------------------------------------------------------------- rutas

def entorno_base(destino: Path | None) -> dict:
    if destino is not None:
        home = destino.resolve()
        return {"HOME": home, "LOCALAPPDATA": home / "AppData" / "Local", "usar_variables": False}
    local = os.environ.get("LOCALAPPDATA", "").strip()
    return {"HOME": Path.home(),
            "LOCALAPPDATA": Path(local) if local else Path.home() / "AppData" / "Local",
            "usar_variables": True}


def resolver_raiz(spec: dict, base: dict) -> Path:
    variable = spec.get("variable")
    if variable and base["usar_variables"] and os.environ.get(variable, "").strip():
        return Path(os.path.expanduser(os.environ[variable].strip()))
    plantilla = spec.get("defecto_windows") if os.name == "nt" and spec.get("defecto_windows") else spec["defecto"]
    texto = plantilla.replace("{HOME}", str(base["HOME"])).replace("{LOCALAPPDATA}", str(base["LOCALAPPDATA"]))
    return Path(texto)


def rutas_plataforma(plat: dict, base: dict) -> dict:
    """Carpetas de destino de cada componente (o None si la plataforma no lo usa)."""
    rutas = {}
    for comp in ("skills", "agentes", "comandos"):
        spec = plat.get(comp)
        rutas[comp] = resolver_raiz(spec["raiz"], base) / spec["carpeta"] if spec else None
    rutas["raiz"] = rutas["skills"].parent if rutas["skills"] else None
    return rutas


# ---------------------------------------------------------------- operaciones de archivos

def es_enlace(p: Path) -> bool:
    if os.path.islink(p):
        return True
    if hasattr(os.path, "isjunction") and os.path.isjunction(p):
        return True
    try:
        atributos = os.lstat(p).st_file_attributes  # solo Windows
    except (AttributeError, OSError):
        return False
    return bool(atributos & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def borrar(p: Path) -> None:
    """Borra un archivo, una carpeta o un enlace. A un enlace o junction le quita SOLO el enlace:
    nunca entra al destino."""
    if es_enlace(p):
        if os.name == "nt" and p.is_dir():
            os.rmdir(p)  # en Windows, rmdir de un junction o symlink de carpeta quita el enlace
        else:
            os.unlink(p)
    elif p.is_dir():
        shutil.rmtree(p)
    elif p.exists():
        p.unlink()


def ignorar(patrones: list[str]):
    def _ignorar(_carpeta, nombres):
        return {n for n in nombres if any(fnmatch.fnmatch(n, pat) for pat in patrones)}
    return _ignorar


def enlazar_carpeta(origen: Path, destino: Path) -> None:
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(destino), str(origen)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise ErrorInstalacion(f"no se pudo crear el junction {destino}: {r.stdout}{r.stderr}")
    else:
        os.symlink(origen, destino, target_is_directory=True)


def escribir(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:  # sin BOM
        fh.write(texto)


# ---------------------------------------------------------------- conversión de agentes

def toml_cadena(texto: str) -> str:
    if "'''" not in texto and not texto.startswith("\n"):
        return "'''\n" + texto.rstrip("\n") + "\n'''"
    return json.dumps(texto, ensure_ascii=False)


def convertir_agente(origen: Path, formato: str) -> tuple[str, str]:
    """Devuelve (nombre_de_archivo, contenido) del agente en el formato de la plataforma."""
    if formato == "claude-md":
        return origen.name, origen.read_text(encoding="utf-8")
    campos, cuerpo = leer_frontmatter(origen)
    nombre = campos.get("name") or origen.stem
    descripcion = campos.get("description", "")
    if formato == "codex-toml":
        texto = (f"# Generado por instalar.py desde agents/{origen.name} de ingeniero-agentico.\n"
                 f"# Sin 'model': hereda el del agente que lo lanza.\n"
                 f"name = {json.dumps(nombre, ensure_ascii=False)}\n"
                 f"description = {json.dumps(descripcion, ensure_ascii=False)}\n"
                 f"developer_instructions = {toml_cadena(cuerpo)}\n")
        return f"{nombre}.toml", texto
    if formato in CAMPOS_AGENTE:
        frontmatter = (f"---\nname: {nombre}\n"
                       f"description: {json.dumps(descripcion, ensure_ascii=False)}\n---\n\n")
        aviso = (f"<!-- Generado por instalar.py desde agents/{origen.name}: se quitaron tools, model y "
                 f"skills porque usan nombres de Claude Code. -->\n\n")
        return origen.name, frontmatter + aviso + cuerpo
    raise ErrorInstalacion(f"formato de agente desconocido: {formato}")


# ---------------------------------------------------------------- manifiestos

def carpeta_manifiestos(rutas: dict) -> Path:
    return rutas["raiz"] / CARPETA_MANIFIESTOS


def leer_manifiesto(rutas: dict, clave: str) -> dict | None:
    ruta = carpeta_manifiestos(rutas) / f"{clave}.json"
    if not ruta.exists():
        return None
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def rutas_de_otros(rutas: dict, clave: str) -> set[str]:
    """Rutas que otro manifiesto de la misma raíz declara suyas (p. ej. codex y agents comparten
    ~/.agents/skills): esas no se borran."""
    propias = set()
    carpeta = carpeta_manifiestos(rutas)
    if carpeta.is_dir():
        for m in carpeta.glob("*.json"):
            if m.stem == clave:
                continue
            with open(m, encoding="utf-8") as fh:
                propias.update(json.load(fh).get("rutas", []))
    return propias


def todas_las_rutas_instaladas(rutas: dict) -> set[str]:
    return rutas_de_otros(rutas, "\0")


# ---------------------------------------------------------------- instalar en carpetas

def instalar_carpetas(clave: str, plat: dict, cfg: dict, base: dict, enlazar: bool, forzar: bool,
                      silencioso: bool = False) -> dict:
    inv = inventario()
    rutas = rutas_plataforma(plat, base)
    excluir = cfg.get("excluir", [])
    decir = (lambda *_: None) if silencioso else print

    errores = [e for s in inv["skills"] for e in validar_skill(REPO / "skills" / s)]
    if errores:
        raise ErrorInstalacion("skills inválidas, no se instala nada:\n  " + "\n  ".join(errores))
    for s in inv["skills"]:
        for aviso in avisos_skill(REPO / "skills" / s):
            decir(f"  aviso: {aviso}")

    # Plan completo antes de escribir nada.
    plan: list[tuple[str, Path, object]] = []
    for s in inv["skills"]:
        plan.append(("skill", rutas["skills"] / s, REPO / "skills" / s))
    if rutas["agentes"]:
        formato = plat["agentes"]["formato"]
        for a in inv["agentes"]:
            nombre, contenido = convertir_agente(a, formato)
            plan.append(("agente", rutas["agentes"] / nombre, contenido))
    if rutas["comandos"]:
        for c in inv["comandos"]:
            plan.append(("comando", rutas["comandos"] / c.name, c.read_text(encoding="utf-8")))
    plantilla_destino = rutas["raiz"] / cfg["plantilla_perfil"]
    if not enlazar:
        plan.append(("plantilla", plantilla_destino, REPO / cfg["plantilla_perfil"]))

    anterior = leer_manifiesto(rutas, clave) or {"rutas": []}
    nuestras = set(anterior.get("rutas", [])) | todas_las_rutas_instaladas(rutas)
    ajenas = [str(d) for tipo, d, _ in plan
              if tipo != "plantilla" and (d.exists() or es_enlace(d)) and str(d) not in nuestras]
    if ajenas and not forzar:
        raise ErrorInstalacion("ya existen y no las instaló este instalador (usa --forzar para "
                               "reemplazarlas):\n  " + "\n  ".join(ajenas))

    instaladas: list[str] = []
    for tipo, d, fuente in plan:
        if tipo == "plantilla":
            if d.exists() and str(d) not in nuestras:
                if d.read_bytes() != Path(fuente).read_bytes():
                    decir(f"  aviso: {d} ya existe y es distinta; se deja como está")
                continue  # no es nuestra: no se pisa ni se registra (desinstalar no la borrará)
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fuente, d)
            instaladas.append(str(d))
            continue
        if d.exists() or es_enlace(d):
            borrar(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        if tipo == "skill":
            if enlazar:
                enlazar_carpeta(Path(fuente), d)
            else:
                shutil.copytree(fuente, d, ignore=ignorar(excluir))
                for extra in cfg.get("extras", {}).get(d.name, []):
                    shutil.copyfile(REPO / extra, d / Path(extra).name)
        else:
            escribir(d, fuente)
        instaladas.append(str(d))

    manifiesto = {"plataforma": clave, "repo": "ingeniero-agentico", "version": version_plugin(),
                  "modo": "enlace" if enlazar else "copia",
                  "fecha": datetime.now().strftime("%d-%m-%Y %H:%M"), "rutas": instaladas}
    escribir(carpeta_manifiestos(rutas) / f"{clave}.json", json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n")

    decir(f"{plat['nombre']}: {len(inv['skills'])} skills en {rutas['skills']}"
          + (f" ({'enlaces' if enlazar else 'copias'})"))
    if rutas["agentes"]:
        decir(f"  agentes ({plat['agentes']['formato']}) en {rutas['agentes']}")
    if rutas["comandos"]:
        decir(f"  comandos en {rutas['comandos']}")
    if not enlazar:
        decir(f"  plantilla de perfil en {plantilla_destino}")
    decir(f"  orquestación: {plat.get('orquestacion', '')}")
    if plat.get("nota"):
        decir(f"  nota: {plat['nota']}")
    return rutas


def desinstalar_carpetas(clave: str, plat: dict, base: dict, silencioso: bool = False) -> int:
    rutas = rutas_plataforma(plat, base)
    decir = (lambda *_: None) if silencioso else print
    manifiesto = leer_manifiesto(rutas, clave)
    if manifiesto is None:
        decir(f"{plat['nombre']}: no hay instalación registrada en {carpeta_manifiestos(rutas)}")
        return 0
    compartidas = rutas_de_otros(rutas, clave)
    borradas = 0
    for r in manifiesto.get("rutas", []):
        p = Path(r)
        if r in compartidas:
            decir(f"  se conserva (la usa otra instalación): {p}")
            continue
        if p.exists() or es_enlace(p):
            borrar(p)
            borradas += 1
    (carpeta_manifiestos(rutas) / f"{clave}.json").unlink()
    for vacia in (carpeta_manifiestos(rutas), rutas["raiz"] / "perfiles"):
        try:
            vacia.rmdir()
        except OSError:
            pass
    decir(f"{plat['nombre']}: {borradas} elementos quitados")
    return borradas


# ---------------------------------------------------------------- claude-desktop (ZIP)

def version_plugin() -> str:
    try:
        with open(REPO / ".claude-plugin" / "plugin.json", encoding="utf-8") as fh:
            return json.load(fh).get("version", "")
    except OSError:
        return ""


def agregar_arbol(z: zipfile.ZipFile, origen: Path, prefijo: str, excluir: list[str]) -> None:
    for raiz, carpetas, archivos in os.walk(origen):
        carpetas[:] = sorted(c for c in carpetas if not any(fnmatch.fnmatch(c, p) for p in excluir))
        for a in sorted(archivos):
            if any(fnmatch.fnmatch(a, p) for p in excluir):
                continue
            ruta = Path(raiz) / a
            z.write(ruta, prefijo + ruta.relative_to(origen).as_posix())


def generar_zips(plat: dict, cfg: dict, salida: Path, silencioso: bool = False) -> list[Path]:
    inv = inventario()
    excluir = cfg.get("excluir", [])
    decir = (lambda *_: None) if silencioso else print
    errores = [e for s in inv["skills"] for e in validar_skill(REPO / "skills" / s)]
    if errores:
        raise ErrorInstalacion("skills inválidas:\n  " + "\n  ".join(errores))
    salida.mkdir(parents=True, exist_ok=True)
    hechos = []
    for s in inv["skills"]:
        destino = salida / f"{s}.zip"
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            agregar_arbol(z, REPO / "skills" / s, f"{s}/", excluir)
            for extra in cfg.get("extras", {}).get(s, []):
                z.write(REPO / extra, f"{s}/{Path(extra).name}")
        hechos.append(destino)
        for aviso in avisos_skill(REPO / "skills" / s):
            decir(f"  aviso: {aviso}")
    destino = salida / plat["zip_plugin"]
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for item in plat["zip_plugin_incluye"]:
            p = REPO / item
            if p.is_dir():
                agregar_arbol(z, p, f"ingeniero-agentico/{item}/", excluir)
            elif p.exists():
                z.write(p, f"ingeniero-agentico/{item}")
    hechos.append(destino)
    decir(f"{plat['nombre']}: {len(hechos) - 1} ZIP de skill + 1 ZIP del plugin en {salida}")
    decir("  skills: Customize > Skills > subir cada <skill>.zip (requiere ejecución de código)")
    decir(f"  plugin: Customize > Plugins > Add > Upload plugin > {plat['zip_plugin']}")
    return hechos


def salida_zips(plat: dict, destino: Path | None) -> Path:
    return destino.resolve() if destino else REPO / plat["salida"]


# ---------------------------------------------------------------- listar

def listar(cfg: dict, clave: str | None, destino: Path | None) -> None:
    inv = inventario()
    print(f"Repo: {len(inv['skills'])} skills ({', '.join(inv['skills'])}), "
          f"{len(inv['agentes'])} agentes, {len(inv['comandos'])} comandos · versión {version_plugin()}")
    base = entorno_base(destino)
    for k, plat in cfg["plataformas"].items():
        if clave and k != clave:
            continue
        print(f"\n[{k}] {plat['nombre']}")
        if plat["tipo"] == "zip":
            salida = salida_zips(plat, destino)
            zips = sorted(salida.glob("*.zip")) if salida.is_dir() else []
            print(f"  ZIP en {salida}: {len(zips)} generados")
            continue
        rutas = rutas_plataforma(plat, base)
        print(f"  skills   -> {rutas['skills']}")
        print(f"  agentes  -> {rutas['agentes'] or 'no aplica'}")
        print(f"  comandos -> {rutas['comandos'] or 'no aplica'}")
        m = leer_manifiesto(rutas, k)
        if m:
            presentes = [s for s in inv["skills"] if (rutas["skills"] / s / "SKILL.md").exists()]
            print(f"  instalado ({m['modo']}, {m['fecha']}, v{m.get('version', '')}): "
                  f"{len(presentes)}/{len(inv['skills'])} skills presentes")
        else:
            print("  no instalado por este instalador")


# ---------------------------------------------------------------- probar

def scripts_a_probar(carpeta_skill: Path) -> list[str]:
    texto = (carpeta_skill / "SKILL.md").read_text(encoding="utf-8")
    return sorted(set(re.findall(r"python3?\s+scripts/([\w.-]+\.py)\s+--probar", texto)))


def correr_probar(carpeta_skill: Path, home: Path) -> list[str]:
    fallas = []
    entorno = {k: v for k, v in os.environ.items() if k != "INGENIERO_DATOS"}
    entorno.update({"HOME": str(home), "USERPROFILE": str(home), "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONIOENCODING": "utf-8"})
    for script in scripts_a_probar(carpeta_skill):
        r = subprocess.run([sys.executable, str(carpeta_skill / "scripts" / script), "--probar"],
                           cwd=carpeta_skill, env=entorno, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        cola = (r.stdout.strip().splitlines() or [""])[-1]
        if r.returncode != 0 or "OK" not in cola:
            detalle = (r.stdout + r.stderr).strip().splitlines()[-3:]
            fallas.append(f"{carpeta_skill.name}/{script}: código {r.returncode} · " + " | ".join(detalle))
    return fallas


def sin_basura(carpeta: Path, excluir: list[str]) -> list[str]:
    malos = []
    for raiz, carpetas, archivos in os.walk(carpeta):
        for n in carpetas + archivos:
            if any(fnmatch.fnmatch(n, p) for p in excluir):
                malos.append(str(Path(raiz) / n))
    return malos


def verificar_carpetas(clave: str, plat: dict, cfg: dict, rutas: dict, home: Path, enlace: bool,
                       con_scripts: bool) -> list[str]:
    inv = inventario()
    fallas = []
    for s in inv["skills"]:
        d = rutas["skills"] / s
        if not (d / "SKILL.md").is_file():
            fallas.append(f"falta {d / 'SKILL.md'}")
            continue
        fallas += validar_skill(d)
        if enlace:
            if not es_enlace(d):
                fallas.append(f"{d} debía ser enlace")
            elif Path(os.path.realpath(d)) != (REPO / "skills" / s).resolve():
                fallas.append(f"{d} no resuelve al repo ({os.path.realpath(d)})")
        else:
            fallas += [f"basura instalada: {m}" for m in sin_basura(d, cfg.get("excluir", []))]
            for extra in cfg.get("extras", {}).get(s, []):
                if not (d / Path(extra).name).is_file():
                    fallas.append(f"falta extra {extra} en {d}")
    if not enlace and not (rutas["raiz"] / cfg["plantilla_perfil"]).is_file():
        fallas.append(f"falta la plantilla en {rutas['raiz'] / cfg['plantilla_perfil']}")
    if rutas["agentes"]:
        formato = plat["agentes"]["formato"]
        for a in inv["agentes"]:
            nombre, _ = convertir_agente(a, formato)
            p = rutas["agentes"] / nombre
            if not p.is_file():
                fallas.append(f"falta agente {p}")
                continue
            if p.read_bytes().startswith(b"\xef\xbb\xbf"):
                fallas.append(f"{p} trae BOM")
            if formato == "codex-toml":
                try:
                    import tomllib
                    datos = tomllib.loads(p.read_text(encoding="utf-8"))
                    for campo in ("name", "description", "developer_instructions"):
                        if not datos.get(campo):
                            fallas.append(f"{p}: falta {campo}")
                except ImportError:
                    pass
                except Exception as e:  # noqa: BLE001 (cualquier error de TOML es una falla)
                    fallas.append(f"{p}: TOML inválido ({e})")
            elif formato in CAMPOS_AGENTE:
                campos, _ = leer_frontmatter(p)
                sobran = set(campos) - set(CAMPOS_AGENTE[formato])
                if sobran or not campos.get("name") or not campos.get("description"):
                    fallas.append(f"{p}: frontmatter {sorted(campos)}")
            else:
                leer_frontmatter(p)
    if rutas["comandos"]:
        for c in inv["comandos"]:
            if not (rutas["comandos"] / c.name).is_file():
                fallas.append(f"falta comando {rutas['comandos'] / c.name}")
    if con_scripts:
        for s in inv["skills"]:
            fallas += correr_probar(rutas["skills"] / s, home)
    return fallas


def verificar_zips(plat: dict, cfg: dict, zips: list[Path]) -> list[str]:
    inv = inventario()
    fallas = []
    excluir = cfg.get("excluir", [])
    por_nombre = {z.stem: z for z in zips}
    for s in inv["skills"]:
        z = por_nombre.get(s)
        if z is None:
            fallas.append(f"falta {s}.zip")
            continue
        with zipfile.ZipFile(z) as zf:
            nombres = zf.namelist()
            if zf.testzip() is not None:
                fallas.append(f"{z.name}: ZIP corrupto")
        if any("\\" in n for n in nombres):
            fallas.append(f"{z.name}: rutas con barra invertida")
        if not all(n.startswith(f"{s}/") for n in nombres):
            fallas.append(f"{z.name}: hay entradas fuera de {s}/")
        if f"{s}/SKILL.md" not in nombres:
            fallas.append(f"{z.name}: falta {s}/SKILL.md en el primer nivel de la carpeta")
        if "SKILL.md" in nombres:
            fallas.append(f"{z.name}: SKILL.md suelto en la raíz del ZIP")
        if any(any(fnmatch.fnmatch(parte, p) for p in excluir) for n in nombres for parte in n.split("/")):
            fallas.append(f"{z.name}: trae archivos excluidos")
        for extra in cfg.get("extras", {}).get(s, []):
            if f"{s}/{Path(extra).name}" not in nombres:
                fallas.append(f"{z.name}: falta el extra {extra}")
    zp = por_nombre.get(Path(plat["zip_plugin"]).stem)
    if zp is None:
        fallas.append("falta el ZIP del plugin")
    else:
        with zipfile.ZipFile(zp) as zf:
            nombres = zf.namelist()
        tope = {n.split("/")[0] for n in nombres}
        if tope != {"ingeniero-agentico"}:
            fallas.append(f"{zp.name}: más de una carpeta de primer nivel ({sorted(tope)})")
        requeridos = ["ingeniero-agentico/.claude-plugin/plugin.json", "ingeniero-agentico/perfiles/_plantilla.yaml"]
        requeridos += [f"ingeniero-agentico/skills/{s}/SKILL.md" for s in inv["skills"]]
        with open(REPO / ".claude-plugin" / "plugin.json", encoding="utf-8") as fh:
            servidores = json.load(fh).get("mcpServers", {})
        for srv in servidores.values():  # cada script que el plugin lanza con ${CLAUDE_PLUGIN_ROOT} tiene que viajar
            for arg in srv.get("args", []):
                if "${CLAUDE_PLUGIN_ROOT}/" in arg:
                    requeridos.append("ingeniero-agentico/" + arg.split("${CLAUDE_PLUGIN_ROOT}/", 1)[1])
        fallas += [f"{zp.name}: falta {r}" for r in requeridos if r not in nombres]
        if any(n.startswith("ingeniero-agentico/bin/") for n in nombres):
            fallas.append(f"{zp.name}: trae bin/ (claude.ai rechaza el plugin)")
    return fallas


def probar(cfg: dict, con_scripts: bool) -> int:
    resultados = []
    with tempfile.TemporaryDirectory(prefix="ingeniero-agentico-prueba-") as tmp:
        tmp = Path(tmp)
        for clave, plat in cfg["plataformas"].items():
            home = tmp / clave
            home.mkdir()
            base = entorno_base(home)
            try:
                if plat["tipo"] == "zip":
                    zips = generar_zips(plat, cfg, home / "salida", silencioso=True)
                    fallas = verificar_zips(plat, cfg, zips)
                    detalle = f"{len(zips)} ZIP"
                else:
                    rutas = instalar_carpetas(clave, plat, cfg, base, enlazar=False, forzar=False, silencioso=True)
                    fallas = verificar_carpetas(clave, plat, cfg, rutas, home, enlace=False, con_scripts=con_scripts)
                    instalar_carpetas(clave, plat, cfg, base, enlazar=False, forzar=False, silencioso=True)  # reinstalar
                    desinstalar_carpetas(clave, plat, base, silencioso=True)
                    restos = [str(p) for p in (rutas["skills"], rutas["agentes"], rutas["comandos"]) if p and p.is_dir() and any(p.iterdir())]
                    if (rutas["raiz"] / cfg["plantilla_perfil"]).exists():
                        restos.append(str(rutas["raiz"] / cfg["plantilla_perfil"]))
                    fallas += [f"quedó después de desinstalar: {r}" for r in restos]
                    detalle = str(rutas["skills"].relative_to(home))
            except ErrorInstalacion as e:
                fallas, detalle = [str(e)], "error"
            resultados.append((clave, detalle, fallas))

        # Enlaces: instalar, verificar que resuelven al repo, desinstalar y comprobar que el repo sigue entero.
        home = tmp / "enlace"
        home.mkdir()
        plat = cfg["plataformas"]["agents"]
        base = entorno_base(home)
        try:
            rutas = instalar_carpetas("agents", plat, cfg, base, enlazar=True, forzar=False, silencioso=True)
            fallas = verificar_carpetas("agents", plat, cfg, rutas, home, enlace=True, con_scripts=False)
            if con_scripts:
                fallas += correr_probar(rutas["skills"] / "adquisiciones", home)
            desinstalar_carpetas("agents", plat, base, silencioso=True)
            fallas += [f"el repo perdió {s}/SKILL.md" for s in inventario()["skills"]
                       if not (REPO / "skills" / s / "SKILL.md").is_file()]
            if rutas["skills"].is_dir() and any(rutas["skills"].iterdir()):
                fallas.append("quedaron enlaces después de desinstalar")
        except ErrorInstalacion as e:
            fallas = [str(e)]
        resultados.append(("agents --enlazar", "junction" if os.name == "nt" else "symlink", fallas))

        # Dos instalaciones que comparten carpeta (codex y agents): quitar una no borra la otra.
        home = tmp / "compartida"
        home.mkdir()
        base = entorno_base(home)
        fallas = []
        try:
            instalar_carpetas("codex", cfg["plataformas"]["codex"], cfg, base, False, False, silencioso=True)
            r_ag = instalar_carpetas("agents", cfg["plataformas"]["agents"], cfg, base, False, False, silencioso=True)
            desinstalar_carpetas("codex", cfg["plataformas"]["codex"], base, silencioso=True)
            fallas += [f"desinstalar codex borró {s} de agents" for s in inventario()["skills"]
                       if not (r_ag["skills"] / s / "SKILL.md").is_file()]
            desinstalar_carpetas("agents", cfg["plataformas"]["agents"], base, silencioso=True)
            # Una carpeta ajena no se pisa sin --forzar.
            ajena = r_ag["skills"] / "orquestar"
            ajena.mkdir(parents=True)
            (ajena / "SKILL.md").write_text("---\nname: orquestar\ndescription: ajena\n---\n", encoding="utf-8")
            try:
                instalar_carpetas("agents", cfg["plataformas"]["agents"], cfg, base, False, False, silencioso=True)
                fallas.append("pisó una skill ajena sin --forzar")
            except ErrorInstalacion:
                pass
            if "ajena" not in (ajena / "SKILL.md").read_text(encoding="utf-8"):
                fallas.append("la skill ajena cambió")
        except ErrorInstalacion as e:
            fallas.append(str(e))
        resultados.append(("codex + agents", "carpeta compartida", fallas))

    print("Prueba del instalador (HOME temporal, nada toca la configuración real)")
    print(f"Scripts de cada método: {'se corren con --probar desde la copia instalada' if con_scripts else 'omitidos (--sin-scripts)'}\n")
    total = 0
    for clave, detalle, fallas in resultados:
        estado = "OK" if not fallas else f"FALLA ({len(fallas)})"
        print(f"  {clave:<18} {detalle:<34} {estado}")
        for f in fallas:
            print(f"      - {f}")
        total += len(fallas)
    avisos = [a for s in inventario()["skills"] for a in avisos_skill(REPO / "skills" / s)]
    for a in avisos:
        print(f"  aviso: {a}")
    print("\nOK" if total == 0 else f"\nFALLA: {total} problemas")
    return 0 if total == 0 else 1


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    cfg = cargar_config()
    ap = argparse.ArgumentParser(description="Instala ingeniero-agentico en una plataforma de agentes.")
    ap.add_argument("--plataforma", choices=sorted(cfg["plataformas"]))
    ap.add_argument("--destino", type=Path, help="carpeta que reemplaza a la del usuario (o carpeta de los ZIP)")
    ap.add_argument("--enlazar", action="store_true", help="enlaza las skills al repo en vez de copiarlas")
    ap.add_argument("--forzar", action="store_true", help="reemplaza skills con el mismo nombre que no instaló este instalador")
    ap.add_argument("--desinstalar", action="store_true")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--probar", action="store_true", help="instala en un HOME temporal y verifica cada plataforma")
    ap.add_argument("--sin-scripts", action="store_true", help="en --probar, no correr el --probar de cada método")
    a = ap.parse_args(argv)

    try:
        if a.probar:
            return probar(cfg, con_scripts=not a.sin_scripts)
        if a.listar:
            listar(cfg, a.plataforma, a.destino)
            return 0
        if not a.plataforma:
            ap.error("falta --plataforma (o usa --listar / --probar)")
        plat = cfg["plataformas"][a.plataforma]
        if plat["tipo"] == "zip":
            salida = salida_zips(plat, a.destino)
            if a.desinstalar:
                borrados = 0
                for z in sorted(salida.glob("*.zip")) if salida.is_dir() else []:
                    z.unlink()
                    borrados += 1
                print(f"{plat['nombre']}: {borrados} ZIP borrados de {salida} (lo ya subido a claude.ai se quita en Customize)")
                return 0
            if a.enlazar:
                print("aviso: --enlazar no aplica a claude-desktop; se generan ZIP")
            generar_zips(plat, cfg, salida)
            return 0
        base = entorno_base(a.destino)
        if a.desinstalar:
            desinstalar_carpetas(a.plataforma, plat, base)
        else:
            instalar_carpetas(a.plataforma, plat, cfg, base, a.enlazar, a.forzar)
        return 0
    except ErrorInstalacion as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
