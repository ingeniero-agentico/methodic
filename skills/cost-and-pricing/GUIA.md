# Costo y precio · guía para una persona

Este método contesta dos preguntas que parecen una sola: **cuánto me costó** lo que vendo y
**a cuánto lo vendo**. Se recorre con un caso ficticio: la **Ferretería Andes** cotiza una red de
riego a la **Constructora Sur**. Todas las cifras de esta guía salen de
`python scripts/cost_pricing.py --test` (caso en `tests/sample-case.json`).

Todo es **neto**: el impuesto al valor agregado no es costo ni utilidad cuando la empresa
recupera el crédito fiscal, así que no entra en ninguna cuenta de margen.

## 1. Junta las líneas de compra tal como las escribió el proveedor

Una fila por línea de orden de compra (o de cotización adjudicada), **en la unidad y en la moneda
del proveedor**. Si la OC dice «7 tiras de 6 m a $21.900», eso se anota; no «42 m a $3.650». El
documento manda porque es lo que se va a facturar.

| Doc | Línea | Proveedor | Ítem de venta | Cant. | Unidad | Precio unit. | Moneda |
|---|---|---|---|---|---|---|---|
| OC-101 | 1 | Proveedor A | VAL-50 | 30 | un | 18.500 | CLP |
| OC-101 | 2 | Proveedor A | TEF-34 | 24 | un | 1.150 | CLP |
| OC-102 | 1 | Proveedor B | VAL-50 | 10 | un | 21,40 | USD |
| OC-103 | 1 | Proveedor C | TUB-110 | 7 | tira 6 m | 21.900 | CLP |
| OC-103 | 2 | Proveedor C | COD-110 | 12 | un | 3.450 | CLP |

