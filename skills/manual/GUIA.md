# Manual · guía paso a paso

El mismo método de `SKILL.md`, para una persona. Se recorre con la ficticia **Ferretería Andes**
(vende en mesón y a contratistas), cuyo proceso de compras se escribe desde la primera entrevista.
El manual terminado está en `tests/sample/`.

**Qué hace el script y qué no.** Crea las carpetas y archivos, registra las revisiones y verifica
cada regla de `docs/MANUAL-FORMAT.md`. No escribe los pasos: los escribe una persona (o el agente)
desde el registro de la entrevista, y la verificación dice si se sostienen.

## 0 · El perfil y la carpeta de datos

El manual vive fuera del repo, en la carpeta de datos del operador:

```
<datos>/manual/<empresa>/
```

`<datos>` es `--data`; si no, `$METHODIC_DATA`; si no, `$INGENIERO_DATOS`; si no, la carpeta
`methodic-data` junto al repo; si no, `ingeniero-agentico-datos` junto al repo. `<empresa>` es el
nombre del archivo del perfil: `profiles/ferreteria-andes.yaml` da `ferreteria-andes`. Su
`language` (`es` por defecto) elige los nombres: `NEGOCIO.md`, `procesos/`, `entrevista/`… con
`es`; `BUSINESS.md`, `processes/`, `interview/`… con `en`.

## 1 · Crear el manual

```bash
python scripts/manual.py init --company ferreteria-andes
```

Crea el índice, las carpetas de procesos y de entrevista, el alcance, una bitácora vacía y las
carpetas de respaldos y de trabajo. Lo que ya existe se queda, nunca se pisa: correrlo dos veces no
hace daño.

## 2 · Leer el registro de la entrevista

La entrevista escribe `entrevista/2026-10-16.md` (nunca a mano). En Ferretería Andes, la tanda 2:

```markdown
## Tanda 2 · El proceso · COMPRAS · 16-10-2026 15:40
Respondió: dueña

1. [pro-01] ¿Qué hace partir este proceso y quién lo pide? → Bodega pide el material por WhatsApp
2. [pro-02] ¿Cada cuánto ocurre? → Dos o tres veces por semana
3. [pro-03] ¿Cuáles son los pasos en orden de principio a fin? → Pedir tres cotizaciones por correo; compararlas en una planilla; emitir la orden
4. [pro-06] ¿Dónde quedan los archivos de este proceso? → Carpeta Compras, una planilla por mes
```

El código entre corchetes amarra cada respuesta a su pregunta. `interview.py status --json` entrega
las mismas respuestas como lista (`id`, `process`, `maps_to`, `answer`, `gap`, `who`, `date`…), y
`maps_to` dice a dónde va cada una: `process:steps` a los pasos, `process:operation.frequency` a la
sección Operación, `scope:read` al alcance, etc. (tabla en `SKILL.md`). Cada respuesta que describe
una acción se vuelve un paso. Cada «No sé» se vuelve un hueco.

## 3 · Crear la página del proceso

```bash
python scripts/manual.py new-process COMPRAS "Comprar material" --owner dueña
```

La página parte en Borrador, revisión A, con una fila de historial, y su fila se agrega a la tabla
del índice. El código va en mayúsculas; los pasos serán `COMPRAS-01`, `COMPRAS-02`…

## 4 · Escribir la página

**SIPOC arriba**, desde lo que se dijo: quién provee (bodega, tres distribuidores), qué entra
(solicitud, cotizaciones), el proceso, qué sale (orden de compra) y quién lo recibe (bodega,
contabilidad).

**Operación** (opcional, justo después del SIPOC): lo que describe el proceso completo, cada línea
con su propio origen.

```markdown
## Operación
- Frecuencia: dos o tres veces por semana · Origen: entrevista · dueña · 16-10-2026
- Fallas habituales: un proveedor no responde y se compra al de siempre · Origen: entrevista · dueña · 16-10-2026
- Archivos: carpeta Compras, una planilla por mes · Origen: entrevista · dueña · 16-10-2026
```

Solo esas tres etiquetas (`Frequency`, `Usual failures`, `Files` en inglés); las líneas cuentan para
las 800 palabras.

**Pasos abajo**, uno por acción, cada uno con exactamente una línea de origen:

```markdown
1. **COMPRAS-01** Bodega pide el material por WhatsApp.
   - Responsable: bodega · Herramienta: WhatsApp
   - Origen: entrevista · dueña · 16-10-2026
3. **COMPRAS-03** ◆ Se comparan las cotizaciones y se elige proveedor → `procurement`.
   - Responsable: compras · Herramienta: planilla
   - Origen: documento · comparativo-agosto.xlsx, hoja 1
4. **COMPRAS-04** ◆ Sobre $500.000 aprueba la dueña.
   - Responsable: dueña
   - Origen: SUPUESTO · monto no confirmado
5. **COMPRAS-05** Se emite la orden de compra desde la plantilla.
   - Responsable: compras · Herramienta: plantilla-oc.xlsx
   - Origen: observado · bitácora, línea 1
```

