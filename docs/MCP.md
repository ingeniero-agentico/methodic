# Servidor MCP · los métodos en cualquier cliente

`mcp/servidor.py` expone los métodos del repo por **MCP** (Model Context Protocol), para usarlos
desde Claude Desktop, Claude Code, Codex, Cursor, Gemini CLI, Hermes Agent o cualquier otro cliente
MCP. Es un solo archivo en Python estándar (3.11 o más nuevo), sin el SDK `mcp` ni otras dependencias.
Habla por **stdio**: el cliente lo lanza como subproceso.

**El servidor no calcula.** Escribe la entrada en una carpeta de trabajo, corre el script del método
con el mismo Python que lo ejecuta y devuelve lo que el script dejó (JSON, Excel y supuestos). Vale la
regla del repo: todo número sale de un script.

## Qué expone

### Herramientas

| Herramienta | Qué hace | Escribe |
|---|---|---|
| `listar_metodos` | Cada método y etapa: qué resuelve (la frase final de su `description`), qué entrada pide, con qué herramienta se corre y qué opciones acepta | No |
| `leer_metodo(metodo, parte)` | El texto de `SKILL.md` (`skill`), `GUIA.md` (`guia`), `plantillas/` (`plantilla`) o `fuentes.md` (`fuentes`) | No |
| `correr_metodo(metodo, entrada, perfil?, opciones?, caso?, archivos?)` | Corre `adquisiciones`, `costo-y-precio`, `evaluacion-economica` o `evaluacion-financiera`. Devuelve el JSON de salida, las rutas del Excel y los supuestos | Sí, en la carpeta de trabajo |
| `probar_metodo(metodo)` | Corre `--probar` del método (también de `cartografiar`, `investigar` y `auditar`) | No |
| `mapa_contexto(carpetas, salida, excluir?, nucleo?, marcar_leido?)` | Corre `skills/cartografiar/scripts/mapa_contexto.py`; devuelve el MODO, el núcleo y la ruta de `MAPA.md` | Sí, en `salida` |
| `validar_investigacion(ruta, umbral?)` | Corre `skills/investigar/scripts/validar_investigacion.py --json` | No |

Detalles de `correr_metodo`:

- `entrada` es el caso como objeto JSON, con la forma de la plantilla del método (`leer_metodo` con
  `parte: "plantilla"`).
- `perfil` es un nombre (se busca en `<datos>/perfiles/<nombre>.yaml`) o la ruta absoluta a un `.yaml`.
  Sin perfil, el script aplica su propia búsqueda.
- `opciones` acepta solo una lista blanca: `--tasa`, `--impuesto`, `--delta` y `--barrer` en
  `evaluacion-economica`; `--tasa`, `--impuesto` y `--proyecto` en `evaluacion-financiera`. Cualquier
  otra (`--salida`, `--perfil`, `--probar`) se rechaza.
- `archivos` lleva archivos de texto que acompañan la entrada, como `{nombre: contenido}`; por ejemplo,
  el CSV del flujo del proyecto de `evaluacion-financiera`.
- Los supuestos salen del campo `supuestos` del JSON cuando el método lo trae (los dos de evaluación
  y `adquisiciones`). `costo-y-precio` todavía no lo trae (es el punto 1 de la versión 1.1): ahí el
  servidor devuelve las líneas del texto del script que dicen `SUPUESTO`, y lo indica en
  `origen_supuestos`.

### Recursos

El `SKILL.md` y el `GUIA.md` de cada skill, con URI `ingeniero://skills/<metodo>/SKILL.md` y
`ingeniero://skills/<metodo>/GUIA.md` (`resources/list`, `resources/read`).

## Dónde quedan las salidas

La carpeta de datos se busca en el mismo orden que usan los scripts:

1. `--datos <carpeta>` al lanzar el servidor;
2. la variable de entorno `INGENIERO_DATOS`;
3. la carpeta hermana `../ingeniero-agentico-datos/`.

