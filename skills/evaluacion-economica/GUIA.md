# Guía · evaluación económica de un proyecto

Para una persona que quiere saber si un proyecto conviene, paso a paso, con el caso ficticio de
`pruebas/`: **Transportes del Valle** evalúa comprar un furgón para arrendarlo por día.

La pregunta de este método es una sola: **¿el negocio conviene por sí mismo?** Se evalúa como si
la empresa lo pagara entero con plata propia (el «proyecto puro»). Si después hay que decidir cómo
pagarlo (crédito, leasing, contado), eso es otro método: ver `evaluacion-financiera`, que parte
del flujo que sale de aquí.

## 1. Delimitar qué cambia

Anota solo lo que aparece o desaparece **si se hace** el proyecto. Para el furgón:

| Cambia | No cambia (no entra) |
|---|---|
| ingreso por arriendo, lavado, seguro, mantención, permiso, GPS | sueldo del dueño, oficina, contador |

Decide también si los montos van **netos de IVA** (la empresa recupera el IVA) y si están en
**pesos de hoy** (entonces la tasa es real). Transportes del Valle: netos y en pesos de hoy.

## 2. Juntar los números y marcar los supuestos

| Concepto | Valor | ¿De dónde? |
|---|---|---|
| Tarifa | $45.000 por día | competencia |
| Días disponibles | 360 al año | calendario |
| Ocupación | 55 % (198 días) | **SUPUESTO** de la gerencia |
| Lavado y desgaste | $6.000 por día arrendado | **SUPUESTO** del taller |
| Seguro · mantención · permiso · GPS | $900.000 · $600.000 · $250.000 · $180.000 al año | cotizaciones |
| Furgón | $18.000.000, vida útil tributaria 7 años | precio de lista |
| Equipo GPS | $160.000, vida útil 3 años | cotización |
| Valor de desecho del furgón al año 5 | $7.000.000 | **SUPUESTO** (avisos de usados) |
| Capital de trabajo | $1.000.000 | **SUPUESTO** |
| Tasa · impuesto · horizonte | 12 % · 27 % · 5 años | perfil de la empresa |

Todo lo que no viene de un documento se escribe igual, pero **marcado como supuesto y con su
razón**. La sensibilidad dirá después cuáles importan.

## 3. Armar el flujo de caja (año 1)

```
  Ingresos            45.000 × 198            8.910.000
− Costos variables     6.000 × 198           −1.188.000
− Costos fijos                               −1.930.000
− Depreciación   18.000.000/7 + 160.000/3    −2.624.762
= Utilidad antes de impuesto                  3.167.238
− Impuesto (27 %)                              −855.154
= Utilidad neta                               2.312.084
+ Depreciación (no sale de la caja)           2.624.762
= Flujo del año 1                             4.936.846
```

La depreciación se resta para pagar menos impuesto y se suma de vuelta porque no es plata que
salga. El año 0 es la inversión: −18.000.000 − 160.000 − 1.000.000 = **−19.160.000**.

El año 5 suma tres cosas más: la venta del furgón ($7.000.000) menos su valor libro
($18.000.000 − 5 × 2.571.429 = $5.142.857) paga impuesto sobre la ganancia; el valor libro se
suma de vuelta, y se recupera el capital de trabajo. Flujo del año 5: **12.421.017**.

## 4. Calcular los indicadores

| Indicador | Resultado | Lectura |
|---|---|---|
| VAN al 12 % | **$2.873.792** | conviene: deja $2,9 millones de hoy por sobre el 12 % exigido |
| TIR | 17,08 % | rentabilidad propia del proyecto; el flujo cambia de signo una vez, así que es única |
| Recuperación | 3,88 años (4,59 descontado) | se recupera dentro del horizonte |
| IVAN | 0,150 | cada peso invertido deja 15 centavos de VAN |

Decide el **VAN**. La TIR sirve para comunicar, salvo que el flujo cambie de signo más de una
vez (entonces puede haber varias y no sirve).

## 5. Sensibilidad: qué supuesto decide

Se mueve una variable a la vez y se busca el valor que deja el VAN en cero:

| Variable | Base | Valor crítico | Margen |
|---|---|---|---|
| Tarifa | $45.000 | $39.484 | −12,3 % |
| Ocupación | 55 % | 47,2 % (170 días) | −14,1 % |
| Precio del furgón | $18.000.000 | $21.516.694 | +19,5 % |
| Tasa de descuento | 12 % | 17,08 % (la TIR) | +42 % |

Lectura: el proyecto **depende de la ocupación y de la tarifa**. Si el furgón se arrienda menos
de 170 días al año, o si hay que bajar la tarifa más de un 12 %, deja de convenir. Lo primero que
hay que validar no es el precio del seguro: es cuántos días se va a arrendar.

## 6. Decidir y dejar la traza

La recomendación dice el VAN, la variable que decide, su valor crítico y el margen contra lo
supuesto. Y deja los supuestos a la vista para que alguien los pueda discutir.

Con el agente: llena `plantillas/entrada.json` y corre

```
python scripts/evaluar.py entrada.json --perfil <empresa> --barrer "ingresos[0].ocupacion=0.4,0.5,0.6"
```

El Excel de salida trae las cuatro hojas (SUPUESTOS · FLUJO · INDICADORES · SENSIBILIDAD) con el
origen de cada número.

## Siguiente paso

Si conviene y hay que decidir cómo pagarlo, ver `evaluacion-financiera`.
