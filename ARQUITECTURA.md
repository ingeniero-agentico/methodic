# Arquitectura · cómo se orquesta un encargo

Versión 2 (15-10-2026). Reemplaza al agente `orquestador` de la v1.

## La restricción que manda

En Claude Code **un agente no puede lanzar otros agentes**. Por eso:

- El **orquestador es una skill** (`skills/orquestar/`) que corre en la conversación principal, la
  única que puede lanzar agentes.
- Los **agentes son trabajadores** (`agents/`): cada uno hace una etapa, con sus skills y su modelo.

## Las seis etapas

| # | Etapa | Quién | Modelo | Lee | Deja |
|---|---|---|---|---|---|
| 0 | Cartografiar | agente `cartografo` + skill `cartografiar` | económico | las carpetas del encargo | `contexto/MAPA.md` + `contexto/grafo.json` + `contexto/huellas.json` |
| 1 | Investigar | agente `investigador` + skill `investigar` | fuerte | el mapa y los huecos | `contexto/INVESTIGACION.md` (cada dato con fuente, fecha y fiabilidad) |
| 2 | Planificar y pedir | skill `orquestar` | el de la sesión | mapa + investigación | `contexto/PLAN.md`; **se le muestra a la persona y espera su sí** |
| 3 | Ejecutar | agente `ejecutor` (uno por método, en paralelo si no dependen) | según el plan | el plan y su entrada | la salida del método en `casos/` |
| 4 | Auditar | agente `auditor` (solo lectura) | fuerte | entradas, scripts y salidas | `contexto/AUDITORIA.md` (vuelve a correr cada script y compara) |
| 5 | Consolidar | skill `orquestar` | el de la sesión | todo lo anterior | la respuesta: decisión, supuestos que deciden, dónde quedó, qué falta |

## Dos modos, según lo que ya se sabe

El modo lo decide `cartografiar` comparando `huellas.json` (tamaño y fecha de cada archivo) con
el disco. No lo elige el modelo «a ojo».

| | Primera vez | Relectura |
|---|---|---|
| Cuándo | No hay `contexto/MAPA.md`, o el ámbito es nuevo | Hay mapa y las huellas casi no cambiaron |
| Etapa 0 | Mapa completo | Solo los archivos que cambiaron |
| Etapa 1 | Investigación completa de los huecos | Se salta, salvo que el plan declare un hueco nuevo |
| Lectura | Los archivos fuente | **Solo `MAPA.md`** (≤ 3.000 palabras) y los archivos que cambiaron |
| Modelos | Fuerte en investigar y auditar | Económico en todo menos auditar |
| Para quién | Quien llega a un tema y lo investiga por primera vez | Quien vuelve al mismo tema con presupuesto acotado |

**El ahorro de la relectura es leer el mapa en vez de las carpetas.** Por eso el mapa tiene que
bastar: qué hay, dónde, de cuándo, qué dice cada archivo en una línea y qué enlaza con qué.

## La petición (etapa 2)

Ningún agente se lanza sin que la persona apruebe el plan. El plan es una tabla:

| Etapa | Agente | Skill | Modelo | Entrada | Salida | Depende de |
|---|---|---|---|---|---|---|

más el modo, el número de agentes y una estimación gruesa de costo (agentes × modelo). La
persona responde «sí», cambia una fila o pide otro modo. Si el entorno de la persona no permite
agentes, `orquestar` corre las etapas en secuencia en la misma conversación.

## Dónde vive `contexto/`

Junto a los datos del encargo, nunca en el repo público:
`<datos>/casos/<caso>/contexto/`, o `<carpeta del encargo>/contexto/` si no hay carpeta de datos.

## Fiabilidad de una fuente (la usan `investigar` y `auditor`)

| Nivel | Qué es |
|---|---|
| A | Norma, ley, organismo oficial, documento del propio cliente |
| B | Libro o artículo académico, manual técnico del fabricante |
| C | Sitio de proveedor, cotización, prensa especializada |
| D | Blog, foro, IA sin fuente: solo orienta, nunca entra a un cálculo sin marcarse `SUPUESTO` |