| Origen | Cuándo | Qué verifica el script |
|---|---|---|
| `entrevista · <rol> · <fecha>` | lo dijo el operador | existe `entrevista/<fecha>.md` (y el rol aparece en él) |
| `documento · <archivo>[, <lugar>]` | lo muestra un archivo | el archivo está bajo una carpeta `read` del alcance |
| `observado · bitácora, línea N` | se hizo y quedó en la bitácora | existe la línea N de la bitácora |
| `SUPUESTO · <por qué>` | no se puede omitir y nadie lo confirmó | nada; se cuenta y se lista |

- `◆` marca una decisión, justo después del código.
- `` → `procurement` `` dice que el paso se hace con ese método; la skill debe existir.
- La fecha de la entrevista es la de la tanda, no la del día en que se escribe la página.

**Huecos**: lo que no se sabe, con su fecha, escrito como el **dato que falta**, no como la
pregunta. La dueña respondió «No sé» a «¿Quién aprueba en ese momento y con qué criterio?», así que
el hueco dice `- Monto de aprobación de COMPRAS-04 · declarado el 16-10-2026`. El paso COMPRAS-04
conserva el supuesto hasta que la dueña dé el monto.

## 5 · El alcance

`alcance.yaml` guarda los únicos límites que leen los scripts, escritos con el operador:

```yaml
read:
  - C:/Users/usuario/Documents/FerreteriaAndes
write_with_ok:
  - C:/Users/usuario/Documents/FerreteriaAndes/Planillas
never:
  - C:/Users/usuario/Documents/FerreteriaAndes/Sueldos
sensitive:
  - RUT y sueldos del personal
ok_by:
  - dueña
```

`ok_by` lista los roles que pueden dar el OK para intervenir (`intervene` avisa si es otro).

Un origen documento se busca bajo `read` (un nombre de archivo suelto se busca ahí; en `never` no se
busca). Sin alcance, los orígenes documento quedan como aviso; con `check --strict`, como error.

## 6 · Verificar

```bash
python scripts/manual.py check --company ferreteria-andes
```

Para el manual de muestra:

```
  NEGOCIO.md                  113 / 400 palabras
  procesos/COMPRAS.md         159 / 800 palabras · En revisión · rev. B · 5 pasos
errores 0 · avisos 0 · supuestos 1
  SUPUESTO · COMPRAS-04 · monto no confirmado
OK
```

Cualquier error termina en `FALLA` y código de salida 1: **la página no está lista hasta que la
verificación pasa**. Las palabras se cuentan solo en el cuerpo (el frontmatter y el Historial no
cuentan): 400 el índice, 800 cada proceso. `--json` entrega cada hallazgo con archivo y línea.

## 7 · Revisar y aprobar

Después de un cambio en la página:

```bash
python scripts/manual.py revise COMPRAS --change "COMPRAS-03 enlazado al comparativo" --by dueña
```

Se agrega una fila al historial, la revisión pasa a la letra siguiente (A → B), el estado queda En
revisión, y se actualizan la fecha de la página y la fila del índice.

**La aprobación es del operador.** Solo después de que la dueña dice que sí a la página:

```bash
python scripts/manual.py revise COMPRAS --change "Aprobado" --approve --by dueña
```

La revisión pasa a `0` y el estado a Aprobado. El script se niega si la página tiene errores o si
falta `--by`. Desde ahí, cada cambio se aprueba de nuevo (`1`, `2`…); un cambio sin `--approve` a
una página aprobada se rechaza, así que se prepara en `trabajo/` hasta el OK.

## 8 · Qué carga una sesión

El índice (`NEGOCIO.md`) y el único proceso que toca la tarea. El registro de la entrevista y la
bitácora se abren solo para resolver un origen. Si un proceso pasa las 800 palabras, contiene dos
procesos: se divide.

## Errores que la verificación ataja

| Error | Código |
|---|---|
| Un paso escrito de memoria | `source-missing` |
| Dos orígenes mezclados en un paso | `source-multiple` |
| Una línea de Operación sin su origen, o con otra etiqueta | `source-missing` · `operation-line` |
| La fecha de la entrevista no es la de una tanda | `interview-missing` |
| Una línea de bitácora adivinada | `logbook-line-missing` |
| Un documento fuera del alcance | `document-missing` · `document-out-of-scope` |
| El mismo código dos veces, o un código que no es `COMPRAS-NN` | `code-duplicate` · `code-format` |
| «Aprobado» escrito a mano con revisión en letra | `status-revision` |
| Frontmatter editado sin `revise` | `history-mismatch` · `history-sequence` |
| Una fecha como 2026-10-16 o 31-02-2026 | `date-format` |
| Una página que no está en el índice, o una fila sin su página | `index-row-missing` · `index-file-missing` |
| Una página que creció demasiado | `cap-words` |
