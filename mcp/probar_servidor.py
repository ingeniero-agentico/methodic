#!/usr/bin/env python3
"""probar_servidor.py · prueba de punta a punta del servidor MCP.

Lanza mcp/servidor.py como subproceso (stdio), con una carpeta de datos y otra de trabajo
temporales (no toca la carpeta de datos real), y verifica:

    1. handshake legado (initialize 2025-11-25 + notifications/initialized + ping);
    2. era moderna 2026-07-28 (server/discover, versión no soportada, _meta incompleto);
    3. tools/list y resources/list|read;
    4. probar_metodo de los cuatro métodos y de las etapas de apoyo;
    5. correr_metodo de evaluacion-economica con su caso ficticio: el VAN y la TIR contra
       pruebas/esperado.json, el Excel, los supuestos y que la salida quedó fuera del repo;
    6. mapa_contexto y validar_investigacion;
    7. errores limpios: herramienta inexistente, método inexistente, ruta con «..», ruta fuera de
       las raíces, salida dentro del repo y opción no permitida;
    8. que el repo no cambió y que el servidor sale al cerrar stdin.

Uso:  python mcp/probar_servidor.py [--probar]      Termina en OK o FALLA.
"""
from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
SERVIDOR = AQUI / "servidor.py"
MODERNA = "2026-07-28"
META = {"io.modelcontextprotocol/protocolVersion": MODERNA,
        "io.modelcontextprotocol/clientInfo": {"name": "probar_servidor", "version": "1.0.0"},
        "io.modelcontextprotocol/clientCapabilities": {}}


