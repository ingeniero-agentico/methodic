# Guía · evaluación financiera

Cómo decidir si un activo se paga al contado, con crédito, con leasing o se arrienda, paso a paso,
con el caso ficticio de `tests/`.

> Es un método de cálculo, no asesoría financiera personalizada.

## La pregunta

**Transportes del Valle** (empresa ficticia) necesita un furgón de $24.000.000 neto. Ya sabe que el
furgón se paga solo (su flujo del proyecto puro da VAN $5.291.023 al 12 %). Ahora la pregunta es
otra: **¿cómo lo paga?**

| Alternativa | Condiciones |
|---|---|
| Contado | $24.000.000 hoy |
| Crédito 36 cuotas | pie 20 %, 1,5 % mensual, cuota francesa, $250.000 de gastos, seguro $8.000 al mes, impuesto de timbres 0,066 % por mes con tope 0,8 % |
| Crédito 36 cuotas (alemana) | lo mismo con amortización fija |
| Leasing 36 cuotas | 1,3 % mensual, cuota inicial y opción de compra iguales a una cuota |
| Arriendo 60 meses | $620.000 al mes, garantía de una renta; incluye mantención y seguro |

Perfil: impuesto 27 %, tasa de descuento 12 %, horizonte 5 años, depreciación lineal en 7 años.
Valor de venta del furgón al año 5: $9.000.000 (SUPUESTO).

## Paso 1 · Separar el proyecto del financiamiento

El proyecto (¿conviene el furgón?) se evalúa sin deuda: es `economic-evaluation`. Este método parte
de ese flujo y solo agrega lo que cambia con cada forma de pagar. El puente es un archivo
(`tests/sample-project-flow.csv`, columnas `year,flow`), no cifras copiadas.

## Paso 2 · Normalizar las ofertas

Antes de comparar, todas deben hablar del mismo activo, el mismo plazo de uso y el mismo valor al
final. Lo que no se puede igualar se declara: el arriendo incluye mantención y seguro; las demás no.
Ese dato no se promedia, se escribe al lado del resultado.

## Paso 3 · La tabla de amortización

**Cuota francesa** (cuota fija): C = L · i / (1 − (1 + i)^−n). Con L = $19.200.000, i = 1,5 % y
n = 36, la cuota es **$694.126**. Cada mes el interés es saldo × i y lo que sobra de la cuota
amortiza. **Cuota alemana**: la amortización es fija (L / n) y la cuota baja mes a mes; parte en
$821.333.

La tabla tiene que cuadrar: la suma de las amortizaciones es exactamente el monto prestado, y la
cuota de la fórmula es la de la tabla. La última cuota absorbe el redondeo al peso.

**CAE**: la tasa que iguala lo que de verdad llega al deudor (monto − gastos − impuesto al crédito)
con todo lo que paga (cuotas + seguro), mensual × 12. Aquí es **20,37 %**, aunque la tasa pactada
sea 1,5 % × 12 = 18 %. La CAE es lo que se compara entre créditos, no la tasa.

**Leasing**: el precio se iguala a cuota inicial + 36 cuotas + opción de compra en el mes 37,
descontadas a la tasa del leasing. Cuota: **$794.063**.

## Paso 4 · El efecto tributario

Cada alternativa rebaja impuestos de forma distinta:

- **Contado**: depreciación del furgón ($24.000.000 / 7 por año).
- **Crédito**: depreciación + intereses + gastos + seguro. El capital no rebaja.
- **Leasing** (regla chilena): la cuota inicial y todas las cuotas son gasto; el furgón se activa al
  ejercer la opción, por el valor de la opción, y se deprecia desde ahí.
- **Arriendo**: la renta es gasto; no hay activo ni valor de venta.

Al vender al final, se paga impuesto sobre la diferencia entre el precio de venta y el valor libro.
En el leasing el valor libro es casi cero (la opción), así que paga más impuesto al vender.

## Paso 5 · El flujo del inversionista

