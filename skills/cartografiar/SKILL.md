---
name: cartografiar
description: Use at the start of any engagement (stage 0 of ingeniero-agentico) to map the folders of a job before anyone reads them (what files exist, where, from when, what each one says in one line and what links to what), and to decide whether this is a first pass or a re-read. Also when someone returns to a topic already worked ("¿qué cambió desde la última vez?"), when a folder is too large to read file by file, or when the orchestrator needs contexto/MAPA.md, grafo.json and huellas.json. Runs a deterministic script with no LLM; the mode (primera-vez or relectura) comes from comparing file fingerprints, never from judgment. Cartografía las carpetas del encargo sin LLM y decide si se lee todo o solo lo que cambió.
---

# Cartografiar · etapa 0

**El ahorro de la relectura es leer el mapa en vez de las carpetas.** Esta skill deja ese mapa,
barato y siempre igual para la misma entrada, y decide el modo comparando huellas (tamaño, fecha
y sha1 de cada archivo). El modelo no elige el modo «a ojo».

El script hace todo: recorre, resume cada archivo en una línea sin LLM, saca los enlaces, compara
con la corrida anterior y escribe los tres archivos. El agente solo elige qué carpetas, completa
lo que el script dejó vacío y nombra los huecos.

```bash
python scripts/mapa_contexto.py <carpeta> [<carpeta> ...] --salida <contexto/> [--excluir PATRON] [--umbral 0.20] [--nucleo ruta1,ruta2] [--graphify]
python scripts/mapa_contexto.py --salida <contexto/> --marcar-leido   # lo llama orquestar al consolidar
python scripts/mapa_contexto.py --probar      # el caso ficticio tiene que terminar en OK
```

La última línea que imprime es la que se lee:

```
MODO: relectura · cambiados 1 · mapa 454 palabras
```

## Cuándo usarla

- Llega un encargo con una o varias carpetas y todavía nadie las leyó (`primera-vez`).
- Se vuelve a un tema ya trabajado: el mapa dice qué cambió y basta releer eso (`relectura`).
- La carpeta es grande y leerla entera gasta más de lo que vale.

## Dónde queda `contexto/`

Junto a los datos del encargo, **nunca en el repo público** (`ARQUITECTURA.md`):
`<datos>/casos/<caso>/contexto/`, o `<carpeta del encargo>/contexto/` si no hay carpeta de datos.
Si la carpeta del encargo es de solo lectura, la salida va a `<datos>/casos/<caso>/contexto/`.
Si `contexto/` queda dentro de la carpeta cartografiada, el script la excluye solo.

## Lo que calcula el script

| Paso | Regla |
|---|---|
| Recorrido | Todas las carpetas dadas. Excluye `.git`, `node_modules`, `__pycache__`, `.venv`, `.obsidian`, `graphify-out` y parecidos, archivos de sistema (`~$…`, `desktop.ini`), binarios sobre `--max-mb` (25 MB), lo que calce con `--excluir` y la carpeta de salida. No sigue enlaces ni junctions |
| Resumen | Sin LLM. `.md`: título · campos de estado (`Estado`, `Para qué`, `Reemplaza a`, `Cliente`) · `description` del frontmatter o primera frase · secciones `##`. `.json`/`.yaml`: claves de primer nivel. `.py`: docstring o primer comentario. `.xlsx`: hojas con su tamaño y la primera fila (openpyxl). `.pdf`: título o primera línea y páginas (pypdf). `.docx`: título y primer párrafo. Imágenes: dimensiones. Lo demás: solo el nombre |
| Enlaces | `[[wikilinks]]`, enlaces markdown a archivos locales, rutas citadas en el texto que existan (entre comillas invertidas o sueltas) y `skill:`/`skills:` del frontmatter. Solo entra una arista si el destino existe; una skill que no está en las carpetas queda como nodo externo `skill:<nombre>` |
| Huellas | Por archivo: tamaño, fecha (ns) y sha1 de 12 caracteres. Si tamaño y fecha no cambiaron, reutiliza el sha1 y el resumen anteriores sin volver a abrir el archivo |
| Cambios | Cada corrida compara contra la anterior y, si algo cambió, anota la diferencia con su fecha en `cambios.json`. Lo anotado se **acumula** hasta `--marcar-leido`: correr dos veces no borra lo pendiente. En neto: nuevo y después cambiado sigue nuevo; nuevo y después borrado desaparece |
| Modo | Se calcula contra lo **acumulado no leído**. Sin `huellas.json` previo, sin `MAPA.md` o con otras raíces: `primera-vez`. Una `primera-vez` sigue siéndolo hasta que se marque leída. Si no: archivos acumulados ÷ archivos de la base (la del último `--marcar-leido`). Hasta `--umbral` (20 %): `relectura` con la lista; sobre el umbral: `primera-vez`. Un archivo cuya fecha cambió pero su sha1 no, **no cuenta como cambiado** |
| Núcleo | Hasta 3 archivos que se leen siempre, por regla fija: 1) los de `--nucleo`; 2) nombres clave `LEEME`, `README`, `TRABAJO`, `CLAUDE`, `INDICE` (el menos profundo primero, en ese orden); 3) los más enlazados, sin imágenes, comprimidos ni CAD; empate: el más reciente. Una ruta de `--nucleo` que no está en el mapa aborta |
| Tope | `MAPA.md` ≤ 3.000 palabras (`--max-palabras`). Si se pasa, comprime por niveles: acorta resúmenes, deja los archivos más relevantes de cada carpeta («+N más»), agrupa carpetas, y como último recurso corta con aviso |