class Cliente:
    def __init__(self, args, env):
        self.p = subprocess.Popen([sys.executable, str(SERVIDOR), *args], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        self.cola: queue.Queue = queue.Queue()
        self.basura: list = []
        self.stderr: list = []
        self.n = 0
        threading.Thread(target=self._leer, daemon=True).start()
        threading.Thread(target=self._leer_err, daemon=True).start()

    def _leer(self):
        for linea in self.p.stdout:
            try:
                self.cola.put(json.loads(linea.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.basura.append(linea)
        self.cola.put(None)

    def _leer_err(self):
        for linea in self.p.stderr:
            self.stderr.append(linea.decode("utf-8", "replace"))

    def enviar(self, msg):
        self.p.stdin.write((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
        self.p.stdin.flush()

    def pedir(self, metodo, params=None, timeout=180, moderno=False):
        self.n += 1
        params = dict(params or {})
        if moderno:
            params["_meta"] = META
        self.enviar({"jsonrpc": "2.0", "id": self.n, "method": metodo, "params": params})
        fin = time.time() + timeout
        while True:
            msg = self.cola.get(timeout=max(0.1, fin - time.time()))
            if msg is None:
                raise RuntimeError("el servidor cerró stdout")
            if msg.get("id") == self.n:
                return msg

    def herramienta(self, nombre, argumentos, timeout=180):
        return self.pedir("tools/call", {"name": nombre, "arguments": argumentos}, timeout)

    def cerrar(self, timeout=15):
        self.p.stdin.close()
        try:
            return self.p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.p.kill()
            return None


VIGILADAS = ("skills", "perfiles", "grafo", "agents", "commands", "mcp")  # lo que el servidor o un script podría tocar


def foto_repo():
    """Archivos de las carpetas vigiladas (otras, como docs/ o instalar/, pueden cambiar en paralelo)."""
    out = {}
    for sub in VIGILADAS:
        for raiz, dirs, archivos in os.walk(REPO / sub):
            for a in archivos:
                p = Path(raiz) / a
                out[str(p.relative_to(REPO))] = p.stat().st_mtime_ns
    for raiz, dirs, _ in os.walk(REPO):
        dirs[:] = [d for d in dirs if d != ".git"]
        if Path(raiz).name == "__pycache__":
            out[f"{Path(raiz).relative_to(REPO)}/(__pycache__)"] = 0
    return out


def _yaml_hermes(texto: str) -> dict:
    """Lector mínimo para hermes.config.yaml (la biblioteca estándar no trae YAML)."""
    cfg, env, en_env = {}, {}, False
    for ln in texto.splitlines():
        s = ln.split(" #")[0].rstrip()
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        sangria, clave, _, valor = len(s) - len(s.lstrip()), *s.strip().partition(":")
        valor = valor.strip()
        if sangria == 4:
            en_env = clave == "env"
            if clave in ("command", "args"):
                cfg[clave] = json.loads(valor)
        elif sangria == 6 and en_env:
            env[clave] = json.loads(valor)
    return {"command": cfg.get("command"), "args": cfg.get("args", []), "env": env}


def leer_ejemplos() -> dict:
    """{archivo: (command, args, env)} de cada plantilla de mcp/ejemplos/."""
    import tomllib
    ej = AQUI / "ejemplos"
    out = {}
    for p in sorted(ej.glob("*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))["mcpServers"]["ingeniero-agentico"]
        out[p.name] = (s["command"], s["args"], s.get("env", {}))
    for p in sorted(ej.glob("*.toml")):
        s = tomllib.loads(p.read_text(encoding="utf-8"))["mcp_servers"]["ingeniero-agentico"]
        out[p.name] = (s["command"], s["args"], s.get("env", {}))
    for p in sorted(ej.glob("*.yaml")):
        s = _yaml_hermes(p.read_text(encoding="utf-8"))
        out[p.name] = (s["command"], s["args"], s["env"])
    return out


def probar() -> int:
    fallas: list[str] = []

    def chequear(cond, msg):
        print(("  ok    " if cond else "  FALLA ") + msg)
        if not cond:
            fallas.append(msg)
        return cond

    antes = foto_repo()
    tmp = Path(tempfile.mkdtemp(prefix="probar-mcp-"))
    datos, trabajo = tmp / "datos", tmp / "trabajo"
    (datos / "perfiles").mkdir(parents=True)
    trabajo.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    env.pop("INGENIERO_DATOS", None)
    env.pop("INGENIERO_MCP_RAICES", None)
    cli = Cliente(["--datos", str(datos), "--trabajo", str(trabajo), "--tiempo-max", "120"], env)
    try:
        print("1. Handshake legado")
        r = cli.pedir("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                     "clientInfo": {"name": "probar_servidor", "version": "1.0.0"}})
        res = r.get("result", {})
        chequear(res.get("protocolVersion") == "2025-11-25", f"initialize responde 2025-11-25 ({res.get('protocolVersion')})")
        chequear(res.get("serverInfo", {}).get("name") == "ingeniero-agentico", "serverInfo.name = ingeniero-agentico")
        chequear("tools" in res.get("capabilities", {}) and "resources" in res.get("capabilities", {}),
                 "declara tools y resources")
        cli.enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
        r = cli.pedir("ping")
        chequear(r.get("result") == {}, "ping responde {}")
        r = cli.pedir("initialize", {"protocolVersion": "1999-01-01", "capabilities": {},
                                     "clientInfo": {"name": "x", "version": "0"}})
        chequear(r.get("result", {}).get("protocolVersion") == "2025-11-25",
                 "con una versión desconocida ofrece la última legada")

        print("2. Era moderna 2026-07-28")
        r = cli.pedir("server/discover", moderno=True)
        res = r.get("result", {})
        chequear(MODERNA in res.get("supportedVersions", []) and res.get("resultType") == "complete",
                 f"server/discover: {res.get('supportedVersions')}")
        chequear(res.get("_meta", {}).get("io.modelcontextprotocol/serverInfo", {}).get("name") == "ingeniero-agentico",
                 "serverInfo en _meta")
        cli.n += 1
        cli.enviar({"jsonrpc": "2.0", "id": cli.n, "method": "tools/list",
                    "params": {"_meta": {**META, "io.modelcontextprotocol/protocolVersion": "1900-01-01"}}})
        r = cli.cola.get(timeout=30)
        chequear(r.get("error", {}).get("code") == -32022 and MODERNA in r["error"].get("data", {}).get("supported", []),
                 "versión no soportada → -32022 con la lista de versiones")
        cli.n += 1
        cli.enviar({"jsonrpc": "2.0", "id": cli.n, "method": "tools/list",
                    "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": MODERNA}}})
        r = cli.cola.get(timeout=30)
        chequear(r.get("error", {}).get("code") == -32602, "sin clientCapabilities → -32602")
        r = cli.pedir("tools/list", moderno=True)
        res = r.get("result", {})
        chequear(res.get("resultType") == "complete" and "ttlMs" in res and "cacheScope" in res,
                 "tools/list moderno trae resultType, ttlMs y cacheScope")

        print("3. Herramientas y recursos")
        r = cli.pedir("tools/list")
        nombres = sorted(t["name"] for t in r["result"]["tools"])
        esperadas = sorted(["listar_metodos", "leer_metodo", "correr_metodo", "probar_metodo",
                            "mapa_contexto", "validar_investigacion"])
        chequear(nombres == esperadas, f"6 herramientas: {', '.join(nombres)}")
        chequear(all(t["inputSchema"].get("type") == "object" for t in r["result"]["tools"]),
                 "cada inputSchema es un objeto")
        r = cli.pedir("resources/list")
        uris = [x["uri"] for x in r["result"]["resources"]]
        uri = "ingeniero://skills/evaluacion-economica/SKILL.md"
        chequear(uri in uris, f"{len(uris)} recursos, entre ellos {uri}")
        r = cli.pedir("resources/read", {"uri": uri})
        chequear(r["result"]["contents"][0]["text"].startswith("---"), "resources/read devuelve el SKILL.md")
        r = cli.pedir("resources/read", {"uri": "ingeniero://skills/../CLAUDE.md"})
        chequear("error" in r and r["error"]["code"] == -32002, "recurso inexistente → error -32002 (era legada)")
        r = cli.herramienta("listar_metodos", {})
        met = {m["metodo"]: m for m in r["result"]["structuredContent"]["metodos"]}
        calc = ["adquisiciones", "costo-y-precio", "evaluacion-economica", "evaluacion-financiera"]
        chequear(all(met.get(m, {}).get("herramienta") == "correr_metodo" for m in calc),
                 "listar_metodos: los cuatro métodos corren con correr_metodo")
        r = cli.herramienta("leer_metodo", {"metodo": "evaluacion-economica", "parte": "plantilla"})
        arch = r["result"]["structuredContent"]["archivos"]
        chequear(arch and arch[0]["archivo"].endswith("plantillas/entrada.json"), "leer_metodo devuelve la plantilla")

        print("4. probar_metodo")
        for m in calc + ["cartografiar", "investigar", "auditar"]:
            r = cli.herramienta("probar_metodo", {"metodo": m}, timeout=180)
            sc = r["result"].get("structuredContent", {})
            chequear(sc.get("ok") is True, f"{m}: {sc.get('ultima_linea', r['result'])}"[:150])

        print("5. correr_metodo · evaluacion-economica con el caso ficticio")
        pr = REPO / "skills" / "evaluacion-economica" / "pruebas"
        caso = json.loads((pr / "caso-ficticio.json").read_text(encoding="utf-8"))
        esperado = json.loads((pr / "esperado.json").read_text(encoding="utf-8"))
        r = cli.herramienta("correr_metodo", {"metodo": "evaluacion-economica", "entrada": caso,
                                              "perfil": str(pr / "perfil-ficticio.yaml"), "caso": "furgon-ficticio"})
        sc = r["result"].get("structuredContent", {})
        chequear(r["result"].get("isError") is False and sc.get("ok"), "corrió sin error")
        ind = (sc.get("resultado") or {}).get("indicadores", {})
        van, tir = ind.get("van"), ind.get("tir")
        chequear(van is not None and abs(van - esperado["van"]) <= esperado["tolerancia_moneda"],
                 f"VAN {van} = esperado {esperado['van']} (tolerancia {esperado['tolerancia_moneda']})")
        chequear(tir is not None and abs(tir - esperado["tir"]) <= esperado["tolerancia_tasa"],
                 f"TIR {tir} = esperado {esperado['tir']}")
        chequear(sc.get("excel") and all(Path(x).is_file() for x in sc["excel"]), f"Excel: {sc.get('excel')}")
        chequear(isinstance(sc.get("supuestos"), list) and len(sc["supuestos"]) > 0,
                 f"{len(sc.get('supuestos') or [])} supuestos ({sc.get('origen_supuestos')})")
        carpeta = Path(sc.get("carpeta", ""))
        chequear(str(carpeta).startswith(str(trabajo)) and not str(carpeta).startswith(str(REPO)),
                 "la corrida quedó en la carpeta de trabajo, fuera del repo")
        r = cli.herramienta("correr_metodo", {"metodo": "evaluacion-economica", "entrada": caso,
                                              "perfil": str(pr / "perfil-ficticio.yaml"),
                                              "opciones": ["--tasa", "0.12"]})
        sc2 = r["result"].get("structuredContent", {})
        van2 = ((sc2.get("resultado") or {}).get("indicadores") or {}).get("van")
        chequear(van2 is not None and abs(van2 - esperado["van"]) <= esperado["tolerancia_moneda"],
                 "con --tasa 0.12 (la del perfil) da el mismo VAN")

        print("5b. correr_metodo · los otros tres métodos con su caso ficticio")
        pf = REPO / "skills" / "evaluacion-financiera" / "pruebas"
        caso_f = json.loads((pf / "caso-ficticio.json").read_text(encoding="utf-8"))
        esp_f = json.loads((pf / "esperado.json").read_text(encoding="utf-8"))
        csv = (pf / caso_f["flujo_proyecto"]).read_text(encoding="utf-8")
        r = cli.herramienta("correr_metodo", {"metodo": "evaluacion-financiera", "entrada": caso_f,
                                              "perfil": str(pf / "perfil-ficticio.yaml"),
                                              "archivos": {caso_f["flujo_proyecto"]: csv}})
        res = (r["result"].get("structuredContent") or {}).get("resultado") or {}
        chequear(res.get("ganadora") == esp_f["ganadora"]
                 and abs((res.get("van_proyecto") or 0) - esp_f["van_proyecto"]) <= 1.0,
                 f"evaluacion-financiera: gana {res.get('ganadora')} · VAN del proyecto {res.get('van_proyecto')} "
                 f"(esperado {esp_f['van_proyecto']})")
        pc = REPO / "skills" / "costo-y-precio" / "pruebas"
        esp_c = json.loads((pc / "esperado.json").read_text(encoding="utf-8"))
        r = cli.herramienta("correr_metodo", {"metodo": "costo-y-precio",
                                              "entrada": json.loads((pc / "caso-ficticio.json").read_text(encoding="utf-8")),
                                              "perfil": str(pc / "perfil-ficticio.yaml")})
        res = (r["result"].get("structuredContent") or {}).get("resultado") or {}
        precios = {k: (res.get("items") or {}).get(k, {}).get("precio_unit") for k in esp_c["items"]}
        chequear(all(precios[k] is not None and abs(precios[k] - v["precio_unit"]) <= 0.01
                     for k, v in esp_c["items"].items()), f"costo-y-precio: precios {precios}")
        pa = REPO / "skills" / "adquisiciones" / "pruebas"
        esp_a = json.loads((pa / "esperado.json").read_text(encoding="utf-8"))
        r = cli.herramienta("correr_metodo", {"metodo": "adquisiciones",
                                              "entrada": json.loads((pa / "caso-ficticio.json").read_text(encoding="utf-8")),
                                              "perfil": str(REPO / "perfiles" / "_plantilla.yaml")})
        res = (r["result"].get("structuredContent") or {}).get("resultado") or {}
        tot = res.get("totales") or {}
        chequear(all(isinstance(tot.get(k), (int, float)) and abs(tot[k] - v) <= 0.01
                     for k, v in esp_a["totales"].items() if isinstance(v, (int, float))),
                 f"adquisiciones: totales {tot}")

        print("6. mapa_contexto y validar_investigacion")
        salida_mapa = trabajo / "contexto-prueba"
        r = cli.herramienta("mapa_contexto", {"carpetas": [str(REPO / "skills" / "evaluacion-economica")],
                                              "salida": str(salida_mapa)})
        sc = r["result"].get("structuredContent", {})
        chequear(sc.get("ok") and sc.get("modo") and (salida_mapa / "MAPA.md").is_file(),
                 f"MODO {sc.get('modo')} · núcleo {[n['archivo'] for n in sc.get('nucleo', [])]} · MAPA.md escrito")
        inv = REPO / "skills" / "investigar" / "pruebas"
        r = cli.herramienta("validar_investigacion", {"ruta": str(inv / "caso-ficticio.json")})
        sc = r["result"].get("structuredContent", {})
        chequear(sc.get("valida") is True, "caso-ficticio.json de investigar: válido")
        r = cli.herramienta("validar_investigacion", {"ruta": str(inv / "caso-con-errores.json")})
        sc = r["result"].get("structuredContent", {})
        chequear(sc.get("valida") is False and r["result"].get("isError") is False,
                 "caso-con-errores.json: no válido, informado como resultado")

        print("7. Errores limpios")
        r = cli.herramienta("no_existe", {})
        chequear(r.get("error", {}).get("code") == -32602, "herramienta inexistente → JSON-RPC -32602")
        r = cli.herramienta("correr_metodo", {"metodo": "metodo-inventado", "entrada": {"x": 1}})
        chequear(r["result"].get("isError") is True and "desconocido" in r["result"]["content"][0]["text"],
                 "método inexistente → isError con mensaje")
        r = cli.herramienta("probar_metodo", {"metodo": "metodo-inventado"})
        chequear(r["result"].get("isError") is True, "probar_metodo de un método inexistente → isError")
        ruta_sube = str(REPO / "skills" / ".." / ".." / "fuera.json")
        r = cli.herramienta("validar_investigacion", {"ruta": ruta_sube})
        chequear(r["result"].get("isError") is True and "«..»" in r["result"]["content"][0]["text"],
                 "ruta con «..» → isError")
        r = cli.herramienta("mapa_contexto", {"carpetas": [str(REPO)], "salida": str(trabajo / ".." / "x")})
        chequear(r["result"].get("isError") is True and "«..»" in r["result"]["content"][0]["text"],
                 "salida con «..» → isError")
        fuera = Path(sys.executable).resolve()
        r = cli.herramienta("validar_investigacion", {"ruta": str(fuera)})
        chequear(r["result"].get("isError") is True and "fuera de las raíces" in r["result"]["content"][0]["text"],
                 "ruta fuera de las raíces → isError")
        r = cli.herramienta("mapa_contexto", {"carpetas": [str(REPO / "grafo")], "salida": str(REPO / "contexto")})
        chequear(r["result"].get("isError") is True and "dentro del repo" in r["result"]["content"][0]["text"],
                 "salida dentro del repo → isError")
        r = cli.herramienta("correr_metodo", {"metodo": "evaluacion-economica", "entrada": caso,
                                              "opciones": ["--salida", str(REPO)]})
        chequear(r["result"].get("isError") is True and "no permitida" in r["result"]["content"][0]["text"],
                 "opción --salida no permitida → isError")
        r = cli.herramienta("correr_metodo", {"metodo": "evaluacion-financiera",
                                              "entrada": {"caso": "x", "flujo_proyecto": str(fuera)}})
        chequear(r["result"].get("isError") is True, "entrada.flujo_proyecto fuera de las raíces → isError")
        r = cli.pedir("metodo/inventado")
        chequear(r.get("error", {}).get("code") == -32601, "método JSON-RPC desconocido → -32601")

        chequear(not cli.basura, f"stdout solo trae JSON-RPC ({len(cli.basura)} líneas ajenas)")
    finally:
        codigo = cli.cerrar()
        print("8. Cierre y repo intacto")
        chequear(codigo == 0, f"el servidor sale con 0 al cerrar stdin (salió {codigo})")
        despues = foto_repo()
        nuevos = sorted(set(despues) - set(antes))
        cambiados = sorted(k for k in antes if k in despues and antes[k] != despues[k])
        chequear(not nuevos and not cambiados, f"el repo no cambió (nuevos {nuevos[:5]}, cambiados {cambiados[:5]})")
        if fallas and cli.stderr:
            print("stderr del servidor:\n" + "".join(cli.stderr[-30:]))

    print("9. Plantillas de mcp/ejemplos: cada una arranca el servidor tal como la escribió el cliente")
    try:
        for nombre, (cmd, args, env_cfg) in sorted(leer_ejemplos().items()):
            def reemplazar(s: str) -> str:
                return s.replace("<ruta-al-repo>", REPO.as_posix()).replace("<ruta-a-los-datos>", datos.as_posix())
            args_r = [reemplazar(a) for a in args]
            env_r = {**env, **{k: reemplazar(v) for k, v in env_cfg.items()}}
            ok_forma = cmd == "python" and args_r and Path(args_r[0]).resolve() == SERVIDOR \
                and env_cfg.get("INGENIERO_DATOS") == "<ruta-a-los-datos>"
            c = Cliente(args_r[1:], env_r)  # «python» del cliente = este intérprete
            try:
                r = c.pedir("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                           "clientInfo": {"name": nombre, "version": "0"}}, timeout=30)
                c.enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
                t = c.pedir("tools/list", timeout=30)
                n = len(t.get("result", {}).get("tools", []))
            finally:
                c.cerrar()
            chequear(ok_forma and "result" in r and n == 6, f"{nombre}: forma correcta, handshake y {n} herramientas")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("OK" if not fallas else f"FALLA ({len(fallas)})")
    return 0 if not fallas else 1


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return probar()


if __name__ == "__main__":
    sys.exit(main())