Flujo del inversionista = flujo del proyecto + (flujo del activo con la alternativa − flujo del
activo al contado).

Para el crédito, eso es lo mismo que el esquema clásico: proyecto + préstamo − cuotas + ahorro
tributario de los intereses. Restar el contado evita contar la compra dos veces, porque el flujo
del proyecto ya trae la inversión.

## Paso 6 · Comparar y decidir

| Posición | Alternativa | Costo en VP después de impuesto | Costo efectivo después de impuesto | VAN del inversionista |
|---|---|---|---|---|
| 1 | Leasing 36 cuotas | $15.250.911 | 10,22 % | $5.924.574 |
| 2 | Contado | $15.884.462 | | $5.291.023 |
| 3 | Crédito 36 cuotas (alemana) | $16.905.972 | 16,55 % | $4.269.514 |
| 4 | Crédito 36 cuotas | $16.948.620 | 16,38 % | $4.226.865 |
| 5 | Arriendo 60 meses | $21.291.354 | 21,53 % | $−115.868 |

Cómo se lee:

1. **Gana el leasing por $633.551 en valor presente** frente al contado.
2. **El costo efectivo después de impuesto** del leasing (10,22 %) es menor que la tasa de descuento
   (12 %): financiarse así le cuesta menos que lo que rinde su propia plata. El crédito (16,38 %)
   cuesta más que el 12 %, por eso pierde contra el contado.
3. **Entre los dos créditos**, la cuota alemana sale más barata: como la deuda cuesta más que la
   tasa de descuento, conviene devolverla antes.
4. **La tasa que cambia la decisión es 10,22 %**: si la plata de la empresa rinde menos que eso, el
   contado gana. La sensibilidad lo confirma: al 9 % gana el contado, y con impuesto 0 % también
   (sin escudo tributario el leasing pierde su ventaja).
5. **El arriendo** es el más caro, pero incluye mantención y seguro: antes de descartarlo hay que
   restar lo que cuestan esos servicios en las otras alternativas.

## La tasa de descuento: WACC y CAPM (referencia)

Una pyme puede usar su **costo de oportunidad**: lo que rinde su plata en la mejor alternativa real.
Las dos herramientas clásicas son estas, y sirven de referencia, no son obligatorias:

- **WACC** (costo promedio ponderado del capital):
  WACC = E/(D+E) · kₑ + D/(D+E) · k_d · (1 − t). Pondera lo que exigen los dueños (kₑ) y lo que
  cuesta la deuda después de impuesto. Sirve para descontar el flujo del proyecto cuando la
  empresa mantiene una mezcla estable de deuda y capital.
- **CAPM** (modelo de valoración de activos de capital): kₑ = r_f + β · (r_m − r_f). La rentabilidad
  que exige el dueño es la tasa libre de riesgo más una prima por el riesgo sistemático (β). En una
  pyme sin acciones transadas no hay β propio: se toma el de empresas comparables del rubro,
  desapalancado y vuelto a apalancar con la deuda de la pyme, y se agrega una prima por tamaño y
  liquidez. Por eso, en una pyme, es una referencia y no un cálculo exigible.

El script recibe una sola tasa (la del perfil o `--rate`) y entrega la tasa de indiferencia, para
que la discusión sea «¿la plata del dueño rinde más o menos que X %?».

## Correr el caso

```
python scripts/financial_evaluation.py --test
python scripts/financial_evaluation.py --case tests/sample-case.json --profile tests/sample-profile.yaml
```

`--test` compara con `tests/expected.json` y revisa por un segundo camino que la cuota de la
fórmula de anualidad sea la de la tabla, que las amortizaciones sumen el monto al peso y que el VAN
del inversionista sea el VAN del proyecto más la ventaja frente al contado. `expected.json` se
verificó con `tests/second_path.py`, que recalcula todo con fórmulas cerradas (anualidades,
saldo por fórmula, escudos anuales) sin usar el script: la mayor diferencia es de 6 pesos, por
redondear cuotas e intereses al peso.
