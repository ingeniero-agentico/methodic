# Intervenir · guía paso a paso

El mismo método de `SKILL.md`, para una persona. Se recorre con un caso ficticio: en **Ferretería
Andes** la dueña le pide al agente arreglar la plantilla de orden de compra, cuya columna IVA sale
vacía. El contrato detrás de cada regla es `docs/MANUAL-FORMAT.md`.

**Qué es esta skill.** Una forma de dejar que un agente cambie archivos en tu computador sin perder
el control: lee solo las carpetas que autorizaste, escribe libre solo en su propia carpeta de
trabajo y cambia un archivo tuyo solo después de mostrarte el plan, recibir tu sí para ese cambio y
hacer un respaldo. Después comprueba el resultado con un hecho y anota una línea en la bitácora.

**Qué no es.** El texto de la skill guía al modelo; no lo detiene. Lo que lo detiene son los
permisos del programa de agente que uses. Por eso la skill genera un archivo de permisos para
Claude Code, y el paso 1 de abajo es instalarlo.

## 0 · Qué tiene que existir antes

| Pieza | Dónde | Quién la escribe |
|---|---|---|
| Perfil | `<datos>/profiles/ferreteria-andes.yaml` | tú (`language: es` o `en`) |
| Manual | `<datos>/manual/ferreteria-andes/` | las skills `interview` y `manual` |
| Alcance | `<datos>/manual/ferreteria-andes/alcance.yaml` | tú y el agente, en la tercera ronda de la entrevista |

`<datos>` es `--data`, o `$METHODIC_DATA`, o `$INGENIERO_DATOS`, o la carpeta `methodic-data` al
lado del repo (después la antigua `ingeniero-agentico-datos`). El alcance de ejemplo es
`templates/alcance-ferreteria-andes.yaml`:

| Lista | Ferretería Andes | Qué significa |
|---|---|---|
| `read` | `C:/Users/usuario/Documents/FerreteriaAndes` | se puede leer |
| `write_with_ok` | `.../FerreteriaAndes/Planillas` | se puede cambiar, un cambio aprobado a la vez |
| `never` | `.../FerreteriaAndes/Sueldos`, `.../Bancos` | no se lee ni se toca |
| `ok_by` | `dueña`, `encargado de compras` | roles que pueden dar el OK; `log --ok` avisa con cualquier otro (una lista vacía acepta cualquier rol y avisa) |

Lo que no está bajo `read` queda fuera del alcance, **incluida una carpeta de `write_with_ok` que no
esté dentro de una de `read`** (el script avisa). La carpeta `trabajo/` del manual siempre se escribe
libre.

## 1 · Instalar los permisos (Claude Code)

```bash
python skills/intervene/scripts/intervene.py permissions --platform claude-code
```

Escribe `trabajo/permisos-claude-code.json` (`work/claude-code-permissions.json` con
`language: en`) y nada más: nunca toca la configuración de tu agente. Lo que trae:

| Lista | Reglas | Efecto |
|---|---|---|
| `allow` | `Read(//c/.../FerreteriaAndes/**)`, la carpeta del manual; `Edit(//c/.../trabajo/**)` | leer y trabajar sin preguntas |
| `ask` | `Edit(//c/.../Planillas/**)`, el archivo de alcance, `mcp__*` | una pregunta antes de cada cambio ahí, y antes de cada herramienta MCP (correo, chat, pagos) |
| `deny` | `Read` y `Edit` de cada carpeta `never`; `Edit` de los respaldos y la bitácora; `Edit` de las carpetas `read` sin nada escribible adentro; borrar (`rm`, `rmdir`, `del`, `rd`, `Remove-Item`...), red (`curl`, `wget`, `Invoke-WebRequest`, `Invoke-RestMethod`, `WebFetch`, `WebSearch`), instalar (`pip install`, `npm install`, `npx`, `winget`, `choco`, `msiexec`...) y `git push` | rechazado |

También fija `defaultMode: "default"` (pregunta antes de editar) y desactiva los modos bypass y
auto. `templates/claude-code-settings.json` es la misma idea sin rutas, para cualquier carpeta.

Dos formas de usarlo (lo haces tú, no el agente):