Cada corrida queda en `<base>/<caso>/<metodo>-<AAAAMMDD-HHMMSS>-<id>/`, con `entrada.json` y lo que
escribió el script. La base es, en orden:

1. `--trabajo <carpeta>`, si se dio;
2. `<datos>/casos/`, si hay carpeta de datos;
3. `<temporal del usuario>/ingeniero-agentico-mcp/`.

**Nunca dentro del repo.** El servidor se niega a arrancar si la carpeta de trabajo cae dentro del repo.

## Seguridad

- **Rutas.** Toda ruta que llega en un argumento tiene que ser absoluta, no puede traer `..` y tiene
  que caer dentro de una raíz permitida:
  - se puede **leer** del repo, de la carpeta de datos, de la de trabajo y de las raíces extra
    (`--raiz <carpeta>`, que se repite, o `INGENIERO_MCP_RAICES` con carpetas separadas por `;` en
    Windows o `:` en macOS y Linux);
  - se puede **escribir** en las mismas, menos el repo.
  
  Para mapear las carpetas de un encargo con `mapa_contexto`, esas carpetas tienen que estar en una
  raíz. Los campos de la entrada que el script abre como archivo (`perfil`, y `flujo_proyecto` en
  `evaluacion-financiera`) pasan por la misma validación.
- **Procesos.** Cada script corre con `sys.executable`, sin `shell=True` y con la entrada estándar
  cerrada. Hay un tiempo máximo por corrida (`--tiempo-max`, 300 s por defecto); si se pasa, el
  proceso se detiene. `notifications/cancelled` también lo detiene.
- **Tamaños.** La entrada y sus archivos pesan como máximo 2 MB. Una respuesta tiene como máximo
  `--max-respuesta` caracteres (400.000 por defecto): si el JSON no cabe, se devuelve su ruta.
- **El texto es dato.** Lo que el servidor lee de un archivo se devuelve como contenido; nunca se
  interpreta como instrucción.
- **Errores.** Una herramienta inexistente responde con el error JSON-RPC `-32602`. Un argumento mal
  dado (método inexistente, ruta con `..`, opción no permitida) responde con un resultado
  `isError: true` y el motivo, para que el modelo se corrija.

## Protocolo

El servidor sirve a clientes de **las dos eras** de MCP:

- **Moderna, 2026-07-28** (la revisión vigente al 15-10-2026). No hay handshake. Cada pedido trae
  `_meta["io.modelcontextprotocol/protocolVersion"]` y
  `_meta["io.modelcontextprotocol/clientCapabilities"]`. El servidor responde `server/discover`, pone
  `resultType: "complete"` y `serverInfo` en cada resultado, y `ttlMs`/`cacheScope` en las listas. Una
  versión que no soporta responde `-32022` con la lista de versiones que sí.
- **Legada, 2025-11-25, 2025-06-18, 2025-03-26 y 2024-11-05.** `initialize`, luego
  `notifications/initialized` y `ping`. Si el cliente pide una versión que no conoce, responde con
  2025-11-25.

Un mensaje JSON-RPC por línea (UTF-8). Por stdout sale solo protocolo; los avisos van a stderr.

Fuentes (leídas el 15-10-2026):

- Especificación vigente: https://modelcontextprotocol.io/specification/2026-07-28
- Cambios respecto de 2025-11-25: https://modelcontextprotocol.io/specification/2026-07-28/changelog
- Versiones y compatibilidad entre eras: https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
- `_meta` y códigos de error: https://modelcontextprotocol.io/specification/2026-07-28/basic/index
- `server/discover`: https://modelcontextprotocol.io/specification/2026-07-28/server/discover
- Transporte stdio: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio
- Herramientas y recursos: https://modelcontextprotocol.io/specification/2026-07-28/server/tools ·
  https://modelcontextprotocol.io/specification/2026-07-28/server/resources