La columna **ítem de venta** es la única decisión de criterio en este paso: dice a qué cosa
que se vende se carga cada compra. La válvula (VAL-50) se compró a dos proveedores, y cada uno la
describe distinto («Válvula bola bronce 2 pulg.» y «Ball valve bronze 2"»). Si la especificación
es la misma, van al mismo ítem. Si hay duda, se pregunta: unir dos productos distintos inventa un
costo que no existe.

## 2. Declara el tipo de cambio

La válvula del Proveedor B vino en dólares. El tipo de cambio **se declara** con fecha y fuente
(en el caso: 945,30 CLP por USD al 01-10-2026, dado por el usuario). Sin él, el script se detiene.
En moneda extranjera, siempre dos decimales: USD 21,40, no USD 21.

## 3. Costo ponderado: cuánto costó de verdad la unidad

La válvula costó 18.500 a un proveedor y 20.229,42 al otro (21,40 × 945,30). El costo real no es
el promedio de los dos precios: es el **promedio ponderado por cantidad**.

- Proveedor A: 30 un, $555.000.
- Proveedor B: 10 un, $202.294,20.
- Total $757.294,20 ÷ 40 un = **$18.932,36 por unidad**.

El promedio simple exagera al proveedor caro justo cuando se le compró poco, que es el caso
normal (al caro se le compra el saldo que el barato no tenía).

La hoja `TRAZABILIDAD` muestra el peso de cada línea en el ítem: la OC-101 explica el 73,3 % del
costo de la válvula.

## 4. Si se compró en la unidad del proveedor, lo que sobra también se paga

El tubo se vende por metro y se compra por tira de 6 m (`factor_unidad: 6`). Se instalan 40 m;
no se compran 6,67 tiras, se compran 7: **42 m, sobran 2 m**.

- Costo ponderado por metro comprado: $153.300 ÷ 42 = **$3.650**.
- Costo por metro **vendido**: $153.300 ÷ 40 = **$3.832,50**.

La diferencia es el costo del sobrante ($7.300), que llega a la obra y se paga igual. Si el
precio se calcula sobre $3.650, ese sobrante se regala.

## 5. Gastos generales: el costo que no está en ninguna OC

Arriendo, sueldos de administración, vehículo, contador: no se compran para un trabajo en
particular, pero los paga la venta. Aquí se cargan como una **fracción del costo directo**
(8 % en el caso). El metro de tubo pasa de $3.832,50 a **$4.139,10**.

Esto es **costeo por absorción** en su forma más simple: el indirecto se reparte en proporción
al costo directo. Funciona bien cuando todos los trabajos se parecen. Falla cuando un trabajo es
casi todo material caro y poca gestión (absorbe demasiado indirecto) o al revés. Ahí conviene
repartir por horas de trabajo o por actividad (ver `SOURCES.md`).

Si nadie declara los gastos generales, el script usa 0 % y lo marca `SUPUESTO`: un precio sin
gastos generales es un precio que no cubre la oficina.

## 6. Precio por recargo, y al lado el margen real

**Recargo** es lo que se suma **sobre el costo**. **Margen** es lo que queda **de la venta**.

```
precio       = costo × (1 + recargo)
margen real  = (precio − costo) ÷ precio
margen       = recargo ÷ (1 + recargo)        recargo = margen ÷ (1 − margen)
```

El tubo, con recargo 30 %: $4.139,10 × 1,30 → **$5.381** el metro (redondeado a pesos), con
**margen real de 23,1 %**. El codo lleva recargo propio de 40 %: precio $5.216, margen real 28,6 %.

Por qué se fija con recargo: es lo que se dice en voz alta («le puse un 30») y es lo que se
negocia. Por qué se muestra el margen: es lo que de verdad queda. El error clásico es escribir
30 en una planilla que calcula `costo ÷ (1 − 30 %)`: da ×1,43 y no ×1,30, un 10 % de sobreprecio
que nadie nota mirando el PDF.

**Precio manual.** Si el precio lo fija el mercado (la cinta teflón se vende a $1.990 en todas
partes), se escribe `precio_manual` y el script devuelve el recargo que eso significa: 60,2 % de
recargo, 37,6 % de margen real.

## 7. Lee el total

| | Caso Ferretería Andes |
|---|---:|
| Costo directo | $979.594,20 |
| Costo total (con gastos generales) | $1.057.961,74 |
| Venta | $1.388.832 |
| Utilidad | $330.870,26 |
| Recargo efectivo | 31,3 % |
| Margen real global | 23,8 % |

El recargo efectivo no es 30 % porque cada ítem tiene el suyo (el codo 40 %, la cinta 60,2 %).

## 8. Margen de contribución y punto de equilibrio de un servicio

La ferretería también vende **horas de instalación**: $28.000 la hora, con $12.500 de costo
variable por hora (técnico por hora, consumibles, traslado) y $1.860.000 de costos fijos al mes.

- **Margen de contribución** = precio − costo variable = **$15.500 por hora**. Es lo que cada
  hora aporta para pagar los fijos (razón de contribución 55,4 %).
- **Punto de equilibrio** = fijos ÷ margen de contribución = **120 horas al mes**
  ($3.360.000 en ventas). Bajo eso, se pierde.
- Con 160 horas esperadas, la utilidad es $620.000 y el **margen de seguridad** es 25 %: las
  ventas pueden caer un cuarto antes de perder.

## 9. Costeo variable y costeo por absorción

Las dos formas de costear dan **el mismo costo total del período**; lo que cambia es **cuándo**
se reconoce el costo fijo de producción.

- **Costeo variable**: el fijo de producción es gasto del mes, se venda o no lo producido. El
  producto solo carga su costo variable.
- **Costeo por absorción**: el fijo de producción se reparte entre las unidades producidas. Lo
  que queda en bodega se lleva su parte del fijo, y ese fijo recién es gasto cuando se vende.

El caso trae un **kit de riego armado**: se producen 500, se venden 400, precio $45.000,
variable $27.000, fijos de producción $900.000 y de operación $360.000.

| | Variable | Absorción |
|---|---:|---:|
| Costo unitario del kit | $27.000 | $28.800 |
| Utilidad del mes | $5.940.000 | $6.120.000 |
| Inventario final (100 kits) | $2.700.000 | $2.880.000 |

La diferencia de utilidad, $180.000, es exactamente el fijo de producción que quedó en los 100
kits de bodega. Por eso la absorción puede **inflar la utilidad produciendo de más**, y por eso
para decidir precios y volúmenes de corto plazo se mira el margen de contribución.

En un **servicio** no hay inventario (una hora de instalación no se guarda): las dos utilidades
coinciden y la discusión se reduce al punto de equilibrio.

## 10. Antes de entregar

1. Lee la hoja `SUPUESTOS`: lo que está en naranjo no vino de nadie.
2. Revisa los avisos: sobrantes, diferencias grandes entre proveedores, tipo de cambio sin fuente.
3. El libro tiene costos y proveedores: **no sale de la empresa**. Al cliente va solo el precio.
