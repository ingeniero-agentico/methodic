# methodic

[Read in English → README.md](README.md)

**Un documentador metódico para agentes de IA.** methodic entiende cualquier negocio haciendo las
preguntas pertinentes, deja lo aprendido en un **manual trazable** de sus procesos y recién
entonces interviene en el computador del operador: con un plan, el OK del operador para cada
acción, un respaldo y una línea en la bitácora. Los métodos de ingeniería industrial (compras,
costos, evaluación de proyectos, financiamiento) son sus herramientas; cada número sale de un
script con su prueba.

Sirve para cualquier empresa. Los datos y el manual de cada empresa viven **fuera de este repo**,
en el computador del operador (ver «Datos privados»).

## Cómo funciona

```
/new-task perdemos un día a la semana comparando cotizaciones de proveedores
```

1. **Entrevista.** Tandas de 3 a 4 preguntas con opciones, una tanda a la vez. «No sé» es una
   respuesta válida: queda como hueco declarado con su fecha. Tres rondas: el negocio, el proceso
   que duele y los límites (qué carpetas puede leer, qué no se toca nunca).
2. **Documentación.** Cada proceso queda en una página: SIPOC arriba y pasos numerados abajo. Cada
   paso tiene un código (`COMPRAS-03`), un responsable, una herramienta y **de dónde salió**
   (entrevista, documento, observación o `SUPUESTO`). Estado, revisión e historial como cualquier
   documento controlado. Un script lo verifica todo.
3. **Intervención.** Plan → **tu OK para esa acción** → respaldo → ejecución → verificación con un
   hecho → línea en la bitácora. Nunca borra, instala, sale a la red, envía ni paga: prepara, y la
   persona envía. Un archivo de permisos generado desde tu alcance hace que Claude Code bloquee los
   comandos habituales para eso, porque el texto de una skill por sí solo no obliga. Es una
   barrera, no una jaula: tu revisión de cada plan sigue siendo el control principal.
4. **Cálculo**, cuando un paso necesita números: el script del método calcula, un agente
   independiente lo vuelve a correr y el resultado queda amarrado al paso del manual que lo pidió.

**Es barato de usar, con cualquier plan.** Una sesión carga el índice del manual (≤ 400 palabras)
y el proceso que toca (≤ 800 palabras), no el manual completo ni una entrevista nueva. Lo que una
sesión aprende se escribe antes de cerrar, así que la siguiente parte leyendo una página. Los
tokens los paga la cuenta del agente del operador.

## Skills

| Skill | Qué hace |
|---|---|
| [orchestrate](skills/orchestrate/) | Lleva una tarea por las etapas; se parte aquí cuando no está claro por dónde |
| [interview](skills/interview/) | Pregunta en tandas con opciones y registra respuestas y huecos |
| [manual](skills/manual/) | Escribe el índice y las páginas de proceso y verifica topes y trazabilidad |
| [intervene](skills/intervene/) | Cambia un archivo del operador solo mediante el ciclo seguro |
| [map-context](skills/map-context/) | Mapea las carpetas de una tarea antes de leerlas |
| [research](skills/research/) | Un dato externo por hueco, con fuente, fecha y confiabilidad |
| [audit](skills/audit/) | Vuelve a correr cada cálculo y compara |
| [procurement](skills/procurement/) | A quién comprarle qué, cuando cada proveedor cubre solo una parte |
| [cost-and-pricing](skills/cost-and-pricing/) | Cuánto cuesta de verdad un trabajo y a cuánto venderlo (recargo sobre el costo) |
| [economic-evaluation](skills/economic-evaluation/) | Si un proyecto conviene: flujo de caja, VAN, TIR, sensibilidad |
| [financial-evaluation](skills/financial-evaluation/) | Cómo financiarlo: crédito, leasing, arriendo o contado |

Cada skill con script se prueba con `python skills/<skill>/scripts/<script>.py --test`, que
termina en `OK` o falla. `python security/run_tests.py` las corre todas.

