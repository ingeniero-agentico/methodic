# Entrevista · guía paso a paso

El mismo método de `SKILL.md`, para una persona. Se recorre con el caso ficticio de `tests/`:
**Ferretería Andes**, una ferretería de unas quince personas, va a empezar a trabajar con methodic.
Nadie ha escrito cómo funciona el negocio. La entrevista lo averigua preguntando, en tandas cortas, y
deja un registro fechado que después cita el manual.

**Qué hace la entrevista y qué no.** Pregunta y anota las respuestas. No escribe las páginas del
manual (eso lo hace la skill `manual`) y no abre ni cambia ningún archivo del computador (eso lo hace
la skill `intervene`, más adelante y dentro de los límites que se acuerdan en la ronda 3).

## 0 · El perfil y la carpeta de datos

El registro vive fuera del repo, en la carpeta de datos del operador:

```
C:/Users/usuario/methodic-data/
├── profiles/ferreteria-andes.yaml      ← empresa = el nombre del archivo sin .yaml
└── manual/ferreteria-andes/entrevista/ ← lo crea el primer registro
```

Copia `profiles/_template.yaml` a `profiles/ferreteria-andes.yaml` y llena al menos `language`
(`es` o `en`) y `company.name`. El script busca la carpeta de datos en este orden: `--data`,
`METHODIC_DATA`, `INGENIERO_DATOS`, `../methodic-data/`, `../ingeniero-agentico-datos/`.

## 1 · Pedir la primera tanda

```bash
python scripts/interview.py next
```

```
Ferretería Andes · Tanda 1 · El negocio
[neg-01] ¿Qué vende principalmente la empresa? (varias)
   1) Productos que compra y revende · 2) Productos que fabrica o arma · 3) Servicios u obras · 4) No sé · u otra respuesta
[neg-02] ¿En qué tipo de negocio está?
   ...
```

Cuatro preguntas, cada una con opciones y siempre con «No sé». El agente las hace tal como vienen (con
la herramienta AskUserQuestion donde existe, o con esta misma lista en texto). No las redacta de
nuevo: el registro tiene que calzar con el banco.

## 2 · Registrar las respuestas

Responde la dueña. El agente anota las respuestas por código de pregunta y las registra de inmediato:

```json
{"round": 1, "who": "dueña", "answers": [
  {"id": "neg-01", "answer": ["Productos que compra y revende"]},
  {"id": "neg-02", "answer": "Comercio (tienda o distribuidora)"},
  {"id": "neg-03", "answer": ["Personas (público general)", "Empresas"]},
  {"id": "neg-04", "answer": ["Al contado al entregar", "Con factura a 30 o 60 días"]}]}
```

```bash
python scripts/interview.py record --answers tanda-1.json
```

`who` es un rol (`dueña`, `vendedor`, `bodega`), nunca el nombre de una persona dentro del repo.

## 3 · «No sé» es una respuesta

La segunda tanda la responde el vendedor. No sabe cómo se fijan los precios:

```bash
python scripts/interview.py record --answers tanda-2.json --who vendedor
```

El archivo del día, `entrevista/2026-10-16.md`, queda con dos bloques (la fecha es la del día en que
se registró):

```markdown
## Tanda 2 · El negocio · 16-10-2026 15:20
Respondió: vendedor

1. [neg-05] ¿Cómo se fija el precio de lo que vende? → No sé · HUECO
2. [neg-06] ¿Cuántas personas trabajan en la empresa contando al dueño? → 6 a 20
3. [neg-07] ¿Quién decide lo importante (precios, compras grandes, contrataciones)? → El dueño o la dueña
4. [neg-08] ¿Qué procesos le quitan más tiempo o le dan más problemas hoy? (si son otros, escríbalos separados por coma) → Compras, Cobranza
```

El hueco no es una falla: dice qué falta y desde cuándo. Cuando la dueña esté disponible,
`next --gaps` lo vuelve a preguntar y la respuesta nueva lo cierra. Al archivo solo se le agrega: un
bloque anterior nunca se edita.

## 4 · Dónde vamos

```bash
python scripts/interview.py status
```

```
Ferretería Andes · entrevista · 2 tanda(s) · última 16-10-2026 15:20
Ronda 1 · El negocio: 8/10 (1 no aplica)
Ronda 2 · El proceso:
   COMPRAS (Compras) · duele: 0/12
   COBRANZA (Cobranza) · duele: 0/12
Ronda 3 · Los límites: 0/8
Huecos abiertos (1):
   - neg-05 · ¿Cómo se fija el precio de lo que vende? · declarado el 16-10-2026
Siguiente: Ronda 1 · neg-10, neg-11
```

«1 no aplica» es `neg-09` (hasta qué monto decide un jefe): aquí decide todo la dueña, así que no se
pregunta. La respuesta «Compras, Cobranza» nombró dos procesos que duelen, y cada uno recibe su código.

## 5 · Ronda 2, una vez por proceso

Cuando se cierra la ronda 1, `next` pasa a `COMPRAS`: qué lo hace partir, cada cuánto ocurre, los
pasos en orden, quién hace cada uno, con qué herramienta, dónde quedan sus archivos, dónde alguien
decide y quién aprueba, qué entrega y a quién, qué suele fallar y quién responde por el proceso.
Después, lo mismo para `COBRANZA`. Cada bloque lleva el código: `## Tanda 4 · El proceso · COMPRAS · …`.

Para saltar: `next --round 2 --process COBRANZA`.

## 6 · Ronda 3, los límites

La última ronda fija qué puede hacer methodic en el computador: qué carpetas puede leer (con la ruta
escrita, por ejemplo `C:/Users/usuario/Documents/FerreteriaAndes`), dónde puede cambiar un archivo
(siempre con respaldo y con un OK cada vez), qué no se toca nunca (sueldos, bancos), qué datos son
sensibles, quién da el OK, si hay respaldo y quién envía o paga lo que se prepare (methodic prepara;
envía una persona).

La dueña prefiere llenar esta ronda sola y de una vez:

```bash
python scripts/interview.py form --round 3 > limites.md
# marca con [x] y escribe las rutas en «Otra respuesta»; después:
python scripts/interview.py record --form limites.md
```

Las mismas preguntas, los mismos códigos, un solo bloque en el registro.

## 7 · Entregar al manual

Cuando `status` dice que no queda nada por preguntar, la skill `manual` lee `status --json` y
escribe `NEGOCIO.md`, una página por proceso y `alcance.yaml`. Cada paso cita su respuesta
(`entrevista · dueña · 16-10-2026`), cada hueco va a `Huecos` con su fecha y lo que nadie respondió
queda marcado `SUPUESTO`.

## Errores que el método ataja

| Error | Dónde se ataja |
|---|---|
| El agente completa con «lo que suele hacer una ferretería» | solo cuentan las respuestas registradas; el resto va como `SUPUESTO` en el manual |
| Se pierde una pregunta que nadie supo responder | queda como hueco fechado en `status` y en el índice |
| Veinte preguntas en un mensaje | tandas de 4 como máximo; `record` rechaza más |
| Una pregunta redactada de nuevo pierde sus respuestas anteriores | cada línea del registro lleva el código de la pregunta |
| Una respuesta anterior pisada sin aviso | el archivo solo crece; una respuesta nueva es un bloque nuevo |
| Un paso del proceso sin fuente | cada respuesta lleva quién la dio y cuándo |