- Handshake legado: https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle

## Antes de configurar un cliente

1. **Python 3.11 o más nuevo** y `openpyxl` (`python -m pip install openpyxl`); los scripts lo usan
   para el Excel.
2. Comprueba que arranca y mira qué raíces quedaron:

   ```
   python <ruta-al-repo>/mcp/servidor.py --comprobar
   ```

3. Prueba de punta a punta (termina en `OK`):

   ```
   python <ruta-al-repo>/mcp/probar_servidor.py
   ```

En los ejemplos, `<ruta-al-repo>` es la ruta absoluta de este repo y `<ruta-a-los-datos>` la de tu
carpeta de datos (la que tiene `perfiles/` y `casos/`). Si no tienes carpeta de datos, borra el
bloque `env` y las salidas irán al temporal.

**En Windows:**

- En JSON, escribe las rutas con barras normales (`D:/proyectos/ingeniero-agentico`) o con la
  barra invertida doble (`D:\\proyectos\\ingeniero-agentico`).
- Si `python` no está en el PATH del cliente (o abre la Microsoft Store), pon en `command` la ruta
  absoluta a `python.exe`, o usa `"command": "py"` con `"args": ["-3", "<ruta-al-repo>/mcp/servidor.py"]`.

**En macOS y Linux**, el comando suele ser `python3`.

Las plantillas listas están en `mcp/ejemplos/`. `probar_servidor.py` lee cada una y lanza el servidor
tal como lo haría el cliente.

## Configuración por cliente

### Claude Desktop

- Archivo `claude_desktop_config.json`; se abre desde Settings → Developer → Edit Config.
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Se agrega la entrada en `mcpServers` y se reinicia la aplicación por completo.
- Plantilla: `mcp/ejemplos/claude-desktop.json`.

```json
{
  "mcpServers": {
    "ingeniero-agentico": {
      "command": "python",
      "args": ["<ruta-al-repo>/mcp/servidor.py"],
      "env": { "INGENIERO_DATOS": "<ruta-a-los-datos>" }
    }
  }
}
```

Los registros quedan en `%APPDATA%\Claude\logs\mcp-server-ingeniero-agentico.log` (macOS:
`~/Library/Logs/Claude/`).
Fuente: https://modelcontextprotocol.io/docs/develop/connect-local-servers

### Claude Code

Por comando (todo lo que va después de `--` pasa intacto al servidor):

```
claude mcp add --transport stdio --scope project ingeniero-agentico -- python <ruta-al-repo>/mcp/servidor.py
```

- `--scope project` escribe `.mcp.json` en la raíz del proyecto. `local` (por defecto) y `user`
  escriben en `~/.claude.json`.
- Para pasar la carpeta de datos, agrega `--env INGENIERO_DATOS=<ruta-a-los-datos>` antes de
  `--transport`. Si el nombre del servidor va justo después de `--env`, el CLI lo lee como otro par
  `CLAVE=valor`.
- `claude mcp list` muestra el estado y `claude mcp get ingeniero-agentico` el detalle. La primera vez
  que se usa, un servidor de `.mcp.json` pide aprobación en la sesión interactiva.
- En `.mcp.json` se aceptan `${VAR}` y `${VAR:-defecto}`.
- Plantilla del `.mcp.json`: `mcp/ejemplos/claude-code.mcp.json`.

```json
{
  "mcpServers": {
    "ingeniero-agentico": {
      "type": "stdio",
      "command": "python",
      "args": ["<ruta-al-repo>/mcp/servidor.py"],
      "env": { "INGENIERO_DATOS": "<ruta-a-los-datos>" }
    }
  }
}
```

Fuente: https://code.claude.com/docs/en/mcp

### Codex (OpenAI)

