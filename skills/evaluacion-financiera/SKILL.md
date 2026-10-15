---
name: evaluacion-financiera
description: Use when an asset or project is already worth doing and the question is how to pay for it — cash versus a bank or car loan (French or German amortization, amortization table, CAE), financial leasing (installments, purchase option, tax effect of deducting the installments), or renting instead of buying — and how much each option changes the owner's result after tax. Builds the investor cash flow (pure project flow + financing, with the interest tax shield), the investor NPV, the after-tax effective cost of each alternative, the discount rate at which the decision flips, and a sensitivity table; reads the pure project flow from a file (the output of evaluacion-economica or a simple year/flow CSV). Triggers: «¿contado, crédito o leasing?», «¿me conviene financiarlo?», «arma la tabla de amortización», «¿cuál es la CAE?», «flujo del inversionista», «¿arriendo o compro?». Not for deciding whether the project itself is worth doing (that is evaluacion-economica). Decide cómo financiar un activo (contado, crédito, leasing o arriendo) y cuánto cambia para el dueño después de impuesto.
---

# evaluacion-financiera

Responde **cómo financiar** un activo y cuánto cambia para el dueño. No responde si el proyecto
conviene: eso es `evaluacion-economica`, y su flujo puro es la entrada de este método.

Es un método de cálculo, no asesoría financiera personalizada.

## Cuándo

- El proyecto ya conviene (o se va a hacer igual) y hay que elegir entre pagar al contado, pedir un
  crédito, tomar un leasing o arrendar.
- Llegó una cotización de crédito o de leasing y hay que saber cuánto cuesta de verdad (CAE, tasa
  implícita, costo después de impuesto).
- Piden la tabla de amortización, el flujo del inversionista o el VAN del inversionista.

## Qué decide el agente (el juicio)

1. **Qué alternativas comparar.** Solo las que la empresa puede tomar de verdad. Si no tiene la
   plata, el contado queda como referencia, no como opción; dilo en la salida.
2. **Que sean el mismo activo.** Normalizar antes de comparar: mismo precio neto, mismo plazo de
   uso, mismo valor de venta al final. Lo que cambia entre ofertas (un bono por financiar con la
   marca, una renta que incluye mantención) se carga en el caso: el precio propio en `precio_neto`
   de la alternativa y lo demás en `notas_no_comparables`, que la salida declara, no promedia.
3. **Qué tasa de descuento usar.** La del perfil (`finanzas.tasa_descuento`): el costo de
   oportunidad del dinero del dueño. Si el perfil no la trae, el script la exige con `--tasa` y la
   marca SUPUESTO. Una pyme no necesita CAPM: basta con lo que rinde su plata en la mejor
   alternativa real (depósito, pagar otra deuda, otro proyecto). El WACC y el CAPM están en la
   GUIA como referencia.
4. **Qué impuesto.** `empresa.impuesto_renta` del perfil o `--impuesto`. Si el régimen no está
   claro (persona natural con giro, Pro Pyme, régimen general), correr la sensibilidad con las
   tasas posibles (`sensibilidad.impuestos` en el caso) y decir cuál cambia la decisión.
5. **Buscar los datos que faltan** (precio, tasa del crédito, condiciones del leasing): con la
   fuente (URL y fecha) en el campo `fuente`; si no se encuentra, `"supuesto": true`.

## Qué calcula el script

`scripts/evaluacion_financiera.py` (Python 3.11+, biblioteca estándar + openpyxl):

- **Tabla de amortización** por alternativa: crédito con cuota francesa (fija) o alemana
  (amortización fija), leasing con cuota inicial y opción de compra. Cuotas e intereses al peso;
  la última cuota absorbe el redondeo.
- **CAE** del crédito (TIR mensual × 12 de lo que llega al deudor contra lo que paga, con gastos e
  impuesto al crédito) y **tasa implícita** del leasing (o la despeja si se da la cuota).
- **Flujo del activo** mes a mes y después de impuesto: pagos, ahorro tributario de intereses y
  gastos financieros, de depreciación, de cuotas de leasing o de renta (al cierre de cada año), y
  valor residual neto del impuesto a la venta.
- **Costo en valor presente después de impuesto** de cada alternativa; la de menor costo gana.
- **Costo efectivo anual después de impuesto**: TIR de (alternativa − contado). Si es menor que la
  tasa de descuento, financiar así conviene más que pagar al contado.
- **Flujo y VAN del inversionista**: flujo del proyecto + (flujo del activo con la alternativa −
  flujo del activo al contado). Así la compra no se cuenta dos veces; al contado, VAN del
  inversionista = VAN del proyecto.
- **Tasa de indiferencia** entre la ganadora y la segunda, y sensibilidad tasa × impuesto.

```
python scripts/evaluacion_financiera.py --caso caso.json [--proyecto flujo.csv|salida.json]
       [--perfil empresa] [--tasa 0.12] [--impuesto 0.25] [--salida carpeta]
python scripts/evaluacion_financiera.py --probar
```

El perfil se busca en este orden: ruta dada en `--perfil` (o campo `perfil` del caso) ·
`$INGENIERO_DATOS/perfiles/<empresa>.yaml` · `../ingeniero-agentico-datos/perfiles/` ·
`perfiles/_plantilla.yaml` (y entonces todo sale SUPUESTO).

El flujo del proyecto es un archivo: la `salida.json` de `evaluacion-economica` tal cual, o un CSV
con columnas `anio,flujo` (números sin separador de miles). Plantillas en `plantillas/`.

## Cómo se lee la salida

`<caso>-evaluacion-financiera.xlsx` y `<caso>-resultado.json`:

| Hoja | Qué dice |
|---|---|
| SUPUESTOS | cada parámetro, su valor, de dónde vino; fila naranja = SUPUESTO; reglas del modelo y avisos |
| AMORTIZACION | una tabla por crédito o leasing, con CAE o tasa implícita y el chequeo «suma de amortizaciones = monto» |
| FLUJO-INVERSIONISTA | por alternativa y por año: proyecto, pagos, ahorros tributarios, residual, flujo del inversionista; al final la tabla mensual con la que se calcula el VAN |
| COMPARACION | ranking por costo en VP, ganadora y por cuánto, tasa que cambia la decisión, lo no comparable y la sensibilidad |

Se informa: «Gana X: cuesta $N menos en VP que Y», la tasa de indiferencia y qué SUPUESTO podría
dar vuelta la decisión. Nada de cifras calculadas fuera del script.

## Errores típicos

- **Comparar la cuota mensual.** Una cuota más baja a más plazo no es más barata; se compara el
  costo en VP después de impuesto.
- **Olvidar el escudo tributario.** Los intereses, las cuotas de leasing y la renta rebajan
  impuesto; el capital del crédito no.
- **Contar la compra dos veces** al sumar el préstamo a un flujo que ya trae la inversión: por eso
  el script suma la diferencia frente al contado.
- **Leasing en otro país.** El script trata la cuota de leasing como gasto del arrendatario (regla
  chilena vigente: el art. 37 bis de la LIR se derogó en 2023). Donde el arrendatario activa el bien,
  hay que modelarlo como crédito.
- **Régimen Pro Pyme.** Con depreciación instantánea (`"depreciacion": "instantanea"`), comprar
  rebaja todo el primer año y el leasing pierde su ventaja tributaria.
- **Un ahorro tributario sin utilidades.** El modelo supone que la empresa tiene utilidades para
  usarlo; si no las tiene, el escudo no existe ese año.
- **Tasa efectiva con varios cambios de signo.** La salida lo avisa; ahí se decide por el costo en VP.
