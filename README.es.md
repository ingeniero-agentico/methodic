# ingeniero-agentico

[Read in English → README.md](README.md)

Métodos de ingeniería industrial convertidos en **skills para agentes de IA**: cada método trae la
skill que ejecuta el agente, la guía para una persona (`GUIA.md` en español, `GUIDE.md` en inglés),
plantillas, el cálculo en un script y una prueba que tiene que cuadrar.

Sirve para cualquier empresa. Los datos de cada empresa viven **fuera de este repo**, en un perfil
propio (ver «Datos privados»).

## Métodos

| Método | Qué resuelve | Estado |
|---|---|---|
| [procurement](skills/procurement/) | A quién comprar qué, cuando cada proveedor cubre solo una parte | v1 |
| [cost-and-pricing](skills/cost-and-pricing/) | Cuánto cuesta de verdad un trabajo y a cuánto venderlo (recargo sobre el costo) | v1 |
| [economic-evaluation](skills/economic-evaluation/) | Si un proyecto o inversión conviene: flujo de caja, VAN, TIR, sensibilidad | v1 |
| [financial-evaluation](skills/financial-evaluation/) | Cómo financiarlo: crédito, leasing, arriendo o compra al contado | v1 |

Los nombres de las skills quedaron en inglés desde la versión 1.1 (antes: `adquisiciones`,
`costo-y-precio`, `evaluacion-economica`, `evaluacion-financiera`).

Cada método se prueba con `python skills/<metodo>/scripts/<script>.py --test`: corre un caso
ficticio cuyo resultado se calculó por un segundo camino, y termina en `OK` o falla.

## Cómo se trabaja un encargo

```
/new-task ¿me conviene comprar otra camioneta para arrendarla?
```

La skill `orchestrate` lo lleva por seis etapas (detalle en [ARCHITECTURE.md](ARCHITECTURE.md)):

1. **Cartografiar** (`map-context`): un agente barato hace el mapa de las carpetas que toca el encargo.
2. **Investigar** (`research`): solo si faltan datos; cada dato con fuente, fecha y fiabilidad (A a D).
3. **Planificar y pedir:** te muestra qué agentes lanzará, con qué skill y modelo. Espera tu sí.
4. **Ejecutar:** un agente por método, en paralelo cuando no dependen entre sí.
5. **Auditar** (`audit`): un agente independiente vuelve a correr cada cálculo y compara.
6. **Consolidar:** una respuesta con la decisión, los supuestos que la deciden y qué falta.

**Dos modos.** La *primera vez* (`first-run`) sobre un tema se investiga y se mapea completo. Las
siguientes son *relectura* (`reread`): se lee el mapa en vez de las carpetas, con modelos
económicos. El modo lo decide la comparación de huellas de los archivos, no el modelo.

## Cómo está ordenado

```
ingeniero-agentico/
├── skills/        los métodos + orchestrate · map-context · research · audit
├── agents/        trabajadores de una etapa: cartographer · researcher · executor · auditor
├── commands/      /new-task
├── mcp/           servidor MCP: los métodos como herramientas para cualquier cliente MCP
├── install/       instalador para Codex, Cursor, Gemini CLI, Hermes y otros
├── graph/         notas enlazadas método ↔ ramo ↔ patrón, para Obsidian y graphify
└── profiles/      la plantilla del perfil de empresa (vacía)
```

## Instalar

| Dónde | Cómo | Detalle |
|---|---|---|
| Claude Code | `/plugin marketplace add ingeniero-agentico/ingeniero-agentico` y `/plugin install ingeniero-agentico@ingeniero-agentico` | Trae skills, agentes, `/new-task` y el servidor MCP |
| Claude Code sin plugin | `python install/install.py --platform claude-code` | Skills, agentes y comandos en `~/.claude/` |
| Claude Desktop / claude.ai | `python install/install.py --platform claude-desktop` y subir los ZIP en Customize | Sin agentes en el chat: `orchestrate` corre las etapas en secuencia |
| Codex | `python install/install.py --platform codex` | Skills en `~/.agents/skills/`, agentes en TOML; lee `AGENTS.md` |
| Cursor | `python install/install.py --platform cursor` | Skills y subagentes en `~/.cursor/`; lee `AGENTS.md` |
| Gemini CLI | `python install/install.py --platform gemini` | Skills y subagentes en `~/.gemini/`; lee `GEMINI.md` → `AGENTS.md` |
| Hermes Agent | `python install/install.py --platform hermes` | Skills en `HERMES_HOME/skills/`; delega con `delegate_task` |
| Otros agentes con Agent Skills | `python install/install.py --platform agents` | Skills en `~/.agents/skills/`, en secuencia |
| Cualquier cliente MCP | `python mcp/server.py` en su configuración | Los métodos como herramientas |

Paso a paso por plataforma en [docs/INSTALL.md](docs/INSTALL.md) (en inglés); el servidor MCP en
[docs/MCP.md](docs/MCP.md). `python install/install.py --test` instala en un HOME temporal para cada
plataforma y lo verifica sin tocar tu configuración. Las opciones en español de la versión 1.0
(`--plataforma`, `--probar` y las demás) siguen funcionando.

## Datos privados

Cada skill busca el perfil de la empresa en este orden:

1. La ruta que se pasa con `--profile`.
2. La ruta en la variable de entorno `INGENIERO_DATOS`.
3. La carpeta hermana `../ingeniero-agentico-datos/`.
4. Si no encuentra ninguna, trabaja con `profiles/_template.yaml` y te pide los datos que falten
   (todo lo que completa sale marcado `SUPUESTO`).

Esa carpeta lleva `profiles/<empresa>.yaml` y `cases/<caso>/` (las carpetas antiguas `perfiles/` y
`casos/` siguen sirviendo). **Nunca se sube a este repo.**

El campo `language: es | en` del perfil fija el idioma de las salidas (rótulos del Excel, la marca
`SUPUESTO` o `ASSUMPTION`, el texto de la consola). Por defecto es `es`, así que los casos armados
con la versión 1.0 producen los mismos archivos. Las claves en español del perfil y de las
entradas se siguen aceptando.

## Próxima versión

La versión 1.1 (esta rama) pasa el repo a inglés con el español al lado, y cierra los tres
primeros puntos de la auditoría sobre casos reales (15-10-2026): `procurement` y `cost-and-pricing`
reciben y devuelven supuestos, como los métodos de evaluación; un mismo formato de
`research-data.json` entre `research`, `executor` y `auditor`; y el núcleo del mapa excluye un
archivo que otro declara reemplazado («Reemplaza a»). Lo que queda:

1. **Skills autosuficientes.** La plantilla de perfil dentro de cada skill, para que los scripts
   funcionen en claude.ai sin `--profile` y sin copiar nada fuera de la skill.
2. **Probar dentro de Codex, Cursor y Gemini reales.** Hoy se verificó solo el formato instalado.
3. **Regla de versiones al publicar.** Cada entrega sube `version` en `.claude-plugin/plugin.json`:
   quien instaló el plugin no recibe cambios mientras la versión sea la misma.

## De dónde sale

Cada método nace de ramos de Ingeniería Civil Industrial y de su uso en empresas reales. El
`SOURCES.md` de cada método cita la bibliografía; el material de los cursos no se reproduce.

## Licencia

Código y scripts: MIT. Guías y notas: CC BY-SA 4.0. Ver `LICENSE`.
