---
name: costo-y-precio
description: Use when the real cost of what a company sells must be known before pricing it (an item bought split across several suppliers needing a weighted average cost, bought in the supplier's unit such as pipe lengths, rolls or boxes and sold by the meter so the leftover must be carried into the unit cost, bought in a foreign currency, or loaded with overhead), and when setting sale prices by markup on cost while showing the real margin on sales, or computing contribution margin and break-even for a service or product (variable vs absorption costing). Also when someone says "¿cuánto nos costó?", "¿a cuánto lo vendo?", "le puse un 30", "¿cuánto margen es eso?", "¿cuántas horas tengo que vender para cubrir los fijos?". Calcula el costo real por ítem desde las órdenes de compra, el precio por recargo con su margen real y el punto de equilibrio.
---

# Costo y precio

**Qué resuelve.** Cuánto costó de verdad cada ítem de un trabajo y a cuánto venderlo, con cada
número trazado hasta la línea de la orden de compra de la que salió.

**Regla de los nombres, que no se negocia.** El precio se fija con **RECARGO sobre el costo**
(0,30 = costo × 1,30). Al lado se muestra el **MARGEN REAL sobre la venta**
((precio − costo) ÷ precio). Un 30 % de recargo es un 23,1 % de margen. Nunca se usa una
palabra por la otra: escribir «30» en una columna que calcula costo ÷ (1 − 0,30) da ×1,43 en vez
de ×1,30, un 10 % de sobreprecio sin ningún aviso.

## Cuándo

- Un trabajo ya tiene órdenes de compra (o cotizaciones adjudicadas) y hay que cotizar al cliente.
- Un ítem se compró partido entre proveedores y nadie sabe cuánto costó la unidad.
- Se compró en tiras, rollos o cajas y se vende por metro o unidad: sobra material.
- Una compra vino en moneda extranjera.
- Hay que saber cuánto vender de un servicio para cubrir los costos fijos del mes.

## Qué decides tú (el agente) y qué calcula el script

| Decides tú | Calcula `scripts/costo_precio.py` |
|---|---|
| Qué línea de compra va a qué ítem de venta (`item`) | Costo directo por ítem, ponderado por cantidad |
| El factor de unidad (tira de 6 m vendida por metro = 6) | Sobrante y costo por unidad **vendida** |
| Si dos descripciones de proveedores son el mismo producto | Conversión de moneda con el tipo de cambio declarado |
| El tipo de cambio, con fecha y fuente (lo da el usuario) | Gastos generales sobre el costo directo |
| Recargo por ítem o global; precio manual si el usuario lo fija | Precio, margen real, recargo efectivo, utilidad |
| Costos fijos y variables de un servicio | Margen de contribución, punto de equilibrio, variable vs absorción |

**No propongas un recargo parejo** si el usuario no lo pidió: hay ítems que aguantan más que
otros. Si el perfil trae `recargo_por_defecto`, úsalo como punto de partida y dilo.

**Dos descripciones distintas pueden ser el mismo producto** (cada proveedor escribe a su
manera). Si los números de la especificación coinciden, pregunta antes de unirlas en un solo
`item`: unir dos productos distintos inventa un costo promedio que no existe.

## Cómo se corre

```
python scripts/costo_precio.py <caso.json> --perfil <empresa> --salida costo.xlsx [--json resumen.json]
python scripts/costo_precio.py --probar
```

La entrada es un JSON con la forma de `plantillas/caso.json`: `compras` (una fila por línea de
OC, en la unidad y moneda del proveedor), `items` (lo que se vende), `tipos_de_cambio`,
y opcional `equilibrio`.

**El perfil** se busca así: `--perfil` (ruta o nombre) · campo `perfil` del caso ·
`$INGENIERO_DATOS/perfiles/<nombre>.yaml` · `../ingeniero-agentico-datos/perfiles/<nombre>.yaml` ·
y si no hay nombre, `perfiles/_plantilla.yaml` (todo queda marcado `SUPUESTO`). Del perfil se leen
`empresa.moneda`, `empresa.decimales_moneda`, `precios.recargo_por_defecto` y
`precios.gastos_generales`. El caso puede pisar los dos últimos.

## Qué calcula, en orden

1. **Costo de cada línea** en moneda local: cantidad × precio unitario × tipo de cambio.
2. **Costo ponderado** del ítem: Σ costos ÷ Σ unidades compradas (en unidad de venta). Ponderado,
   no simple: 100 un a $1.000 y 2 un a $2.000 cuestan $1.019,61 la unidad, no $1.500.
3. **Costo directo por unidad vendida**: Σ costos ÷ unidades vendidas. Si se compraron 7 tiras de
   6 m (42 m) y se instalan 40 m, los 2 m que sobran se pagan igual y van en el costo del metro.
4. **Costo total por unidad** = costo directo × (1 + gastos generales).
5. **Precio** = costo total × (1 + recargo), redondeado a los decimales de la moneda (mitad hacia
   arriba, como `ROUND` de una planilla). Con `precio_manual`, manda ese precio y el recargo real
   se recalcula.
6. **Margen real** = (precio − costo total) ÷ precio, neto contra neto.
7. **Equilibrio**: margen de contribución = precio − costo variable; punto de equilibrio =
   costos fijos ÷ margen de contribución. Con unidades producidas y vendidas, utilidad por costeo
   variable y por absorción, y la diferencia (el fijo que quedó en el inventario).

## Cómo se lee la salida

Excel con cuatro hojas (la tercera solo si hay `equilibrio`):

| Hoja | Qué |
|---|---|
| `COSTO Y PRECIO` | Un ítem por fila: cantidad vendida y comprada, sobrante, costo ponderado, costo por unidad vendida, gastos generales, recargo y su origen, precio, margen real, venta, utilidad y los `doc:línea` de donde vino. Al pie, recargo efectivo y margen real global. Fondo azul: comprado a más de un proveedor |
| `TRAZABILIDAD` | Una fila por línea de compra: documento, línea, proveedor, unidad del proveedor, factor, precio original, moneda, tipo de cambio, total local y su peso en el ítem |
| `EQUILIBRIO` | Margen de contribución, punto de equilibrio en unidades y en ventas, margen de seguridad, y variable vs absorción |
| `SUPUESTOS` | Cada parámetro con su origen (caso, perfil o `SUPUESTO`) y los avisos. Naranjo = `SUPUESTO` |

Antes de entregar, **lee los avisos** en voz alta al usuario: gastos generales supuestos,
sobrantes, tipo de cambio sin fuente, diferencias grandes de costo entre proveedores.

El libro lleva costos y proveedores: **no se le manda al cliente**. Al cliente va solo el precio.

## Errores típicos

| Síntoma | Causa |
|---|---|
| `la compra no cubre la venta` | `cantidad_venta` mayor que lo comprado: falta una OC o el factor de unidad está mal |
| `no declara tipo de cambio USD` | Hay una línea en otra moneda: pide el tipo de cambio con fecha y fuente, no lo supongas |
| El precio sale 43 % sobre el costo cuando pidieron 30 | Alguien trató el 30 como margen. Aquí el campo es `recargo` |
| El costo por metro es mayor que el de la tira ÷ 6 | Correcto si sobra material: el sobrante se carga a lo vendido |
| Un ítem aparece dos veces con costos distintos | Dos proveedores lo describen distinto. Si es el mismo producto, un solo `item` |
| Gastos generales en naranjo | No vinieron del usuario ni del perfil: se usó 0 %. Pregúntalos |
| Margen real global distinto del recargo pedido | Normal: margen y recargo son cosas distintas, y el redondeo del precio mueve décimas |

## Archivos

`GUIA.md` (el método para una persona, con el caso ficticio) · `plantillas/caso.json` ·
`pruebas/` (Ferretería Andes + `esperado.json`) · `fuentes.md`.
