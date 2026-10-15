---
name: auditar
description: Use when the outputs of a method of this repo (adquisiciones, costo-y-precio, evaluacion-economica, evaluacion-financiera) must be checked before anyone relies on them — stage 4 of an encargo, after the ejecutor agents finished, or whenever someone asks "¿esto está bien calculado?", "audita el caso", "¿se puede reproducir?". Re-runs each method script with the same input in a temporary folder and compares every figure against the archived output (JSON and Excel), detects whether the script wrote into the case folder, reads a value by path and cross-checks values between chained methods (the project NPV that evaluacion-financiera read must equal the one evaluacion-economica produced). It is the mechanical half of the independent auditor agent; it never fixes anything. Vuelve a correr cada método en una carpeta temporal y compara cifra por cifra contra la salida archivada.
---

# Auditar · re-ejecutar y comparar

La mitad mecánica de la etapa 4. El juicio (supuestos, fiabilidad, trazabilidad, veredicto) lo pone
el agente `auditor`; esta skill solo responde dos preguntas sin opinión: **¿la salida archivada sale
igual si se vuelve a correr?** y **¿dos métodos encadenados dicen el mismo número?**

```
python scripts/recorrer.py correr --script <metodo.py> --original <salida.json> [--original <salida.xlsx>] -- <args con {SALIDA}>
python scripts/recorrer.py manifiesto <caso>/contexto/ejecuciones/
python scripts/recorrer.py valor <archivo.json> <ruta>
python scripts/recorrer.py cruzar <a.json> <ruta_a> <b.json> <ruta_b> [--tol-abs 1]
python scripts/recorrer.py --probar
```

## Qué hace `recorrer.py`

| Paso | Regla |
|---|---|
| Carpeta temporal | `{SALIDA}` en los argumentos se reemplaza por una carpeta temporal nueva. **Sin `{SALIDA}` no corre**: la salida iría a la carpeta del caso y pisaría la archivada |
| Misma entrada | La entrada se lee desde su lugar original (solo lectura); las rutas relativas que pida (por ejemplo `flujo_proyecto`) siguen resolviendo igual |
| Comparar JSON | Recorre todo el árbol: cada número con tolerancia (`--tol-abs 0.01`, `--tol-rel 1e-9`), cada texto exacto, listas por posición y largo |
| Comparar Excel | Con openpyxl: cada celda de cada hoja, valor y color de relleno (el amarillo o naranjo que marca un `SUPUESTO` también se compara) |
| Vigilar el caso | Toma una foto (tamaño y fecha) de las carpetas del caso antes y después. Si el script escribió ahí, lo informa como cambio |
| Si el script falla | Devuelve `FALLA` y su salida **tal cual** |
| Código de salida | 0 = `IGUAL` · 1 = `DISTINTO` (o cambió algo en el caso) · 2 = `FALLA` o `FALTA` |

Rutas dentro de un JSON: `indicadores.van`, `filas[0].valor`, `alternativas["Leasing 36 cuotas"].cae`.

## El manifiesto de una ejecución (contrato con el agente `ejecutor`)

Cada corrida del ejecutor deja `<caso>/contexto/ejecuciones/<id>.json`. Es lo que permite
re-ejecutar sin adivinar el comando:

```json
{
  "id": "evaluacion-economica-base",
  "metodo": "evaluacion-economica",
  "fecha": "DD-MM-AAAA",
  "script": "skills/evaluacion-economica/scripts/evaluar.py",
  "args": ["<ruta absoluta>/entrada.json", "--perfil", "<empresa>", "--salida", "{SALIDA}"],
  "carpeta_salida": "<ruta absoluta del caso>",
  "salidas": ["<caso>/salida.json", "<caso>/salida.xlsx"],
  "cifra_decisiva": {"nombre": "VAN", "archivo": "<caso>/salida.json", "ruta": "indicadores.van", "valor": 0},
  "supuestos": [{"campo": "ingresos[0].ocupacion", "valor": 0.5, "origen": "SUPUESTO", "razon": "…", "fiabilidad": null}],
  "tol_abs": 0.01
}
```

`script` es relativo a la raíz del repo. `args` lleva `{SALIDA}` donde va la carpeta (o el archivo)
de salida: el ejecutor la reemplaza por `carpeta_salida` al correr; `recorrer.py manifiesto` la
reemplaza por la temporal y además verifica que `cifra_decisiva.valor` sea lo que dice la salida.

## Dónde está la cifra decisiva de cada método

| Método | Archivo | Ruta |
|---|---|---|
| adquisiciones | `<salida>.json` (junto al Excel) | `totales.neto`, `faltantes` |
| costo-y-precio | el de `--json` (sin `--json` no hay JSON: pásalo siempre) | `totales.venta_total`, `totales.margen_global` |
| evaluacion-economica | `salida.json` | `indicadores.van`, `sensibilidad.filas[0].critico` |
| evaluacion-financiera | `<caso>-resultado.json` | `ganadora`, `diferencia_vp`, `van_proyecto` |

## Cruces entre métodos encadenados

| Cadena | Debe coincidir |
|---|---|
| evaluacion-economica → evaluacion-financiera | `indicadores.van` = `van_proyecto`; `parametros.tasa.valor` = `tasa_descuento`; `parametros.impuesto.valor` = `impuesto_renta`; `parametros.horizonte.valor` = `horizonte_anios`; monto, vida útil y valor de desecho del activo en las dos entradas |
| adquisiciones → costo-y-precio | lo asignado a cada proveedor (cantidad, unidad, unitario, moneda y tipo de cambio) = las líneas de `compras` |

Un cruce que no coincide no es error si la diferencia está declarada en la salida (por ejemplo, un
escenario con otro impuesto que lo avise). Si solo la declara un resumen aparte, es un hallazgo.

## Errores típicos

| Síntoma | Causa |
|---|---|
| `FALTA · ningún argumento lleva {SALIDA}` | Falta `--salida "{SALIDA}"` (o `{SALIDA}/archivo.xlsx`). Es a propósito |
| `DISTINTO` solo en `barridos` o en la hoja `SENSIBILIDAD` | La salida archivada se corrió con otros `--barrer`: el comando no quedó registrado |
| `NO GENERADO` | El nombre que deja el script no es el del archivado (`--original ruta=nombre_nuevo`) |
| `SIN COMPARAR` en un `.xlsx` | Falta openpyxl; el JSON sí se compara |