- **Una sesión:** inicia Claude Code con el archivo:
  `claude --settings "C:/Users/usuario/methodic-data/manual/ferreteria-andes/trabajo/permisos-claude-code.json"`.
  Se aplica por encima de tus archivos de usuario y de proyecto, y por debajo de la configuración
  administrada; no cambia ningún archivo.
- **Siempre, para una carpeta:** pon el bloque `permissions` del archivo generado en el
  `.claude/settings.local.json` de la carpeta donde inicias Claude Code. Si ese archivo ya tiene
  listas, agrega las reglas a ellas: Claude Code junta las listas de todos los archivos, y un deny
  siempre gana.

Inicia Claude Code **en la carpeta `trabajo/` del manual**: así el único directorio de trabajo es el
área libre, y todo lo demás pasa por las reglas de arriba. Con `/permissions` ves las reglas
cargadas y con `/status` confirmas que el archivo se cargó.

**Verificado contra la documentación oficial el 16-10-2026:**
`https://code.claude.com/docs/en/permissions` (sintaxis de reglas, orden `allow`/`ask`/`deny`,
`Bash`, `PowerShell`, rutas de `Read`/`Edit`, `WebFetch`, enlaces, modos) y
`https://code.claude.com/docs/en/settings` (alcances de archivo, `--settings`, cómo se juntan las
listas, `$schema`). La dirección `code.claude.com/docs/en/iam` hoy lleva a la página de
autenticación; los permisos se movieron a `/permissions`. Lo que dicen esas páginas, y en lo que se
apoya este archivo:

- Las reglas se revisan deny, luego ask, luego allow; la primera que calza decide. Un allow no abre
  una excepción dentro de un deny.
- `Bash(rm *)` y `Bash(rm:*)` son lo mismo; un ` *` al final calza también el comando solo. Las
  reglas de PowerShell tienen la misma forma, no distinguen mayúsculas y calzan los alias comunes
  (el ejemplo de la página: `Get-ChildItem` calza también `gci`, `ls`, `dir`; por la misma regla
  `Remove-Item` cubre `rm` y `del` escritos en PowerShell).
- En Windows una ruta se compara en forma POSIX: `C:\Users\usuario` pasa a `/c/Users/usuario`, así
  que una regla absoluta es `//c/Users/usuario/...`. Un solo `/` al inicio **no** es absoluto.
- Las reglas `Edit` cubren todas las herramientas que editan, `Write` incluida; un deny de `Read`
  también bloquea `Edit` y `Write` en esa ruta. Una regla de ruta escrita como `Write(...)` nunca se
  consulta.
- Un `WebFetch` o `WebSearch` solo, en `deny`, saca la herramienta.
- A través de un enlace o junction, un allow exige que calcen el enlace y su destino; a un deny le
  basta uno de los dos.

**Lo que no puede impedir (también de esas páginas, dicho en claro):**

- Una regla `Bash` o `PowerShell` calza el texto del comando, no el programa. `Bash(rm *)` detiene
  `rm -rf x/` pero no `/bin/rm -rf x/` ni `bash -c 'rm -rf x/'`; tampoco calza `cmd /c del`.
- Las reglas `Read` y `Edit` no alcanzan a un script que abre archivos por su cuenta (un Python que
  corre el agente). Por eso `intervene.py` revisa el alcance por sí mismo.
- Los comandos de solo lectura (`cat`, `ls`, `grep`) corren sin preguntar incluso fuera del
  directorio de trabajo. Un deny de `Read` sí alcanza a `cat`, `head` o `tail` que nombran una ruta
  `never`, pero no a un `grep -r` lanzado desde una carpeta de más arriba.
- Una carpeta `read` que contiene una de `write_with_ok` no se puede negar para `Edit` sin bloquear
  también la escribible (un deny gana sobre todo, y la excepción con `!` funciona solo con rutas
  relativas). Los cambios ahí quedan en la pregunta normal del modo `default`.
- Para una barrera que no dependa del texto del comando, Claude Code tiene un sandbox a nivel del
  sistema operativo; esta skill no lo configura.

**Otros agentes.** `templates/codex.md`, `cursor.md` y `gemini-cli.md` dicen qué se verificó en
cada uno. Donde algo no está verificado (por ejemplo, negar la lectura de una carpeta), las reglas
de la skill y `intervene.py check` son la única barrera.

