# Instalar ingeniero-agentico

Versión 1.0.0 · revisado contra la documentación de cada plataforma el 15-10-2026.

El repo se instala de dos formas: como **plugin** (Claude Code, Claude Desktop y claude.ai) o
copiando sus skills a la carpeta que lee cada agente con `instalar/instalar.py`. Las skills siguen
el estándar [Agent Skills](https://agentskills.io/specification), así que el mismo `SKILL.md` sirve en
todas; lo que cambia es dónde se ponen, si hay subagentes y cómo llegan los datos privados.

## Resumen

| Plataforma | Comando | Dónde quedan las skills | Orquestación |
|---|---|---|---|
| Claude Code | `/plugin marketplace add camiloalonsomerino-spec/ingeniero-agentico` y `/plugin install ingeniero-agentico@ingeniero-agentico` | caché de plugins (`~/.claude/plugins/`) | con agentes |
| Claude Code sin plugin | `python instalar/instalar.py --plataforma claude-code` | `~/.claude/skills/` | con agentes |
| Claude Desktop y claude.ai | `python instalar/instalar.py --plataforma claude-desktop` y subir los ZIP | tu cuenta (Customize) | chat: en secuencia · Cowork: con agentes |
| Codex | `python instalar/instalar.py --plataforma codex` | `~/.agents/skills/` | subagentes TOML o en secuencia |
| Cursor | `python instalar/instalar.py --plataforma cursor` | `~/.cursor/skills/` | subagentes o en secuencia |
| Gemini CLI | `python instalar/instalar.py --plataforma gemini` | `~/.gemini/skills/` | subagentes o en secuencia |
| Hermes Agent | `python instalar/instalar.py --plataforma hermes` | `%LOCALAPPDATA%\hermes\skills\` (Windows) · `~/.hermes/skills/` | `delegate_task` o en secuencia |
| Otro agente con Agent Skills | `python instalar/instalar.py --plataforma agents` | `~/.agents/skills/` | en secuencia |

Antes de cualquiera: Python 3.11 o superior con `openpyxl` (`python -m pip install openpyxl`), y
acceso al repo (es privado: necesitas permiso en GitHub y credenciales de git en tu equipo).

La tabla completa de rutas, con la URL que respalda cada una, está en `instalar/plataformas.json`.

## Los datos privados, en todas

Los scripts buscan el perfil de la empresa así: `--perfil` · variable `INGENIERO_DATOS` · carpeta
hermana `ingeniero-agentico-datos/` · plantilla del repo (todo sale `SUPUESTO`). La carpeta hermana
depende de dónde quedó instalado el script:

| Instalación | «Carpeta hermana» que busca el script |
|---|---|
| Repo clonado o `--enlazar` | junto al repo: `<carpeta del repo>/../ingeniero-agentico-datos/` |
| Copia en Claude Code, Codex, Cursor, Gemini o `agents` | `~/ingeniero-agentico-datos/` |
| Copia en Hermes (Windows) | `%LOCALAPPDATA%\ingeniero-agentico-datos\` |
| Plugin de Claude Code | ninguna útil (queda dentro de la caché): usa `INGENIERO_DATOS` |
| claude.ai (sandbox) | no existe: sube el perfil al chat y pásalo con `--perfil` |

**Lo seguro es definir `INGENIERO_DATOS`** con la ruta de tu carpeta de datos. Nunca pongas un
perfil real dentro del repo ni dentro de la carpeta de skills instalada.

---

## Claude Code

### Como plugin (recomendado)

Dentro de una sesión de Claude Code:

```
/plugin marketplace add camiloalonsomerino-spec/ingeniero-agentico
/plugin install ingeniero-agentico@ingeniero-agentico
```

Desde la versión 2.1.275 basta una línea: `/plugin install ingeniero-agentico --marketplace camiloalonsomerino-spec/ingeniero-agentico`.
Desde la terminal, lo mismo con `claude plugin marketplace add ...` y `claude plugin install ...`.

- **Repo privado.** Claude Code clona con el git de tu equipo y sin preguntar contraseña. Antes,
  `gh auth login` y `gh auth setup-git` (HTTPS), o una llave SSH cargada en `ssh-agent`. Sin llave
  SSH, define `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`.
- **Rama.** El catálogo se lee de la rama por defecto (`main`). Mientras esto viva en otra rama:
  `/plugin marketplace add camiloalonsomerino-spec/ingeniero-agentico#plataformas`.
- **Nombres.** Las skills quedan con prefijo: `/ingeniero-agentico:orquestar`,
  `/ingeniero-agentico:nuevo-encargo`; los agentes, `ingeniero-agentico:cartografo`, etc.
- **Actualizar.** `plugin.json` fija `"version": "1.0.0"`: quien instaló no recibe cambios hasta que
  la versión sube. Cada entrega nueva sube la versión. El usuario actualiza con
  `/plugin marketplace update ingeniero-agentico`.
- **Datos.** En `~/.claude/settings.json`: `"env": { "INGENIERO_DATOS": "<ruta a ingeniero-agentico-datos>" }`.

**El servidor MCP viene incluido.** `plugin.json` declara en `mcpServers` el servidor de `mcp/servidor.py`
(detalle en `docs/MCP.md`), así que `/plugin install` lo registra solo, como
`plugin:ingeniero-agentico:ingeniero-agentico`. Se lanza con `${CLAUDE_PLUGIN_ROOT}/mcp/servidor.py`
y tres opciones del plugin (`userConfig`), que se cambian con `/plugin configure ingeniero-agentico@ingeniero-agentico`
o al instalar con `--config CLAVE=valor`:

| Opción | Por defecto | Qué es |
|---|---|---|
| `python` | `python` | El comando que lanza el servidor. En Windows sirve `python` (si está en el PATH) o `py`; en macOS y Linux, `python3`; o la ruta absoluta al ejecutable |
| `datos` | vacío | Carpeta de datos; pasa al servidor como `INGENIERO_DATOS`. Vacío: el servidor usa la variable del entorno o la carpeta temporal |
| `raices` | vacío | Carpetas extra que el servidor puede leer y escribir (`INGENIERO_MCP_RAICES`), separadas por `;` en Windows y `:` en macOS y Linux |

Ejemplo desde la terminal: `claude plugin install ingeniero-agentico@ingeniero-agentico --config python=py --config datos=D:/ingeniero-agentico-datos`.
El servidor exige rutas absolutas dentro de una raíz permitida (el plugin, `datos`, la carpeta de
trabajo y `raices`): para mapear las carpetas de un encargo con `mapa_contexto`, agrégalas a `raices`.

Verificado en este equipo con una configuración temporal (`CLAUDE_CONFIG_DIR`): el marketplace se
agrega, el plugin se instala, `claude plugin details ingeniero-agentico` lista 9 skills (las 8 más
`nuevo-encargo`), 4 agentes y 1 servidor MCP, y `claude mcp list` lo muestra conectado tanto con
`python` como con `--config python=py --config datos=<carpeta>`. `claude plugin validate .` pasa con
un aviso: el `CLAUDE.md` de la raíz no se carga como contexto del plugin (es para quien desarrolla el
repo, no para quien lo usa).

### Sin plugin

```
python instalar/instalar.py --plataforma claude-code
```

Copia `skills/` a `~/.claude/skills/`, `agents/` a `~/.claude/agents/`, `commands/` a
`~/.claude/commands/` y la plantilla de perfil a `~/.claude/perfiles/_plantilla.yaml`. Respeta
`CLAUDE_CONFIG_DIR`. No instales las dos vías a la vez: verías cada skill dos veces. Esta vía no
registra el servidor MCP: si lo quieres, agrégalo con `claude mcp add` (ver `docs/MCP.md`).

**Qué funciona:** todo. Es la única plataforma donde la orquestación fue diseñada y probada con agentes.

---

## Claude Desktop y claude.ai

```
python instalar/instalar.py --plataforma claude-desktop
```

Deja en `instalar/salida/claude-desktop/` (ignorada por git):

- un ZIP por skill (`orquestar.zip`, `adquisiciones.zip`, ...), cada uno con la carpeta `<skill>/`
  como único primer nivel, que es lo que exige claude.ai;
- `ingeniero-agentico-plugin.zip`, el plugin completo en una carpeta `ingeniero-agentico/` (incluye
  `mcp/`, porque `plugin.json` declara el servidor MCP).

Súbelos de una de estas formas:

1. **Una skill a la vez:** Customize > Skills > subir el ZIP, y activarla.
2. **El plugin completo:** Customize > Plugins > Add > Upload plugin > `ingeniero-agentico-plugin.zip`.
3. **Desde GitHub:** Customize > Plugins > Add > Add marketplace con la URL del repo (claude.ai
   tiene que poder leer el repo privado; si no, usa la opción 2).

Requisitos: plan Pro, Max, Team o Enterprise, con **ejecución de código activada**: sin ella los
scripts no corren y el método no entrega números.

**Qué funciona y qué no:**

| | Chat | Cowork |
|---|---|---|
| Skills y scripts | sí, en el sandbox de ejecución de código | sí |
| `commands/` | se carga como skill (no hay `/nuevo-encargo`) | sí |
| `agents/` | se ignora: `orquestar` corre **en secuencia** | se carga |
| Servidor MCP del plugin (local) | se ignora | arranca si la sesión corre en tu equipo |
| Carpeta de datos | no existe | la de tu equipo, si Cowork corre local |

**Datos privados:** el sandbox no ve tu disco. Sube el perfil YAML y los archivos del caso al chat y
corre los scripts con `--perfil <ruta del archivo subido>`. En los ZIP de una skill la plantilla de
perfil no viaja (los scripts la buscan tres carpetas arriba, fuera de la skill), así que **siempre
pasa `--perfil`**: probado, `evaluacion-financiera` sin perfil ni plantilla se detiene con
«No encontré el perfil». Para `auditar`, pasa los scripts con ruta absoluta. Lo que se genera queda
en el sandbox: descárgalo, porque no persiste entre conversaciones.

**Aviso:** las descripciones de `evaluacion-economica` (1.077 caracteres) y `evaluacion-financiera`
(1.091) superan los 1.024 que admiten claude.ai y el estándar. Si la subida las rechaza, hay que
acortarlas en su `SKILL.md`.

Fuentes: [Create custom skills](https://claude.com/docs/skills/how-to) ·
[Plugin structure and testing](https://claude.com/docs/plugins/build) ·
[Plugin support by app](https://claude.com/docs/plugins/platform-support).

---

## Codex (OpenAI)

```
python instalar/instalar.py --plataforma codex
```

- Skills en `~/.agents/skills/` (la carpeta de usuario que lee Codex; también la leen Cursor y Gemini).
- Agentes convertidos a TOML en `~/.codex/agents/` (respeta `CODEX_HOME`): cada uno con `name`,
  `description` y `developer_instructions` (el cuerpo del `.md`). Sin `model`: heredan el de la sesión.
- Se invocan con `$orquestar` o desde `/skills`; Codex también elige una skill sola por su descripción.
- Al abrir el repo, Codex lee `AGENTS.md` (instrucciones neutrales y el modo «sin agentes»).

**Qué funciona:** skills y scripts completos. Codex lanza subagentes cuando la instrucción lo pide,
así que `orquestar` puede delegar; si no lo hace, corre las etapas en secuencia con la aprobación del
plan como puerta. `/nuevo-encargo` no existe: usa `$orquestar`. Los agentes convertidos no fueron
probados dentro de Codex (no está instalado en este equipo); el instalador verifica que el TOML se lee.

**Datos:** define `INGENIERO_DATOS` en el entorno antes de abrir Codex, o usa `~/ingeniero-agentico-datos/`.

Fuentes: [Skills](https://developers.openai.com/codex/skills) ·
[Subagents](https://developers.openai.com/codex/subagents) ·
[AGENTS.md](https://developers.openai.com/codex/guides/agents-md).

---

## Cursor

```
python instalar/instalar.py --plataforma cursor
```

- Skills en `~/.cursor/skills/`; agentes en `~/.cursor/agents/` solo con `name` y `description`
  (las herramientas y modelos de Claude Code no valen en Cursor, así que heredan los de la sesión).
- Cursor también lee `~/.claude/skills/`, `~/.codex/skills/` y `~/.agents/skills/`: si ya instalaste
  para Claude Code o Codex, no repitas (evitas duplicados).
- Se invoca escribiendo `/orquestar` en el chat del agente. Lee `AGENTS.md` al abrir el repo.

**Qué funciona:** skills, scripts y subagentes. No hay `/nuevo-encargo` (Cursor está pasando los
comandos a skills). No probado dentro de Cursor (no está instalado en este equipo).

Fuentes: [Skills](https://cursor.com/docs/context/skills) ·
[Subagents](https://cursor.com/docs/context/subagents) · [Rules y AGENTS.md](https://cursor.com/docs/context/rules).

---

## Gemini CLI

```
python instalar/instalar.py --plataforma gemini
```

- Skills en `~/.gemini/skills/`; agentes en `~/.gemini/agents/` solo con `name` y `description`.
- Gemini pide permiso la primera vez que activa una skill (`activate_skill`): acéptalo.
- Gemini lee `GEMINI.md`, no `AGENTS.md`. El `GEMINI.md` del repo solo importa `AGENTS.md`
  (`@./AGENTS.md`), así que hay una sola fuente de instrucciones.
- Gemini también lee `~/.agents/skills/` (con precedencia): si instalaste para Codex, ya las tiene.

**Qué funciona:** skills, scripts y subagentes (un subagente no lanza a otro, igual que en Claude
Code). Sin `/nuevo-encargo`. No probado dentro de Gemini (no está instalado en este equipo).

Fuentes: [Agent Skills](https://geminicli.com/docs/cli/skills/) ·
[Subagents](https://geminicli.com/docs/core/subagents/) · [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/) ·
[Imports](https://geminicli.com/docs/reference/memport/).

---

## Hermes Agent (Nous Research)

```
python instalar/instalar.py --plataforma hermes
```

Copia las skills a `HERMES_HOME/skills/` (en Windows `%LOCALAPPDATA%\hermes\skills\`; en macOS y
Linux `~/.hermes/skills/`; respeta `HERMES_HOME`) y la plantilla a `HERMES_HOME/perfiles/`. Hermes
busca `SKILL.md` en toda la carpeta, así que no hace falta una categoría. Cada skill queda como
comando: `/orquestar`, `/adquisiciones`, etc.

**Alternativa sin copiar** (las skills se leen del repo y se actualizan con `git pull`): agrega la
carpeta `skills/` del repo en `config.yaml`. El instalador no toca `config.yaml`; lo editas tú:

```yaml
skills:
  external_dirs:
    - <ruta al repo>/skills
```

- **Contexto:** al abrir el repo, Hermes carga un solo archivo de proyecto, el primero que encuentra
  (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, ...). Carga `AGENTS.md`, no `CLAUDE.md`.
- **Delegación:** Hermes no lee archivos de agentes; delega con la herramienta `delegate_task`
  (hijos genéricos con `goal` y `context`). `orquestar` puede pasarle como contexto el archivo de
  `agents/` de cada etapa, o correr en secuencia.
- **Curador:** el curador de Hermes solo mantiene skills creadas por el propio agente; estas quedan
  «sin marca de origen» y no las archiva. Pero si el agente usa `skill_manage` puede editarlas donde
  estén: reinstalar las deja como en el repo.
- **Datos:** define `INGENIERO_DATOS` en el entorno del sistema (Hermes reserva su `.env` para
  secretos), o pasa `--perfil`.
- **MCP:** ver `docs/MCP.md`.

**Qué funciona:** skills y scripts; verificado contra el código instalado (v0.21.4): `get_skills_dir()`
es `HERMES_HOME/skills` y la búsqueda de `SKILL.md` es recursiva.

Fuentes: [Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) ·
[Delegation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) ·
[Context files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files).

---

## Cualquier otro agente compatible con Agent Skills

```
python instalar/instalar.py --plataforma agents
```

Copia solo las skills a `~/.agents/skills/`, la carpeta compartida que leen Codex, Cursor y Gemini
CLI. Si tu agente usa otra carpeta, pasa la de tu usuario con `--destino` o copia `skills/<nombre>/`
a mano: cada carpeta es autosuficiente salvo la plantilla de perfil (que va en
`<carpeta de configuración>/perfiles/_plantilla.yaml`). Sin subagentes: `orquestar` corre en secuencia.

---

## `instalar.py`

```
python instalar/instalar.py --plataforma <p> [--destino <carpeta>] [--enlazar] [--forzar]
python instalar/instalar.py --plataforma <p> --desinstalar [--destino <carpeta>]
python instalar/instalar.py --listar [--plataforma <p>] [--destino <carpeta>]
python instalar/instalar.py --probar [--sin-scripts]
```

| Opción | Qué hace |
|---|---|
| `--destino` | Reemplaza tu carpeta de usuario: instala en `<destino>/.claude/...`, `<destino>/.agents/...`. Sirve para probar sin tocar tu configuración. En `claude-desktop` es la carpeta de los ZIP |
| `--enlazar` | En vez de copiar, enlaza cada skill al repo (junction en Windows, symlink en macOS y Linux): un `git pull` actualiza la instalación. Agentes y comandos se copian igual |
| `--forzar` | Reemplaza una skill con el mismo nombre que no instaló este instalador. Sin él, se detiene antes de escribir nada |
| `--desinstalar` | Borra solo lo que dice su manifiesto. A un enlace le quita el enlace, nunca entra al repo. Lo que comparte con otra instalación (codex y agents usan `~/.agents/skills`) se conserva |
| `--listar` | Qué hay en el repo y qué quedó instalado en cada plataforma |
| `--probar` | Instala en un HOME temporal para cada plataforma, verifica cada `SKILL.md`, el formato de los agentes y la estructura de los ZIP, corre el `--probar` de cada método **desde la copia instalada**, desinstala y comprueba que no quedó nada |

Nunca modifica `settings.json`, `config.yaml` ni `config.toml`. Deja un manifiesto en
`<carpeta de configuración>/.ingeniero-agentico/<plataforma>.json`.

**Qué se instala.** Cada `skills/<nombre>/` completa, con `pruebas/`, porque cada `SKILL.md` manda a
correr `--probar` y el auditor lo usa para confirmar que el método funciona donde quedó. Se excluye
lo generado: `__pycache__`, `*.pyc` y `salidas/`. Dos agregados que no están dentro de las skills:

- `perfiles/_plantilla.yaml` en `<carpeta de configuración>/perfiles/`: los scripts la buscan tres
  carpetas arriba de `scripts/`. Sin ella, `evaluacion-financiera` no corre ni su prueba (probado).
- `ARQUITECTURA.md` dentro de `orquestar/`: `orquestar`, `investigar` y `cartografiar` la citan como
  «raíz del repo», que en una copia no existe.

### Resultado de `--probar` (15-10-2026, Windows, Python 3.14)

```
Prueba del instalador (HOME temporal, nada toca la configuración real)
Scripts de cada método: se corren con --probar desde la copia instalada

  claude-code        .claude\skills                     OK
  claude-desktop     9 ZIP                              OK
  codex              .agents\skills                     OK
  cursor             .cursor\skills                     OK
  gemini             .gemini\skills                     OK
  hermes             AppData\Local\hermes\skills        OK
  agents             .agents\skills                     OK
  agents --enlazar   junction                           OK
  codex + agents     carpeta compartida                 OK
  aviso: evaluacion-economica: description de 1077 caracteres (...)
  aviso: evaluacion-financiera: description de 1091 caracteres (...)

OK
```

## Qué no funciona en cada plataforma

| Plataforma | No funciona o cambia |
|---|---|
| Claude Code (plugin) | La carpeta hermana de datos no sirve (usa `INGENIERO_DATOS`). Nombres con prefijo `ingeniero-agentico:` |
| claude.ai chat | Sin agentes (orquestación en secuencia). Sin `/nuevo-encargo`. Sin disco: perfil y caso se suben; salidas se descargan. Plantilla de perfil ausente en los ZIP de skill. Sin ejecución de código no hay números |
| Cowork | Carga agentes; la carpeta de datos depende de si la sesión corre en tu equipo |
| Codex | Sin `/nuevo-encargo` (usa `$orquestar`). Agentes convertidos sin herramientas ni modelo propios |
| Cursor | Sin `/nuevo-encargo`. Agentes sin herramientas ni modelo propios |
| Gemini CLI | Sin `/nuevo-encargo`. Agentes sin herramientas ni modelo propios. Pide permiso al activar cada skill |
| Hermes | Sin archivos de agentes (delega con `delegate_task`). Lee `AGENTS.md`, no `CLAUDE.md` |
| `agents` genérico | Solo skills: orquestación en secuencia |

En todas, `orquestar` en secuencia hace las seis etapas en la misma conversación, con el plan como
puerta (nada corre antes del «sí») y la auditoría declarada «en la misma conversación».

## Fuentes

- Claude Code: [Plugin manifest](https://code.claude.com/docs/en/plugins-reference) ·
  [Create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces) ·
  [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference) ·
  [Host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace) ·
  [Skills](https://code.claude.com/docs/en/skills) · [Subagents](https://code.claude.com/docs/en/sub-agents)
- Claude Desktop y claude.ai: [Create custom skills](https://claude.com/docs/skills/how-to) ·
  [Plugin structure and testing](https://claude.com/docs/plugins/build) ·
  [Plugin support by app](https://claude.com/docs/plugins/platform-support)
- Codex: [Skills](https://developers.openai.com/codex/skills) · [Subagents](https://developers.openai.com/codex/subagents) ·
  [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- Cursor: [Skills](https://cursor.com/docs/context/skills) · [Subagents](https://cursor.com/docs/context/subagents) ·
  [Rules](https://cursor.com/docs/context/rules)
- Gemini CLI: [Agent Skills](https://geminicli.com/docs/cli/skills/) · [Subagents](https://geminicli.com/docs/core/subagents/) ·
  [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/) · [Imports](https://geminicli.com/docs/reference/memport/)
- Hermes Agent: [Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) ·
  [Delegation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) ·
  [Context files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) ·
  código instalado v0.21.4 (`hermes_constants.py`, `agent/skill_utils.py`)
- Estándar: [Agent Skills specification](https://agentskills.io/specification)
