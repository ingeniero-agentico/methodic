# Adquisiciones · guía paso a paso

El mismo método de `SKILL.md`, para una persona. Se recorre con el caso ficticio de
`tests/sample-case.json`: **Constructora Sur** necesita seis ítems para la red de agua de una
faena y le llegaron tres cotizaciones (Proveedor A, B y C).

**Qué hace el script y qué no.** Esta primera versión **compara y asigna**. Dos pasos quedan fuera
del script y se hacen a mano: **leer las cotizaciones** (paso 1) y **emitir las órdenes de compra**
(paso 6). Están descritos acá para que el método quede completo.

## 0 · El perfil de la empresa

Copia `profiles/_template.yaml` a `ingeniero-agentico-datos/profiles/<empresa>.yaml` y llena al
menos `moneda`, `decimales_moneda`, `iva` y `compras.desempate`. Sin perfil, el script usa la
plantilla y marca todo como `SUPUESTO`: sirve para probar, no para comprar.

## 1 · Leer cada cotización (fuera del script)

Por cada documento, transcribe **todas** sus líneas a la entrada (`templates/input.json`):

| Campo | Qué va |
|---|---|
| `linea` | el número que le da el proveedor en su documento |
| `cantidad` | en la unidad en que él vende |
| `total_linea` | lo que cobra por la línea, ya con descuento |
| `unitario_impreso` | lo que imprime como unitario (solo referencia) |
| `subtotal_impreso` | el subtotal neto del documento, una vez por cotización |

Tres cosas que se escapan:

- **La línea que aparece dos veces se transcribe dos veces.** Pasa cuando el producto venía en dos
  partidas. Si lees solo la primera, el proveedor parece cubrir menos de lo que cubre.
- **El flete y lo no pedido también se transcriben**, con `item: null`. Sin ellos la suma no da el
  subtotal impreso.
- **La unidad de venta se copia textual.** «x 6 Mts» o «tira 5.8 mts» va en
  `unidad_venta.textual`; es lo que después permite descubrir que un proveedor vende tiras más
  cortas que el resto.

En el caso: Proveedor B imprime el codo a **4.000** pero la línea cobra **112.000 por 40**. El
unitario que vale es 2.800. Leído el impreso, B parecía el más caro; es el más barato.

## 2 · Emparejar y descartar

Para cada línea, escribe en `item` el número del requerimiento al que corresponde. Antes del
precio, la especificación: medida, presión, material, tipo de unión. **Un ítem mucho más barato
casi siempre es otro producto.**

En el caso: se piden manómetros de **4"**; Proveedor B cotiza uno de **2,5"**. La línea se queda
en la entrada con `descarte: "Esfera de 2,5\"; se pide 4\"."`. Así no compite, y el motivo queda
escrito.

## 3 · Correr

```bash
python scripts/procurement.py entrada.json --out ADQUISICIONES.xlsx --profile <perfil.yaml>
```

Si una cotización no cuadra con su subtotal impreso, el script se detiene y dice cuál. Vuelve al
paso 1: falta una línea, sobra una o un total está mal copiado.

## 4 · Leer el reparto

Lo que sale para Constructora Sur (todo calculado por el script; ver `tests/expected.json`):

| Ítem | Qué pasó |
|---|---|
| 1 · Cañería 2", 104 m | B la vende a 9.500 el metro en tiras de 5,8 m y tiene 10 tiras (58 m). El saldo de 46 m va a A, a 10.000 el metro en tiras de 6 m: **8 tiras = 48 m, sobran 2 m** (se pagan) |
| 2 · Codo 2", 40 un | B (2.800) tiene 30; los 10 que faltan van a A (3.000). C (3.200) no entra |
| 3 · Válvula 1", 12 un | B a 8.400 contra A a 8.500 |
| 4 · Copla 2", 60 un | A a 2.000 contra C a 2.100 |
| 5 · Manómetro 4", 4 un | **POR COTIZAR**: la única oferta estaba descartada |
| 6 · Tapa 2", 10 un | A y C empatan a 1.500. Gana C porque tiene 10 y A solo 6 (desempate por mayor disponibilidad: una orden menos) |

Total neto 1.380.800; con IVA de la plantilla, 1.643.152. Tres órdenes: B 735.800, A 630.000,
C 15.000. El despacho de C (25.000) no entra al reparto: aparece en VERIFICACION como línea sin
ítem, para decidirlo aparte.

Cada fila de `ASIGNACION` dice de dónde salió su unitario, por ejemplo
`B-202 línea 4: 551.000 CLP ÷ 58 (10 × 5,8) = 9.500,00 por m`.

## 5 · Revisar antes de emitir

Lee `VERIFICACION` completa. Después, las decisiones que son de una persona:

- **Ítem 2 partido.** A B le faltaron 10 codos. Pedirle esos 10 al mismo precio ahorra la
  diferencia de unitario sobre esas 10 unidades y una línea en la orden de A (si se consigue, se
  corrige `disponible` y se vuelve a correr: el número lo da el script).
- **Ítem 5 sin cubrir.** Cotizar afuera, o confirmar si el de 2,5" sirve (eso es cambiar la
  especificación, no el precio).
- **Ítem 1 con sobra.** Los 2 m de más llegan a la obra y se pagan. Si importa, se pide a A que
  corte o se acepta.
- **Vencimiento.** B vence en 7 días: su orden va primero.

## 6 · Emitir las órdenes de compra (fuera del script)

Una orden por proveedor, con lo que dice `ASIGNACION`:

- **En la unidad del proveedor.** A A se le piden 8 tiras de 6 m, no 48 m. Si la orden va en
  metros, él factura tiras y la diferencia aparece después.
- **En la moneda del proveedor.** Si cotizó en otra moneda, la orden va en esa; el valor convertido
  es solo para comparar.
- **Con su identificador tributario.** Sin él no se emite: `PROVEEDORES` lo marca como FALTA.

Antes de mandarlas, alguien que no las armó compara cada línea de cada orden contra la cotización
original.

## Errores que el método ataja

| Error | Dónde se ataja |
|---|---|
| Línea olvidada al transcribir | cuadratura contra el subtotal impreso (aborta) |
| Unitario de lista tomado como precio | se deriva del total; VERIFICACION lista los impresos distintos |
| Otra moneda tomada como local | sin `tipo_cambio`, aborta |
| Medio tubo en la orden | se compra en unidades enteras del proveedor |
| Una oferta descartada que igual gana | `descarte` la saca del reparto |
| El hueco que nadie ve | POR COTIZAR en RESUMEN, ASIGNACION y VERIFICACION |