Relevancia de un archivo (decide quién queda al comprimir): enlaces entrantes × 3 + salientes,
más si es documento, si se llama `LEEME`, `README`, `SKILL`, `CLAUDE`, `INDICE`, `RESULTADO` o
parecido, y si cambió en los últimos 30 días del conjunto.

## Lo que decide el agente

1. **Qué carpetas.** Las del encargo, no la raíz del disco. Varias carpetas van en la misma
   llamada (cada una queda con su nombre como prefijo).
2. **Qué excluir de más.** Salidas generadas, respaldos, carpetas de otro tema: `--excluir`.
   **Qué fijar en el núcleo.** Si la regla deja afuera un archivo central (o mete uno reemplazado),
   `--nucleo` lo corrige. Se pasa en cada corrida: no se guarda.
3. **Completar resúmenes.** El mapa trae «Sin resumen (N)» ordenado por relevancia. Se abren a lo
   más **10** de esos, solo los que pesan para el encargo, y se anota su línea en la respuesta (el
   script no se edita a mano).
4. **Nombrar los huecos.** Lo que el encargo necesita y el mapa no muestra: un documento que se
   cita y no está, una cotización que falta, un dato sin fuente. Eso alimenta la etapa 1.

## Cómo se lee la salida

| Archivo | Para quién | Qué trae |
|---|---|---|
| `MAPA.md` | el orquestador y la persona | el MODO arriba, «Núcleo · leer siempre», «A releer» (si es relectura, con la fecha desde la que se acumula), carpetas, una línea por archivo, lo más reciente, más enlazados, huérfanos y sin resumen |
| `grafo.json` | scripts y graphify | `nodes` (`id`, `label`, `type`, `file_type`, `source_file`, `resumen`, grados) y `links` (`source`, `target`, `relation`, `confidence`). `graph.nucleo`, `graph.cambios` (lo acumulado completo) y `graph.cambios_esta_corrida` |
| `huellas.json` | la próxima corrida | el estado de cada archivo en la última corrida |
| `cambios.json` | la próxima corrida y `orquestar` | la base (archivos al último `--marcar-leido`), si hay una primera vez pendiente y las corridas no leídas con su fecha |

**Relectura = núcleo + «A releer» + el mapa.** Nada más.

Relaciones: `wikilink`, `enlace` y `usa_skill` son `EXTRACTED` (el archivo lo dice); `cita` es
`INFERRED` (una ruta en el texto que calza con un archivo).

**Lo pendiente lo vacía quien lee, no quien mapea.** `orquestar` corre `--marcar-leido` al
consolidar, cuando lo cambiado ya se leyó. Hasta entonces, cada corrida suma a la lista.

## graphify (opcional)

Con `--graphify`, si está instalado, el mapa agrega cómo enriquecerlo con `/graphify` (extrae
conceptos con un modelo; el script **no** lo llama). `grafo.json` tiene la misma forma que
`graphify-out/graph.json` y `graphify merge-graphs` los junta.

## Errores típicos

| Síntoma | Causa |
|---|---|
| Siempre sale `primera-vez` | Nadie corrió `--marcar-leido` después de la primera vez; o la salida cambia de carpeta entre corridas; o se pasan las raíces en otro orden |
| «A releer» trae archivos que ya se leyeron | Faltó `--marcar-leido` al consolidar |
| El núcleo trae un archivo reemplazado | La regla no lee «reemplaza a»: fijar el correcto con `--nucleo` |
| Sale `relectura` con muchos cambios esperados | El umbral es alto para ese encargo: bajar `--umbral` |
| Un archivo editado no aparece en «A releer» | Se guardó sin cambiar el contenido (mismo sha1): es correcto |
| El mapa se llena de archivos generados | Falta `--excluir` (por ejemplo `--excluir "salida*"`) |
| Un PDF sale solo con «N pág.» | No trae título ni texto en la primera página (escaneo): va a «abrir a mano» si es clave |
| Una ruta de más de 260 caracteres | El script usa el prefijo `\\?\` en Windows; si aun así falta, revisar permisos |