- Archivo `~/.codex/config.toml`, o `.codex/config.toml` en un proyecto marcado como confiable.
- Sección `[mcp_servers.<nombre>]`.
- Por comando: `codex mcp add ingeniero-agentico --env INGENIERO_DATOS=<ruta-a-los-datos> -- python <ruta-al-repo>/mcp/servidor.py`.
- Plantilla: `mcp/ejemplos/codex.config.toml`.

```toml
[mcp_servers.ingeniero-agentico]
command = "python"
args = ["<ruta-al-repo>/mcp/servidor.py"]
startup_timeout_sec = 20
tool_timeout_sec = 300

[mcp_servers.ingeniero-agentico.env]
INGENIERO_DATOS = "<ruta-a-los-datos>"
```

`tool_timeout_sec` vale 60 por defecto; `cartografiar` sobre carpetas grandes puede tardar más, por
eso la plantilla lo sube a 300. En TOML, una ruta de Windows entre comillas dobles necesita `\\`:
usa `/` o comillas simples.
Fuente: https://developers.openai.com/codex/mcp (redirige a https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

### Cursor

- Archivo `.cursor/mcp.json` (del proyecto) o `~/.cursor/mcp.json` (global). Se reinicia Cursor
  después de cambiarlo.
- Acepta `${workspaceFolder}`, `${userHome}` y `${env:NOMBRE}`.
- Plantilla: `mcp/ejemplos/cursor.mcp.json`.

```json
{
  "mcpServers": {
    "ingeniero-agentico": {
      "type": "stdio",
      "command": "python",
      "args": ["<ruta-al-repo>/mcp/servidor.py"],
      "env": { "INGENIERO_DATOS": "<ruta-a-los-datos>" }
    }
  }
}
```

Fuente: https://cursor.com/docs/context/mcp

### Gemini CLI

- Archivo `~/.gemini/settings.json` (del usuario) o `.gemini/settings.json` (del proyecto).
- Clave `mcpServers`. `timeout` va en milisegundos (600000 por defecto).
- Por comando: `gemini mcp add -s user -e INGENIERO_DATOS=<ruta-a-los-datos> ingeniero-agentico python <ruta-al-repo>/mcp/servidor.py`.
  El alcance por defecto es `project`. Los argumentos del servidor que empiezan con guion van después
  de `--`.
- `/mcp` muestra el estado.
- Plantilla: `mcp/ejemplos/gemini.settings.json`.

```json
{
  "mcpServers": {
    "ingeniero-agentico": {
      "command": "python",
      "args": ["<ruta-al-repo>/mcp/servidor.py"],
      "env": { "INGENIERO_DATOS": "<ruta-a-los-datos>" },
      "timeout": 300000
    }
  }
}
```

Fuente: https://geminicli.com/docs/tools/mcp-server/ (el aviso de esa página dice que desde el
18-06-2026 Antigravity CLI reemplaza a Gemini CLI en el plan gratuito y en Google One).

### Hermes Agent (Nous Research)

- Archivo `config.yaml` del directorio de Hermes:
  - Windows: `%LOCALAPPDATA%\hermes\config.yaml`
  - Linux y macOS: `~/.hermes/config.yaml`
- Clave `mcp_servers`. Si ya existe, se suma la entrada.
- Plantilla: `mcp/ejemplos/hermes.config.yaml`.

```yaml
mcp_servers:
  ingeniero-agentico:
    command: "python"
    args: ["<ruta-al-repo>/mcp/servidor.py"]
    env:
      INGENIERO_DATOS: "<ruta-a-los-datos>"
    enabled: true
    timeout: 300          # segundos por llamada a una herramienta
    connect_timeout: 60   # segundos para arrancar y listar herramientas
```

- Por comando:
  `hermes mcp add ingeniero-agentico --command python --env INGENIERO_DATOS=<ruta-a-los-datos> --args <ruta-al-repo>/mcp/servidor.py`.
  `--args` va al final, porque toma todo lo que sigue.