## 2 · El caso, paso a paso

La dueña dice: «arregla la plantilla de OC, la columna IVA sale vacía». La página del proceso
`procesos/COMPRAS.md` tiene el paso **COMPRAS-05** (emitir la orden de compra).

**Revisar.** `intervene.py check C:/Users/usuario/Documents/FerreteriaAndes/Planillas/plantilla-oc.xlsx --write`
responde `write-needs-ok`: se puede cambiar, por el ciclo.

**Plan.** El agente escribe el plan y lo muestra:

```
Plan 1 · COMPRAS-05 · pide OK
   Archivo   C:/Users/usuario/Documents/FerreteriaAndes/Planillas/plantilla-oc.xlsx
   Cambio    columna IVA corregida
   Por qué   la OC salía sin IVA
   Verificar total = neto × 1,19
   Antes     respaldo en respaldos/
¿Lo hago? Responde sí o no (este OK cubre solo esta acción).
```

**OK.** La dueña responde «sí». Ese sí cubre solo este cambio.

**Respaldo.** `intervene.py backup .../plantilla-oc.xlsx` imprime
`respaldos/plantilla-oc_2026-10-16_1542.xlsx`. Un segundo respaldo en el mismo minuto lleva
segundos (`_154200`), después `-2`: ninguno pisa a otro.

**Ejecutar y verificar.** El agente corrige la columna, vuelve a abrir el archivo y recalcula una
fila: neto 100.000, IVA 19.000, total 119.000. Ese es el hecho.

**Bitácora.** `intervene.py log --step COMPRAS-05 --file .../plantilla-oc.xlsx --change "columna IVA corregida" --backup respaldos/plantilla-oc_2026-10-16_1542.xlsx --verified "total 119.000 = 100.000 × 1,19" --ok dueña`
agrega:

```
16-10-2026 15:42 · COMPRAS-05 · plantilla-oc.xlsx · columna IVA corregida · respaldo: respaldos/plantilla-oc_2026-10-16_1542.xlsx · verificado: total 119.000 = 100.000 × 1,19 · OK: dueña
```

y dice que es, por ejemplo, la línea 7. La página del proceso ya puede citar
`observado · bitácora, línea 7`.

## 3 · Ordenar una carpeta

Un plan por archivo: «mover `cotizacion (3).pdf` a `Cotizaciones/2026-10_proveedor-a.pdf`». Se
pueden mostrar varios planes juntos, numerados, y responderlos juntos por número («sí a 1, 2 y
4»). No se borra nada: lo que se retira va a `_archivo` (por el ciclo) o la persona lo manda a la
papelera.

## 4 · Cuando algo sale mal

- **La verificación falla.** El agente lo dice y propone restaurar el respaldo como un plan nuevo.
  La restauración lleva su propia línea en la bitácora, que cita la fallida con `--corrects N`.
- **Una línea de la bitácora está mal.** Nunca se edita: una línea nueva con `--corrects N`.
- **Pediste algo prohibido** (borrar, instalar, enviar, pagar, una carpeta fuera del alcance): el
  agente lo deja listo en `trabajo/` (el comando, el borrador, la lista) y lo haces tú.

## Errores que el método atrapa

| Error | Dónde se atrapa |
|---|---|
| Una ruta que se escapa por `..`, un enlace o un junction | `check` juzga la ruta pedida y la real; gana la más estricta |
| Un cambio sin respaldo | `log` rechaza un respaldo que no existe o que está fuera de `respaldos/` |
| «Se ve bien» como verificación | `log` lo rechaza |
| Una bitácora reescrita | `log` solo agrega; `--corrects` suma una línea |
| Un respaldo pisado por el siguiente | los respaldos se crean en modo exclusivo, con segundos y contador |
| Un archivo de permisos instalado por el agente | `permissions` escribe solo dentro de `trabajo/` |

La prueba (`python scripts/intervene.py --test`) arma este caso en una carpeta temporal (con un CSV
en lugar del libro Excel), recorre cada veredicto, el ciclo completo y los rechazos, borra su
carpeta temporal y termina en `OK`.
