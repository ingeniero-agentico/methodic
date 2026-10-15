# ingeniero-agentico · instrucciones para cualquier agente

Este archivo lo leen Codex, Cursor, Hermes Agent y Gemini CLI (vía `GEMINI.md`) al abrir el repo.
Claude Code lee `CLAUDE.md`, que tiene las reglas de quien **modifica** el repo; las de quien lo
**usa** están acá. Cómo instalarlo en cada plataforma: `docs/INSTALAR.md`.

## Qué es

Métodos de ingeniería industrial convertidos en skills (formato [Agent Skills](https://agentskills.io/specification)).
Cada método trae un `SKILL.md` (lo que decide el agente), un script en Python (lo que calcula), plantillas
de entrada y una prueba que cuadra. **Ningún número se calcula de cabeza: sale del script.**

| Skill | Para qué |
|---|---|
| `orquestar` | Recibe un encargo, elige el método y lleva las seis etapas. Empieza por acá si no es obvio qué método aplica |
| `cartografiar` | Etapa 0: mapa de las carpetas del encargo y modo (primera vez o relectura) |
| `investigar` | Etapa 1: un dato con fuente, fecha y fiabilidad por cada hueco que el cálculo necesita |
| `adquisiciones` | A quién comprar qué, cuando cada proveedor cubre solo una parte |
| `costo-y-precio` | Costo real de un trabajo y precio de venta por recargo |
| `evaluacion-economica` | Si un proyecto o inversión conviene: flujo de caja, VAN, TIR, sensibilidad |
| `evaluacion-financiera` | Cómo financiarlo: contado, crédito, leasing o arriendo |
| `auditar` | Etapa 4: vuelve a correr cada script con la misma entrada y compara |

Cada skill vive en `skills/<nombre>/SKILL.md`. En `agents/` están los trabajadores de cada etapa
(`cartografo`, `investigador`, `ejecutor`, `auditor`) en formato de Claude Code; `instalar/instalar.py`
los convierte al formato de Codex, Cursor y Gemini.

## Cómo correr un método

1. Lee **solo** el `SKILL.md` del método que corresponde (no los cuatro).
2. Arma la entrada desde `skills/<metodo>/plantillas/` con los datos de la persona.
3. Corre el script que indica el `SKILL.md`, desde la carpeta de la skill:
   `python scripts/<script>.py <entrada> --perfil <empresa|ruta.yaml> ...`
4. Antes de confiar en una instalación nueva: `python scripts/<script>.py --probar` tiene que terminar en `OK`.

Requisitos: Python 3.11 o superior, biblioteca estándar y `openpyxl` (para los Excel).

## Datos privados (regla dura)

Los datos de una empresa **nunca** entran a este repo ni a la carpeta donde quedaron instaladas las
skills. Viven en una carpeta aparte, `ingeniero-agentico-datos/`, con `perfiles/<empresa>.yaml` y
`casos/<caso>/` (ahí va también `contexto/`, el mapa y el plan de cada encargo).

Cada script busca el perfil en este orden:

1. `--perfil <nombre o ruta>`.
2. La variable de entorno `INGENIERO_DATOS`.
3. La carpeta hermana `../ingeniero-agentico-datos/` (hermana del repo; en una instalación por copia,
   hermana de la carpeta de configuración, p. ej. `~/ingeniero-agentico-datos/`).
4. `perfiles/_plantilla.yaml`: todo lo que sale de ahí queda marcado `SUPUESTO`.

Si hay más de un perfil y el encargo no dice cuál, **pregunta**. Si la plataforma corre en un entorno
aislado (claude.ai, un contenedor), pide a la persona que suba su perfil y pásalo con `--perfil`.

## Orquestar un encargo

Usa la skill `orquestar`. Las seis etapas son siempre las mismas; cambia solo quién las hace.

| # | Etapa | Lee primero |
|---|---|---|
| 0 | Cartografiar | `skills/cartografiar/SKILL.md` y `agents/cartografo.md` |
| 1 | Investigar (solo si hay huecos) | `skills/investigar/SKILL.md` y `agents/investigador.md` |
| 2 | Planificar y **pedir aprobación** | `skills/orquestar/SKILL.md` |
| 3 | Ejecutar (un método por fila del plan) | el `SKILL.md` del método y `agents/ejecutor.md` |
| 4 | Auditar | `skills/auditar/SKILL.md` y `agents/auditor.md` |
| 5 | Consolidar | `skills/orquestar/SKILL.md` |

### Sin subagentes (modo «sin agentes»)

Si tu plataforma no lanza subagentes, o la persona dice «sin agentes», haz las seis etapas **tú, en
secuencia, en esta conversación**:

1. Haz cada etapa leyendo el archivo del agente como si fueran tus instrucciones para esa etapa. Al
   terminarla, deja su salida en `contexto/` antes de pasar a la siguiente.
2. **La etapa 2 es una puerta.** Escribe `contexto/PLAN.md` con la tabla de etapas, muéstrasela a la
   persona y **detente hasta que diga «sí»** (o cambie una fila). No corras ningún método antes.
3. En la etapa 4 vuelve a correr cada script con `skills/auditar/scripts/recorrer.py`; no revises tu
   propio cálculo «de memoria». Como la auditoría no la hizo otro agente, dilo en la respuesta:
   «auditoría en la misma conversación».
4. Si una etapa falla, informa y propone el arreglo; no la reemplaces con un cálculo tuyo.

### Con subagentes

Codex, Cursor y Gemini CLI tienen subagentes, y Hermes delega con `delegate_task`. Lánzalos solo
después del «sí» de la etapa 2, uno por fila del plan, en paralelo lo que no depende entre sí. A cada
uno pásale su fila del plan, la ruta de `contexto/`, el perfil, la carpeta del caso y el archivo de
`agents/` que le toca. Un subagente no lanza a otro: la orquestación queda en la conversación principal.

## Si vas a modificar el repo

Lee `CLAUDE.md` antes. Lo mínimo: cero datos reales (ni RUT, ni empresas, ni personas, ni rutas
locales; los ejemplos son ficticios), todo número sale de un script con prueba que cuadra, los `.md`
con frontmatter van en UTF-8 **sin BOM**, y en la redacción el inciso va entre paréntesis.
