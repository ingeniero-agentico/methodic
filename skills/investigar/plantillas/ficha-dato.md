# Ficha de un dato

Cada dato de `datos-investigados.json` es un objeto con estos campos. El validador
(`scripts/validar_investigacion.py`) exige los obligatorios.

| Campo | Obligatorio | Qué va |
|---|---|---|
| `id` | sí | único en la investigación (`D01`, `D02`…) |
| `hueco` | sí | id del hueco al que responde (`H1`…) |
| `descripcion` | sí | qué es, en una línea, con el segmento exacto (plazo, tramo, región) |
| `magnitud` | sí | qué mide, en una clave corta (`tasa_leasing`, `arancel_inscripcion`). Dos datos con la misma magnitud y unidad se comparan entre sí |
| `valor` | sí | número, o texto si el dato es cualitativo («opción de compra = una renta»); `null` solo si `estado` es `no_encontrado` |
| `rango` | no | `[mínimo, máximo]` cuando la fuente da un rango; si `valor` es número, cae dentro |
| `unidad` | sí | `% mensual`, `% anual lineal`, `CLP`, `UF`, `fracción del precio`… |
| `fecha_dato` | sí | `DD-MM-AAAA`: a qué fecha corresponde el valor (vigencia, publicación, mes medido) o `sin_fecha` |
| `fuente` | sí, salvo `calculado` | `{"url": "https://…"}` y/o `{"documento": "nombre, número, fecha, punto"}` |
| `fecha_consulta` | sí | `DD-MM-AAAA`: cuándo se leyó |
| `nivel` | sí | `A` norma, ley, organismo oficial, documento del cliente · `B` libro, artículo, manual del fabricante · `C` proveedor, cotización, prensa especializada · `D` blog, foro, IA sin fuente |
| `estado` | sí | `verificado` (leído en el original) · `por_confirmar` (leído en un resumen o agregador) · `calculado` (sale de `formula`) · `no_encontrado` (se buscó y no está) |
| `usable` | sí | `true` si puede entrar a un cálculo |
| `supuesto` | sí | `true` si entra como SUPUESTO. Obligatorio para un D o un `por_confirmar` usable |
| `formula` | si es `calculado` | aritmética con ids de otros datos: `D01 / 12`, `D22 * (1 - D23)` |
| `tolerancia` | no | tolerancia relativa del recálculo (por defecto 0,001) |
| `tipo` | no | `norma` para leyes, decretos y aranceles vigentes: no envejecen por fecha ni piden segunda fuente |
| `nota` | no | lo que cambia la lectura del dato (qué no mide, por qué no se abrió) |

## Ejemplo

```json
{"id": "D01", "hueco": "H1", "descripcion": "Tasa de leasing cotizada por Proveedor A, 36 meses",
 "magnitud": "tasa_leasing", "valor": 1.45, "unidad": "% mensual", "fecha_dato": "10-03-2030",
 "fuente": {"documento": "cotización Proveedor A N° 101, punto 3"}, "fecha_consulta": "12-03-2030",
 "nivel": "C", "estado": "verificado", "usable": true, "supuesto": false}
```

## Reglas que el validador hace cumplir

1. Un D o un `por_confirmar` usable va con `supuesto: true`.
2. Un `calculado` no tiene nivel mejor que su peor insumo y hereda el SUPUESTO de sus insumos.
3. Dos datos de la misma magnitud y unidad que difieren más del umbral van juntos en
   `contradicciones`, con el que manda y la razón.
