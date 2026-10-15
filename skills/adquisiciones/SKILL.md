---
name: adquisiciones
description: Use when several supplier quotes for the same purchase must be turned into a purchase decision — comparing prices line by line, deciding who gets which items when each supplier covers only part of the quantity, flagging what nobody quoted, or checking that a quote's lines add up to its printed subtotal before trusting it. Also when a supplier prints list prices and applies the discount only on the line total, when items are sold in whole units of the supplier (pipe in 6 m lengths, boxes of 10) and the order must speak that unit, when a quote is in a foreign currency, or when a comparison produced numbers nobody can trace back to a quote. Compara cotizaciones y reparte la compra en cascada entre proveedores, con cada número trazado a su cotización y línea.
---

# Adquisiciones · comparar cotizaciones y asignar la compra

**No gana el más barato: gana el reparto.** Los proveedores cotizan cantidades parciales. Al de
menor unitario se le compra lo que tiene, el saldo pasa al siguiente y lo que nadie cubre queda
**POR COTIZAR**. Exigir que uno solo cubra todo manda líneas completas al caro por dos unidades
que faltaban.

El agente pone el criterio (qué línea de cada cotización corresponde a qué ítem pedido, y si la
especificación calza). El script hace todo el cálculo: cuadratura, unitario efectivo, conversión
de moneda, reparto, totales y el libro Excel.

```bash
python scripts/adquisiciones.py entrada.json --salida ADQUISICIONES.xlsx [--perfil perfil.yaml] [--empresa nombre]
python scripts/adquisiciones.py --probar      # el caso ficticio tiene que terminar en OK
```

Entrada vacía: `plantillas/entrada.json` (trae la ayuda de cada campo en `_ayuda`).

## Cuándo usarla

- Llegaron dos o más cotizaciones para la misma compra y hay que decidir a quién comprar qué.
- Un proveedor parece ganar por lejos y hay que confirmar que es el mismo producto.
- Alguien preguntó «¿de dónde sale este precio?» y la comparativa no lo dice.

Requiere las cotizaciones ya leídas. **Esta versión no lee PDF ni emite órdenes de compra**: la
extracción y la emisión son pasos manuales descritos en `GUIA.md` (pasos 1 y 6).

## El perfil manda

El script lee del perfil de la empresa: `empresa.moneda`, `empresa.decimales_moneda`,
`empresa.iva` y `compras.desempate`. Lo busca en este orden:

1. `--perfil <ruta>`.
2. La variable de entorno `INGENIERO_DATOS` (un archivo, o una carpeta con `perfiles/`).
3. La carpeta hermana del repo, `../ingeniero-agentico-datos/perfiles/`. Si hay varios perfiles,
   se elige con `--empresa`.
4. Si no hay ninguno, `perfiles/_plantilla.yaml`, y **todo lo que sale de ahí queda marcado
   `SUPUESTO`**.

Un perfil real sin `moneda` o sin `iva` hace abortar: se pregunta, no se inventa.

## Lo que decide el agente (antes de correr)

1. **Emparejar cada línea con su ítem** (`item` = el `n` del requerimiento). Cada proveedor nombra
   distinto el mismo producto. **Verifica la especificación antes que el precio: un ítem 4× más
   barato casi siempre es otro producto** (otra presión, otra medida, otro tipo de unión, otro
   material).
2. **Descartar lo que no calza**, con `descarte: "<motivo>"` en la línea. Nunca borres la línea ni
   la dejes «para referencia»: borrada no se distingue de un olvido, y sin `descarte` compite y
   gana. El script la saca del reparto y la lista en VERIFICACION.
3. **La unidad del proveedor.** Si vende tiras, barras o cajas, la `cantidad` va en esa unidad y
   `unidad_venta.contenido` dice cuánto del ítem trae cada una (6 m por tira). Copia en `textual`
   el texto del documento: es la prueba de dónde salió el número.
4. **Lo disponible.** Si el proveedor declaró que entrega menos de lo cotizado, va en `disponible`.
   Si no lo declaró, se asume lo cotizado y queda `SUPUESTO`. **Si no cotizó un ítem, no pongas la
   línea: nunca cargues 0.**
5. **La moneda.** Si no es la del perfil, `tipo_cambio` y `fecha_cambio` son obligatorios. El
   cambio lo pone quien paga (el que cobra su banco), nunca el de una página web.

## Lo que calcula el script

| Paso | Regla |
|---|---|
| Cuadratura | Las líneas de cada cotización suman su `subtotal_impreso`. Si no, **aborta**: falta una línea, sobra una o un total está mal copiado |
| Unitario | `total_linea ÷ (cantidad × contenido)`. **Nunca el impreso**: hay quien imprime lista y descuenta solo en el total. Las líneas con impreso ≠ efectivo se listan |
| Moneda | Se convierte con el `tipo_cambio` declarado; la traza guarda el original |
| Reparto | Cascada por unitario. Empate: `compras.desempate` del perfil (`mayor_disponibilidad` = menos órdenes; `menor_plazo`) |
| Unidad entera | Se compra en la unidad del proveedor, redondeando hacia arriba sin pasar lo disponible. **Lo que sobra se paga** y queda declarado |
| Contraoferta | Mismo ítem, mismo proveedor y vendedor en dos cotizaciones: la de `fecha` más nueva reemplaza a la vieja. Sin fechas distintas, aborta |

## Cómo se lee la salida

El libro trae cinco hojas y un JSON con lo mismo:

| Hoja | Qué contesta |
|---|---|
| `RESUMEN` | total neto, IVA y total; cuánto va a cada proveedor; lo que falta; los supuestos |
| `ASIGNACION` | qué se compra a quién, en qué unidad y a cuánto. **Cada fila trae su traza**: cotización, línea y la división que dio el unitario. Amarillo = ítem partido |
| `COMPARATIVA` | el unitario efectivo de cada proveedor por ítem, con mejor, peor y diferencia |
| `PROVEEDORES` | cada cotización: moneda, cambio, suma de líneas contra subtotal impreso, monto asignado |
| `VERIFICACION` | cuadratura de cantidades, descartes, impreso ≠ efectivo, contraofertas, líneas sin ítem (fletes), supuestos y avisos. **Se lee antes de emitir** |

## Revisar antes de emitir

El script reparte por precio. Esto lo decide una persona:

- **Saldos partidos.** Si el barato cubre 25 de 40, pedirle el saldo al mismo precio suele ganar
  más que mandar 15 al caro.
- **Lo que falta.** Cotizarlo afuera o cambiar la especificación.
- **Cotizaciones por vencer.** El reparto asume precios vigentes.
- **Líneas sin ítem** (flete, embalaje). No entran al reparto; un flete incluido no es un descuento.
- **Una orden chica no es un problema en sí.** No descartes a un proveedor por pocas unidades salvo
  que el usuario declare un costo de gestión.

## Errores típicos

| Síntoma | Causa |
|---|---|
| Un proveedor sale el doble de caro que todos | Se leyó su unitario de lista (el script usa el efectivo; revisar que `total_linea` sea el cobrado) |
| Un proveedor sale ~900 veces más barato | Cotiza en otra moneda y la cotización no declara `moneda` |
| Gana algo que no puede entregar | Falta `disponible` |
| Gana algo que no cotizó | Se cargó una línea en 0 en vez de omitirla |
| Gana por lejos en un ítem | Es otra especificación: va con `descarte` |
| «NO CUADRA» | Falta una línea en la extracción. **No seguir hasta encontrarla** |
| Sobra material en la obra | Es correcto: se compra en la unidad del proveedor y la sobra se declara |