Las etapas, los modos y la carpeta `context/` están en [ARCHITECTURE.md](ARCHITECTURE.md); el
formato del manual, en [docs/MANUAL-FORMAT.md](docs/MANUAL-FORMAT.md).

## Cómo está organizado

```
methodic/
├── skills/        documentador (interview · manual · intervene), orquestación y métodos
├── agents/        trabajadores de una etapa: cartographer · researcher · executor · auditor
├── commands/      /new-task
├── docs/          formato del manual, instalación, servidor MCP
├── mcp/           servidor MCP: los métodos como herramientas para cualquier cliente MCP
├── install/       instalador para Codex, Cursor, Gemini CLI, Hermes y otros
├── security/      escáner, manifiesto y pruebas que vigilan cada cambio
├── graph/         notas enlazadas método ↔ ramo ↔ patrón, para Obsidian y graphify
└── profiles/      la plantilla del perfil de empresa (vacía)
```

## Instalación

| Dónde | Cómo | Notas |
|---|---|---|
| Claude Code | `/plugin marketplace add ingeniero-agentico/methodic` y `/plugin install methodic@methodic` | Trae skills, agentes, `/new-task` y el servidor MCP |
| Claude Code sin el plugin | `python install/install.py --platform claude-code` | Skills, agentes y comandos en `~/.claude/` |
| Claude Desktop / claude.ai | `python install/install.py --platform claude-desktop` y subir los ZIP en Personalizar | Sin agentes en el chat: las etapas corren en secuencia |
| Codex | `python install/install.py --platform codex` | Lee `AGENTS.md` |
| Cursor | `python install/install.py --platform cursor` | Lee `AGENTS.md` |
| Gemini CLI | `python install/install.py --platform gemini` | Lee `GEMINI.md` → `AGENTS.md` |
| Hermes Agent | `python install/install.py --platform hermes` | Delega con `delegate_task` |
| Otros agentes Agent Skills | `python install/install.py --platform agents` | Skills en `~/.agents/skills/` |
| Cualquier cliente MCP | `python mcp/server.py` en su configuración | Los métodos como herramientas |

Paso a paso en [docs/INSTALL.md](docs/INSTALL.md); el servidor MCP en [docs/MCP.md](docs/MCP.md).
Antes de dejar que methodic toque archivos, instala el archivo de permisos que `intervene` genera
a partir de tu alcance (ver [skills/intervene/GUIA.md](skills/intervene/GUIA.md)).

## Datos privados

Todo lo de una empresa vive en una carpeta de datos fuera del repo, que se busca en este orden:
`--data` / `--profile` · `METHODIC_DATA` · la carpeta hermana `../methodic-data/` (siguen
funcionando las antiguas `INGENIERO_DATOS` y `../ingeniero-agentico-datos/`). Contiene:

```
methodic-data/
├── profiles/<empresa>.yaml     moneda, impuestos, tasas, idioma
├── manual/<empresa>/           el manual, el registro de la entrevista, el alcance, la bitácora y los respaldos
└── cases/<caso>/               entradas, salidas y context/ de cada cálculo
```

**Nunca se sube a este repo.** El campo `language: es | en` del perfil fija el idioma de todo lo
que lee una persona, `es` por defecto.

## Lo que sigue

1. **Skills autónomas.** La plantilla del perfil dentro de cada skill, para que los scripts
   funcionen en claude.ai sin `--profile` y sin copiar nada fuera de la skill.
2. **Probado dentro de Codex, Cursor y Gemini reales.** Hoy solo se verificó el formato instalado.
3. **El documentador en un negocio real**, de punta a punta: entrevista, manual aprobado por el
   operador y una intervención con su línea en la bitácora.

## De dónde viene

Los métodos vienen de ramos de Ingeniería Civil Industrial y de su uso en empresas reales; el
documentador, de documentar procesos reales de pymes. El `SOURCES.md` de cada skill cita la
bibliografía; el material de los ramos no se reproduce.

## Licencia

Código y scripts: MIT. Guías y notas: CC BY-SA 4.0. Ver `LICENSE`.
