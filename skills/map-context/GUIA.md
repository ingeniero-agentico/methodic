# Cartografiar · guía paso a paso

El mismo método de `SKILL.md`, para una persona. Se recorre con el caso ficticio de
`tests/sample-case.json`: la carpeta de un encargo de compra de la **Ferretería Andes** para
**Constructora Sur**, con notas, datos, un script y una skill. (El caso y las salidas del script
están en inglés; la versión en inglés de esta guía es `GUIDE.md`.)

## 0 · Para qué sirve

Antes de investigar o calcular hay que saber qué hay. Leer una carpeta archivo por archivo es lo
más caro del trabajo; el mapa lo hace una vez y, cuando se vuelve al tema, dice qué cambió. Si
casi nada cambió, se lee el mapa y esos pocos archivos: eso es la **relectura** (`reread`).

## 1 · Elegir las carpetas y la salida

- **Carpetas:** las del encargo. En el caso, `task/`.
- **Salida:** una carpeta `context/` junto a los datos del encargo. Nunca dentro de un repo
  público, y nunca dentro de una carpeta que no se puede tocar (en ese caso va a
  `<datos>/casos/<caso>/context/`).

## 2 · Correr la primera vez

```bash
python scripts/map_context.py task --out task/context
```

Lo que pasa en el caso (lo verifica `--test` contra `tests/expected.json`):

- **9 archivos** (10 si openpyxl está y la prueba agrega `data/sheet.xlsx`). `.git/` y
  `node_modules/` no entran.
- **8 enlaces:** `README.md` → `purchasing/notes.md` por wikilink; `README.md` → `data/profile.yaml` por
  enlace markdown; `purchasing/notes.md` cita `scripts/calculation.py` y `data/summary.json` en el texto;
  `skills/buy/SKILL.md` cita `purchasing/notes.md`; `agents/buyer.md` usa la skill `buy`
  (que está en la carpeta) y la skill `quote` (que no está: queda como nodo externo).
- **Núcleo:** `README.md` y `JOB.md` (nombres clave, en la raíz) y `purchasing/notes.md` (el más
  enlazado: 2 entrantes).
- **Resúmenes sin LLM:** `scripts/calculation.py` → su docstring; `data/profile.yaml` → «keys:
  company, currency, vat»; `JOB.md` → «Fictitious job · status: open · client: Constructora
  Sur · Pipes are bought for a water network. · sections: What was asked; What is missing».
- **Huérfanos:** `orphan.txt` y `JOB.md` (nadie los cita y no citan a nadie).
- La línea final dice `MODE: first-run`.

## 3 · Leer `MAP.md`

En este orden:

1. **El MODO** (línea 3). En primera vez, todo es nuevo.
2. **Núcleo · leer siempre** («Core · always read»): los tres archivos por los que se entra al
   tema. Un archivo que otro declara reemplazado («Reemplaza a» o «Replaces») queda fuera y el
   mapa lo dice. Si la regla igual eligió mal, se corre de nuevo con `--core`.
3. **Carpetas:** cuántos archivos, de qué tipo y de cuándo.
4. **Archivos:** una línea por archivo: nombre, tamaño, fecha, resumen.
5. **Más enlazados:** por dónde seguir leyendo.
6. **Huérfanos:** lo que nadie cita (o sobra, o falta enlazarlo).
7. **Sin resumen:** lo que el script no pudo leer. Se abren a mano solo los que importan (10 como
   máximo).

## 4 · Marcar leído

Cuando el tema ya se leyó y se cerró el encargo, se vacía lo pendiente:

```bash
python scripts/map_context.py --out task/context --mark-read
```

Hasta que eso pase, **la primera vez sigue siendo primera vez** aunque se corra el mapa de nuevo:
nadie la ha leído. Después de marcar, la base son los 10 archivos de ese momento.

## 5 · Volver al tema

Se edita `purchasing/notes.md` (llegó una cuarta cotización) y se corre igual:

```bash
python scripts/map_context.py task --out task/context
```

Cambió 1 de 10 archivos (10 %, bajo el umbral de 20 %): **`MODE: reread`**, y «A releer»
(«To reread») lista exactamente `purchasing/notes.md`. Se lee el núcleo, ese archivo y el mapa;
nada más.

**Lo no leído se acumula.** Si se corre otra vez sin marcar leído, `purchasing/notes.md` sigue en
«A releer». Si además cambia `scripts/calculation.py`, la lista trae los dos y `changes.json` guarda
las dos corridas con su fecha. Recién `--mark-read` la deja en 0.

Si en cambio se tocan tres archivos y se borra `orphan.txt`, cambian 4 de 10 (40 %) y vuelve a
`first-run`: el tema cambió lo suficiente como para releerlo entero.

(Las cifras son las que imprime `--test` con openpyxl instalado; sin la planilla son 9 archivos.)

Un contexto escrito antes de la v1.1 (`contexto/` con `MAPA.md`, `huellas.json` y `cambios.json`)
se lee tal cual y conserva sus nombres. Las opciones antiguas (`--salida`, `--nucleo`,
`--marcar-leido`, `--probar`) siguen funcionando.

## 6 · Árbol grande

Con 1.200 notas en 40 carpetas, el mapa completo pasaría las 3.000 palabras. El script comprime:
acorta resúmenes, deja en cada carpeta los archivos más relevantes y resume el resto («+N more:
12 markdown»). La prueba exige que quede bajo el tope.

## Errores que el método ataja

| Error | Dónde se ataja |
|---|---|
| Leer todo otra vez sin necesidad | el modo sale de las huellas, no del criterio del modelo |
| Perder un cambio porque el mapa se corrió dos veces | lo no leído se acumula hasta `--mark-read` |
| Releer solo lo cambiado y perder el hilo del tema | el núcleo se lee siempre |
| Leer un listado viejo como si fuera el vigente | un archivo declarado reemplazado nunca entra al núcleo por regla |
| Creer que algo cambió porque cambió su fecha | se compara el sha1, no la fecha |
| Un mapa tan largo que nadie lo lee | tope de 3.000 palabras con compresión por relevancia |
| Cartografiar las propias salidas | la carpeta `context/` se excluye sola |
| Un enlace a un archivo que no existe | solo entra una arista si el destino existe |
