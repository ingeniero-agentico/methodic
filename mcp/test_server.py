#!/usr/bin/env python3
"""test_server.py · end-to-end test of the MCP server.

Launches mcp/server.py as a subprocess (stdio), with temporary data and work folders (it does not
touch the real data folder), and checks:

    1. legacy handshake (initialize 2025-11-25 + notifications/initialized + ping);
    2. modern era 2026-07-28 (server/discover, unsupported version, incomplete _meta);
    3. tools/list and resources/list|read;
    4. test_method of the four methods and of the support stages;
    5. run_method of economic-evaluation with its sample case: NPV and IRR against
       tests/expected.json, the Excel file, the assumptions and that the output stayed outside the repo;
    6. map_context and validate_research;
    7. clean errors: unknown tool, unknown method, path with «..», path outside the roots,
       output inside the repo and option not allowed;
    8. that the repo did not change and that the server exits when stdin closes;
    9. every template in mcp/examples/ starts the server the way its client would.

Usage:  python mcp/test_server.py [--test]      Ends in OK or FAIL.
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
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SERVER = HERE / "server.py"
MODERN = "2026-07-28"
META = {"io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientInfo": {"name": "test_server", "version": "1.1.0"},
        "io.modelcontextprotocol/clientCapabilities": {}}
CALC = ["procurement", "cost-and-pricing", "economic-evaluation", "financial-evaluation"]
SUPPORT = ["map-context", "research", "audit"]


class Client:
    def __init__(self, args, env):
        self.p = subprocess.Popen([sys.executable, str(SERVER), *args], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        self.inbox: queue.Queue = queue.Queue()
        self.junk: list = []
        self.stderr: list = []
        self.n = 0
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    def _read(self):
        for line in self.p.stdout:
            try:
                self.inbox.put(json.loads(line.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.junk.append(line)
        self.inbox.put(None)

    def _read_err(self):
        for line in self.p.stderr:
            self.stderr.append(line.decode("utf-8", "replace"))

    def send(self, msg):
        self.p.stdin.write((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
        self.p.stdin.flush()

    def request(self, method, params=None, timeout=180, modern=False):
        self.n += 1
        params = dict(params or {})
        if modern:
            params["_meta"] = META
        self.send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params})
        end = time.time() + timeout
        while True:
            msg = self.inbox.get(timeout=max(0.1, end - time.time()))
            if msg is None:
                raise RuntimeError("the server closed stdout")
            if msg.get("id") == self.n:
                return msg

    def tool(self, name, arguments, timeout=180):
        return self.request("tools/call", {"name": name, "arguments": arguments}, timeout)

    def close(self, timeout=15):
        self.p.stdin.close()
        try:
            return self.p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.p.kill()
            return None


WATCHED = ("skills", "profiles", "graph", "agents", "commands", "mcp")  # what the server or a script could touch


def repo_snapshot():
    """Files of the watched folders (others, like docs/ or install/, may change in parallel)."""
    out = {}
    for sub in WATCHED:
        for root, dirs, files in os.walk(REPO / sub):
            for f in files:
                p = Path(root) / f
                out[str(p.relative_to(REPO))] = p.stat().st_mtime_ns
    for root, dirs, _ in os.walk(REPO):
        dirs[:] = [d for d in dirs if d != ".git"]
        if Path(root).name == "__pycache__":
            out[f"{Path(root).relative_to(REPO)}/(__pycache__)"] = 0
    return out


def _hermes_yaml(text: str) -> dict:
    """Minimal reader for hermes.config.yaml (the standard library has no YAML)."""
    cfg, env, in_env = {}, {}, False
    for ln in text.splitlines():
        s = ln.split(" #")[0].rstrip()
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        indent, key, _, value = len(s) - len(s.lstrip()), *s.strip().partition(":")
        value = value.strip()
        if indent == 4:
            in_env = key == "env"
            if key in ("command", "args"):
                cfg[key] = json.loads(value)
        elif indent == 6 and in_env:
            env[key] = json.loads(value)
    return {"command": cfg.get("command"), "args": cfg.get("args", []), "env": env}


def read_examples() -> dict:
    """{file: (command, args, env)} of each template in mcp/examples/."""
    import tomllib
    ex = HERE / "examples"
    out = {}
    for p in sorted(ex.glob("*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))["mcpServers"]["methodic"]
        out[p.name] = (s["command"], s["args"], s.get("env", {}))
    for p in sorted(ex.glob("*.toml")):
        s = tomllib.loads(p.read_text(encoding="utf-8"))["mcp_servers"]["methodic"]
        out[p.name] = (s["command"], s["args"], s.get("env", {}))
    for p in sorted(ex.glob("*.yaml")):
        s = _hermes_yaml(p.read_text(encoding="utf-8"))
        out[p.name] = (s["command"], s["args"], s["env"])
    return out


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_test() -> int:
    failures: list[str] = []

    def check(cond, msg):
        print(("  ok    " if cond else "  FAIL  ") + msg)
        if not cond:
            failures.append(msg)
        return cond

    before = repo_snapshot()
    # resolve(): 8.3 short names on Windows CI and /var -> /private/var on macOS
    tmp = Path(tempfile.mkdtemp(prefix="test-mcp-")).resolve()
    data, work = tmp / "data", tmp / "work"
    (data / "profiles").mkdir(parents=True)
    work.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    for var in ("METHODIC_DATA", "INGENIERO_DATOS", "METHODIC_MCP_ROOTS", "INGENIERO_MCP_ROOTS", "INGENIERO_MCP_RAICES"):
        env.pop(var, None)
    cli = Client(["--data", str(data), "--work", str(work), "--max-time", "120"], env)
    try:
        print("1. Legacy handshake")
        r = cli.request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                       "clientInfo": {"name": "test_server", "version": "1.1.0"}})
        res = r.get("result", {})
        check(res.get("protocolVersion") == "2025-11-25", f"initialize answers 2025-11-25 ({res.get('protocolVersion')})")
        check(res.get("serverInfo", {}).get("name") == "methodic", "serverInfo.name = methodic")
        plugin_version = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        check(res.get("serverInfo", {}).get("version") == plugin_version,
              f"serverInfo.version = plugin.json version ({plugin_version})")
        check("tools" in res.get("capabilities", {}) and "resources" in res.get("capabilities", {}),
              "declares tools and resources")
        cli.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        r = cli.request("ping")
        check(r.get("result") == {}, "ping answers {}")
        r = cli.request("initialize", {"protocolVersion": "1999-01-01", "capabilities": {},
                                       "clientInfo": {"name": "x", "version": "0"}})
        check(r.get("result", {}).get("protocolVersion") == "2025-11-25",
              "with an unknown version it offers the latest legacy one")

        print("2. Modern era 2026-07-28")
        r = cli.request("server/discover", modern=True)
        res = r.get("result", {})
        check(MODERN in res.get("supportedVersions", []) and res.get("resultType") == "complete",
              f"server/discover: {res.get('supportedVersions')}")
        check(res.get("_meta", {}).get("io.modelcontextprotocol/serverInfo", {}).get("name") == "methodic",
              "serverInfo in _meta")
        cli.n += 1
        cli.send({"jsonrpc": "2.0", "id": cli.n, "method": "tools/list",
                  "params": {"_meta": {**META, "io.modelcontextprotocol/protocolVersion": "1900-01-01"}}})
        r = cli.inbox.get(timeout=30)
        check(r.get("error", {}).get("code") == -32022 and MODERN in r["error"].get("data", {}).get("supported", []),
              "unsupported version → -32022 with the list of versions")
        cli.n += 1
        cli.send({"jsonrpc": "2.0", "id": cli.n, "method": "tools/list",
                  "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": MODERN}}})
        r = cli.inbox.get(timeout=30)
        check(r.get("error", {}).get("code") == -32602, "without clientCapabilities → -32602")
        r = cli.request("tools/list", modern=True)
        res = r.get("result", {})
        check(res.get("resultType") == "complete" and "ttlMs" in res and "cacheScope" in res,
              "modern tools/list carries resultType, ttlMs and cacheScope")

        print("3. Tools and resources")
        r = cli.request("tools/list")
        names = sorted(t["name"] for t in r["result"]["tools"])
        expected_tools = sorted(["list_methods", "read_method", "run_method", "test_method",
                                 "map_context", "validate_research"])
        check(names == expected_tools, f"6 tools: {', '.join(names)}")
        check(all(t["inputSchema"].get("type") == "object" for t in r["result"]["tools"]),
              "every inputSchema is an object")
        r = cli.request("resources/list")
        uris = [x["uri"] for x in r["result"]["resources"]]
        uri = "methodic://skills/economic-evaluation/SKILL.md"
        check(uri in uris, f"{len(uris)} resources, among them {uri}")
        check(any(u.endswith("/GUIA.md") for u in uris), "the Spanish GUIA.md guides are resources")
        r = cli.request("resources/read", {"uri": uri})
        check(r["result"]["contents"][0]["text"].startswith("---"), "resources/read returns the SKILL.md")
        r = cli.request("resources/read", {"uri": uri.replace("methodic://", "ingeniero://")})
        check("result" in r and r["result"]["contents"][0]["text"].startswith("---"),
              "the legacy ingeniero:// URI is still read")
        r = cli.request("resources/read", {"uri": "methodic://skills/../CLAUDE.md"})
        check("error" in r and r["error"]["code"] == -32002, "unknown resource → error -32002 (legacy era)")
        r = cli.tool("list_methods", {})
        met = {m["method"]: m for m in r["result"]["structuredContent"]["methods"]}
        check(all(met.get(m, {}).get("tool") == "run_method" for m in CALC),
              "list_methods: the four methods run with run_method")
        check(all(m in met for m in SUPPORT + ["orchestrate"]), f"list_methods: {', '.join(sorted(met))}")
        r = cli.tool("read_method", {"method": "economic-evaluation", "part": "template"})
        files = r["result"]["structuredContent"]["files"]
        check(files and files[0]["file"].startswith("skills/economic-evaluation/templates/"),
              f"read_method returns the template ({files[0]['file'] if files else None})")
        r = cli.tool("read_method", {"metodo": "economic-evaluation", "parte": "plantilla"})
        sc = r["result"].get("structuredContent") or {}
        check(r["result"].get("isError") is False and sc.get("part") == "template",
              "1.0 argument names (metodo, parte: plantilla) are still translated")

        print("4. test_method")
        for m in CALC + SUPPORT:
            r = cli.tool("test_method", {"method": m}, timeout=180)
            sc = r["result"].get("structuredContent", {})
            check(sc.get("ok") is True, f"{m}: {sc.get('last_line', r['result'])}"[:150])

        print("5. run_method · economic-evaluation with the sample case")
        te = REPO / "skills" / "economic-evaluation" / "tests"
        case = load(te / "sample-case.json")
        exp = load(te / "expected.json")
        r = cli.tool("run_method", {"method": "economic-evaluation", "input": case,
                                    "profile": str(te / "sample-profile.yaml"), "case": "sample-van"})
        sc = r["result"].get("structuredContent", {})
        check(r["result"].get("isError") is False and sc.get("ok"), "ran without error")
        ind = (sc.get("result") or {}).get("indicators", {})
        npv, irr = ind.get("npv"), ind.get("irr")
        check(npv is not None and abs(npv - exp["npv"]) <= exp["currency_tolerance"],
              f"NPV {npv} = expected {exp['npv']} (tolerance {exp['currency_tolerance']})")
        check(irr is not None and abs(irr - exp["irr"]) <= exp["rate_tolerance"],
              f"IRR {irr} = expected {exp['irr']}")
        check(sc.get("excel") and all(Path(x).is_file() for x in sc["excel"]), f"Excel: {sc.get('excel')}")
        check(isinstance(sc.get("assumptions"), list) and len(sc["assumptions"]) > 0,
              f"{len(sc.get('assumptions') or [])} assumptions ({sc.get('assumptions_source')})")
        check(all(isinstance(a, dict) and {"parameter", "value", "origin", "text"} <= set(a)
                  for a in sc.get("assumptions") or [None]),
              "every assumption has parameter, value, origin and text")
        folder = Path(sc.get("folder", ""))
        check(str(folder).startswith(str(work)) and not str(folder).startswith(str(REPO)),
              "the run stayed in the work folder, outside the repo")
        r = cli.tool("run_method", {"method": "economic-evaluation", "input": case,
                                    "profile": str(te / "sample-profile.yaml"),
                                    "options": ["--tasa", "0.12"]})
        sc2 = r["result"].get("structuredContent", {})
        npv2 = ((sc2.get("result") or {}).get("indicators") or {}).get("npv")
        check(npv2 is not None and abs(npv2 - exp["npv"]) <= exp["currency_tolerance"],
              "with --tasa 0.12 (1.0 alias of --rate, the profile's rate) gives the same NPV")

        print("5b. run_method · the other three methods with their sample case")
        tf = REPO / "skills" / "financial-evaluation" / "tests"
        case_f = load(tf / "sample-case.json")
        exp_f = load(tf / "expected.json")
        flow_key = next(k for k in ("project_flow", "flujo_proyecto") if k in case_f)
        csv = (tf / case_f[flow_key]).read_text(encoding="utf-8")
        r = cli.tool("run_method", {"method": "financial-evaluation", "input": case_f,
                                    "profile": str(tf / "sample-profile.yaml"),
                                    "files": {case_f[flow_key]: csv}})
        sc = r["result"].get("structuredContent") or {}
        res = sc.get("result") or {}
        out_name = Path(sc.get("output_json") or "x").name
        check(out_name.endswith("-result.json") or out_name.endswith("-resultado.json"),
              f"financial-evaluation: main output is <case>-result(ado).json per language ({out_name})")
        check(res.get("winner") == exp_f["winner"]
              and abs((res.get("project_npv") or 0) - exp_f["project_npv"]) <= 1.0,
              f"financial-evaluation: {res.get('winner')} wins · project NPV {res.get('project_npv')} "
              f"(expected {exp_f['project_npv']})")
        tc = REPO / "skills" / "cost-and-pricing" / "tests"
        exp_c = load(tc / "expected.json")
        r = cli.tool("run_method", {"method": "cost-and-pricing", "input": load(tc / "sample-case.json"),
                                    "profile": str(tc / "sample-profile.yaml")})
        sc = r["result"].get("structuredContent") or {}
        res = sc.get("result") or {}
        prices = {k: (res.get("items") or {}).get(k, {}).get("unit_price") for k in exp_c["items"]}
        check(all(prices[k] is not None and abs(prices[k] - v["unit_price"]) <= 0.01
                  for k, v in exp_c["items"].items()), f"cost-and-pricing: prices {prices}")
        check(sc.get("assumptions_source", "").endswith("· assumptions"),
              f"cost-and-pricing: assumptions come from its JSON ({sc.get('assumptions_source')})")
        tp = REPO / "skills" / "procurement" / "tests"
        exp_p = load(tp / "expected.json")
        r = cli.tool("run_method", {"method": "procurement", "input": load(tp / "sample-case.json"),
                                    "profile": str(REPO / "profiles" / "_template.yaml")})
        sc = r["result"].get("structuredContent") or {}
        res = sc.get("result") or {}
        tot = res.get("totals") or {}
        check(all(isinstance(tot.get(k), (int, float)) and abs(tot[k] - v) <= 0.01
                  for k, v in exp_p["totals"].items() if isinstance(v, (int, float))),
              f"procurement: totals {tot}")
        check(sc.get("assumptions_source", "").endswith("· assumptions"),
              f"procurement: assumptions come from its JSON ({sc.get('assumptions_source')})")

        print("6. map_context and validate_research")
        map_out = work / "context-test"
        r = cli.tool("map_context", {"folders": [str(REPO / "skills" / "economic-evaluation")],
                                     "out": str(map_out)})
        sc = r["result"].get("structuredContent", {})
        check(sc.get("ok") and sc.get("mode") and (map_out / "MAP.md").is_file(),
              f"MODE {sc.get('mode')} · core {[n['file'] for n in sc.get('core', [])]} · MAP.md written")
        tr_ = REPO / "skills" / "research" / "tests"
        r = cli.tool("validate_research", {"path": str(tr_ / "sample-case.json")})
        sc = r["result"].get("structuredContent", {})
        check(sc.get("valid") is True, "research sample-case.json: valid")
        r = cli.tool("validate_research", {"path": str(tr_ / "case-with-errors.json")})
        sc = r["result"].get("structuredContent", {})
        check(sc.get("valid") is False and r["result"].get("isError") is False,
              "case-with-errors.json: not valid, reported as a result")

        print("7. Clean errors")
        r = cli.tool("does_not_exist", {})
        check(r.get("error", {}).get("code") == -32602, "unknown tool → JSON-RPC -32602")
        r = cli.tool("listar_metodos", {})
        check(r.get("error", {}).get("code") == -32602, "1.0 tool name listar_metodos → -32602 (renamed)")
        r = cli.tool("run_method", {"method": "made-up-method", "input": {"x": 1}})
        check(r["result"].get("isError") is True and "Unknown" in r["result"]["content"][0]["text"],
              "unknown method → isError with a message")
        r = cli.tool("test_method", {"method": "made-up-method"})
        check(r["result"].get("isError") is True, "test_method of an unknown method → isError")
        going_up = str(REPO / "skills" / ".." / ".." / "outside.json")
        r = cli.tool("validate_research", {"path": going_up})
        check(r["result"].get("isError") is True and "«..»" in r["result"]["content"][0]["text"],
              "path with «..» → isError")
        r = cli.tool("map_context", {"folders": [str(REPO)], "out": str(work / ".." / "x")})
        check(r["result"].get("isError") is True and "«..»" in r["result"]["content"][0]["text"],
              "out with «..» → isError")
        outside = Path(sys.executable).resolve()
        r = cli.tool("validate_research", {"path": str(outside)})
        check(r["result"].get("isError") is True and "outside the allowed roots" in r["result"]["content"][0]["text"],
              "path outside the roots → isError")
        r = cli.tool("map_context", {"folders": [str(REPO / "graph")], "out": str(REPO / "context")})
        check(r["result"].get("isError") is True and "inside the repo" in r["result"]["content"][0]["text"],
              "out inside the repo → isError")
        r = cli.tool("run_method", {"method": "economic-evaluation", "input": case,
                                    "options": ["--out", str(REPO)]})
        check(r["result"].get("isError") is True and "not allowed" in r["result"]["content"][0]["text"],
              "option --out not allowed → isError")
        r = cli.tool("run_method", {"method": "financial-evaluation",
                                    "input": {"case": "x", flow_key: str(outside)}})
        check(r["result"].get("isError") is True, f"input.{flow_key} outside the roots → isError")
        r = cli.request("made/up")
        check(r.get("error", {}).get("code") == -32601, "unknown JSON-RPC method → -32601")

        check(not cli.junk, f"stdout carries only JSON-RPC ({len(cli.junk)} foreign lines)")
    finally:
        code = cli.close()
        print("8. Shutdown and repo intact")
        check(code == 0, f"the server exits with 0 when stdin closes (exited {code})")
        after = repo_snapshot()
        new = sorted(set(after) - set(before))
        changed = sorted(k for k in before if k in after and before[k] != after[k])
        check(not new and not changed, f"the repo did not change (new {new[:5]}, changed {changed[:5]})")
        if failures and cli.stderr:
            print("server stderr:\n" + "".join(cli.stderr[-30:]))

    print("9. mcp/examples templates: each one starts the server exactly as its client writes it")
    try:
        for name, (cmd, args, env_cfg) in sorted(read_examples().items()):
            def fill(s: str) -> str:
                return s.replace("<path-to-repo>", REPO.as_posix()).replace("<path-to-data>", data.as_posix())
            args_f = [fill(a) for a in args]
            env_f = {**env, **{k: fill(v) for k, v in env_cfg.items()}}
            shape_ok = cmd == "python" and args_f and Path(args_f[0]).resolve() == SERVER \
                and env_cfg.get("METHODIC_DATA") == "<path-to-data>"
            c = Client(args_f[1:], env_f)  # the client's «python» = this interpreter
            try:
                r = c.request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                             "clientInfo": {"name": name, "version": "0"}}, timeout=30)
                c.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
                t = c.request("tools/list", timeout=30)
                n = len(t.get("result", {}).get("tools", []))
            finally:
                c.close()
            check(shape_ok and "result" in r and n == 6, f"{name}: correct shape, handshake and {n} tools")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("10. Output file patterns and the pre-v1.1 assumptions fallback (direct calls)")
    sys.path.insert(0, str(HERE))
    import server as srv
    for names, want in ((["x-resultado.json", "a.json"], "x-resultado.json"),
                        (["b.json", "caso-result.json"], "caso-result.json"),
                        (["a.json", "output-2.json"], "output-2.json"),
                        (["a.json", "salida.json"], "salida.json")):
        got = srv._main_json([Path(n) for n in names])
        check(got is not None and got.name == want, f"main output among {names}: {got.name if got else None}")
    old = {"supuestos": [{"parametro": "rate", "valor": 0.12, "origen": "profile", "marca": "SUPUESTO rate"}]}
    got, source = srv._assumptions(old, Path("salida.json"))
    check(got == [{"parameter": "rate", "value": 0.12, "origin": "profile", "text": "SUPUESTO rate"}]
          and "normalized" in source, f"old supuestos normalized: {got} ({source})")

    print("11. Data folder and roots: methodic names first, legacy names still honored (direct calls)")
    saved_env, saved_repo = dict(os.environ), srv.REPO
    tmp2 = Path(tempfile.mkdtemp(prefix="test-mcp-legacy-")).resolve()
    try:
        for var in ("METHODIC_DATA", "INGENIERO_DATOS", "METHODIC_MCP_ROOTS", "INGENIERO_MCP_ROOTS",
                    "INGENIERO_MCP_RAICES"):
            os.environ.pop(var, None)
        srv.REPO = tmp2 / "repo"           # a fake repo, so the real sibling data folder is never seen
        srv.REPO.mkdir()
        new_d, old_d = tmp2 / "new-data", tmp2 / "old-data"
        new_d.mkdir()
        old_d.mkdir()
        check(srv.Config._find_data(None) == (None, "none"), "no env var and no sibling folder → none")
        (tmp2 / "ingeniero-agentico-datos").mkdir()
        got = srv.Config._find_data(None)
        check(got[0] == tmp2 / "ingeniero-agentico-datos", f"legacy sibling ../ingeniero-agentico-datos is used ({got[1]})")
        (tmp2 / "methodic-data").mkdir()
        got = srv.Config._find_data(None)
        check(got[0] == tmp2 / "methodic-data", f"../methodic-data wins over the legacy sibling ({got[1]})")
        os.environ["INGENIERO_DATOS"] = str(old_d)
        got = srv.Config._find_data(None)
        check(got == (old_d, "INGENIERO_DATOS"), f"legacy $INGENIERO_DATOS wins over the siblings ({got[1]})")
        os.environ["METHODIC_DATA"] = str(new_d)
        got = srv.Config._find_data(None)
        check(got == (new_d, "METHODIC_DATA"), f"$METHODIC_DATA wins over $INGENIERO_DATOS ({got[1]})")
        os.environ["INGENIERO_MCP_ROOTS"] = str(tmp2 / "legacy-root")
        os.environ["METHODIC_MCP_ROOTS"] = str(tmp2 / "new-root")
        cfg = srv.Config(work=str(tmp2 / "work"))
        check(tmp2 / "legacy-root" in cfg.write_roots and tmp2 / "new-root" in cfg.write_roots,
              "METHODIC_MCP_ROOTS and the legacy INGENIERO_MCP_ROOTS both add roots")
    finally:
        os.environ.clear()
        os.environ.update(saved_env)
        srv.REPO = saved_repo
        shutil.rmtree(tmp2, ignore_errors=True)

    print("OK" if not failures else f"FAIL ({len(failures)})")
    return 0 if not failures else 1


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return run_test()


if __name__ == "__main__":
    sys.exit(main())