- `hermes mcp test ingeniero-agentico` prueba la conexión y `/reload-mcp` recarga la configuración.
- Las herramientas aparecen como `mcp__ingeniero_agentico__<herramienta>`.
- La clave `protocol` (`auto`, que es el valor por defecto, `stateless` o `legacy`) elige la era.
  Con `auto` intenta primero `initialize`, y este servidor lo atiende.

Fuentes: https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference. Se verificó además
en el código instalado de Hermes Agent: `tools/mcp_tool_config.py` lee `mcp_servers`,
`tools/mcp_tool_transport.py` usa `command`, `args`, `env` y `cwd`, y `hermes_cli/subcommands/mcp.py`
define `hermes mcp add`.

### Resumen

| Cliente | Archivo de configuración | Plantilla | Fuente |
|---|---|---|---|
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` · `~/Library/Application Support/Claude/claude_desktop_config.json` | `claude-desktop.json` | modelcontextprotocol.io/docs/develop/connect-local-servers |
| Claude Code | `.mcp.json` (proyecto) · `~/.claude.json` (local, usuario) | `claude-code.mcp.json` | code.claude.com/docs/en/mcp |
| Codex | `~/.codex/config.toml` · `.codex/config.toml` | `codex.config.toml` | developers.openai.com/codex/mcp |
| Cursor | `.cursor/mcp.json` · `~/.cursor/mcp.json` | `cursor.mcp.json` | cursor.com/docs/context/mcp |
| Gemini CLI | `.gemini/settings.json` · `~/.gemini/settings.json` | `gemini.settings.json` | geminicli.com/docs/tools/mcp-server |
| Hermes Agent | `%LOCALAPPDATA%\hermes\config.yaml` · `~/.hermes/config.yaml` | `hermes.config.yaml` | hermes-agent.nousresearch.com/docs/reference/mcp-config-reference |

Otro cliente MCP con stdio sirve igual: comando `python`, argumento `<ruta-al-repo>/mcp/servidor.py`
y, si hace falta, la variable `INGENIERO_DATOS`.

## Opciones del servidor

| Opción | Qué hace |
|---|---|
| `--datos <carpeta>` | Carpeta de datos (`perfiles/` y `casos/`). Gana sobre `INGENIERO_DATOS` y la carpeta hermana |
| `--trabajo <carpeta>` | Dónde quedan las corridas. Gana sobre la carpeta de datos |
| `--raiz <carpeta>` | Raíz extra de lectura y escritura (se repite). También `INGENIERO_MCP_RAICES` |
| `--tiempo-max <s>` | Segundos máximos por corrida de un script (300) |
| `--max-respuesta <n>` | Caracteres máximos de una respuesta (400.000) |
| `--comprobar` | Muestra la configuración, las herramientas y los recursos, y sale |

## Límites conocidos

- **El perfil por defecto lo elige el script.** Sin `perfil`, cada script busca por su cuenta en
  `INGENIERO_DATOS` y en la carpeta hermana `../ingeniero-agentico-datos/`, aunque el servidor se
  haya lanzado con otro `--datos`. Para no depender de eso, pasa `perfil` explícito.
- **Las raíces se fijan al lanzar el servidor.** No usa *roots* del cliente (la revisión 2026-07-28
  los dejó obsoletos): una carpeta nueva se agrega con `--raiz` y reiniciando el servidor.
- **Una corrida bloquea hasta terminar.** No usa la extensión de tareas ni avisa progreso. El tiempo
  máximo por defecto es 300 s, y algunos clientes cortan antes (Codex, 60 s por defecto).
- **`costo-y-precio` no trae `supuestos` en su JSON**: los supuestos salen del texto del script hasta
  la versión 1.1.
- **`auditar` solo se prueba.** `recorrer.py` compara corridas archivadas y lo maneja el agente
  auditor, no tiene herramienta propia en el servidor.
- **Sin HTTP.** Solo stdio, el transporte que lanzan todos los clientes de la tabla.
