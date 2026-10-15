# Cartografiar · guía paso a paso

El mismo método de `SKILL.md`, para una persona. Se recorre con el caso ficticio de
`pruebas/caso-ficticio.json`: la carpeta de un encargo de compra de la **Ferretería Andes** para
**Constructora Sur**, con notas, datos, un script y una skill.

## 0 · Para qué sirve

Antes de investigar o calcular hay que saber qué hay. Leer una carpeta archivo por archivo es lo
más caro del trabajo; el mapa lo hace una vez y, cuando se vuelve al tema, dice qué cambió. Si
casi nada cambió, se lee el mapa y esos pocos archivos: eso es la **relectura**.

## 1 · Elegir las carpetas y la salida

- **Carpetas:** las del encargo. En el caso, `encargo/`.
- **Salida:** una carpeta `contexto/` junto a los datos del encargo. Nunca dentro de un repo
  público, y nunca dentro de una carpeta que no se puede tocar (en ese caso va a
  `<datos>/casos/<caso>/contexto/`).

## 2 · Correr la primera vez

```bash
python scripts/mapa_contexto.py encargo --salida encargo/contexto
```

Lo que pasa en el caso (lo verifica `--probar` contra `pruebas/esperado.json`):

- **9 archivos** (10 si openpyxl está y la prueba agrega `datos/planilla.xlsx`). `.git/` y
  `node_modules/` no entran.
- **8 enlaces:** `LEEME.md` → `compras/notas.md` por wikilink; `LEEME.md` → `datos/perfil.yaml` por
  enlace markdown; `compras/notas.md` cita `scripts/calculo.py` y `datos/resumen.json` en el texto;
  `skills/comprar/SKILL.md` cita `compras/notas.md`; `agentes/comprador.md` usa la skill `comprar`
  (que está en la carpeta) y la skill `cotizar` (que no está: queda como nodo externo).
- **Núcleo:** `LEEME.md` y `TRABAJO.md` (nombres clave, en la raíz) y `compras/notas.md` (el más
  enlazado: 2 entrantes).
- **Resúmenes sin LLM:** `scripts/calculo.py` → su docstring; `datos/perfil.yaml` → «claves:
  empresa, moneda, iva»; `TRABAJO.md` → «Trabajo ficticio · estado: abierto · cliente: Constructora
  Sur · Se compran cañerías para una red de agua. · secciones: Qué se pidió; Qué falta».
- **Huérfanos:** `huerfano.txt` y `TRABAJO.md` (nadie los cita y no citan a nadie).
- La línea final dice `MODO: primera-vez`.

## 3 · Leer `MAPA.md`

En este orden:

1. **El MODO** (línea 3). En primera vez, todo es nuevo.
2. **Núcleo · leer siempre:** los tres archivos por los que se entra al tema. Si la regla eligió
   mal (por ejemplo, un listado ya reemplazado), se corre de nuevo con `--nucleo`.
3. **Carpetas:** cuántos archivos, de qué tipo y de cuándo.
4. **Archivos:** una línea por archivo: nombre, tamaño, fecha, resumen.
5. **Más enlazados:** por dónde seguir leyendo.
6. **Huérfanos:** lo que nadie cita (o sobra, o falta enlazarlo).
7. **Sin resumen:** lo que el script no pudo leer. Se abren a mano solo los que importan (10 como
   máximo).

## 4 · Marcar leído

Cuando el tema ya se leyó y se cerró el encargo, se vacía lo pendiente:

```bash
python scripts/mapa_contexto.py --salida encargo/contexto --marcar-leido
```

Hasta que eso pase, **la primera vez sigue siendo primera vez** aunque se corra el mapa de nuevo:
nadie la ha leído. Después de marcar, la base son los 10 archivos de ese momento.

## 5 · Volver al tema

Se edita `compras/notas.md` (llegó una cuarta cotización) y se corre igual:

```bash
python scripts/mapa_contexto.py encargo --salida encargo/contexto
```

Cambió 1 de 10 archivos (10 %, bajo el umbral de 20 %): **`MODO: relectura`**, y «A releer»
lista exactamente `compras/notas.md`. Se lee el núcleo, ese archivo y el mapa; nada más.

**Lo no leído se acumula.** Si se corre otra vez sin marcar leído, `compras/notas.md` sigue en
«A releer». Si además cambia `scripts/calculo.py`, la lista trae los dos y `cambios.json` guarda
las dos corridas con su fecha. Recién `--marcar-leido` la deja en 0.

Si en cambio se tocan tres archivos y se borra `huerfano.txt`, cambian 4 de 10 (40 %) y vuelve a
`primera-vez`: el tema cambió lo suficiente como para releerlo entero.

(Las cifras son las que imprime `--probar` con openpyxl instalado; sin la planilla son 9 archivos.)

## 6 · Árbol grande

Con 1.200 notas en 40 carpetas, el mapa completo pasaría las 3.000 palabras. El script comprime:
acorta resúmenes, deja en cada carpeta los archivos más relevantes y resume el resto («+N más:
12 markdown»). La prueba exige que quede bajo el tope.

## Errores que el método ataja

| Error | Dónde se ataja |
|---|---|
| Leer todo otra vez sin necesidad | el modo sale de las huellas, no del criterio del modelo |
| Perder un cambio porque el mapa se corrió dos veces | lo no leído se acumula hasta `--marcar-leido` |
| Releer solo lo cambiado y perder el hilo del tema | el núcleo se lee siempre |
| Creer que algo cambió porque cambió su fecha | se compara el sha1, no la fecha |
| Un mapa tan largo que nadie lo lee | tope de 3.000 palabras con compresión por relevancia |
| Cartografiar las propias salidas | la carpeta `contexto/` se excluye sola |
| Un enlace a un archivo que no existe | solo entra una arista si el destino existe |
