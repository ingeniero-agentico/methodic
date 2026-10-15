---
name: evaluacion-economica
description: Use when someone must decide whether a project or investment is worth doing on its own merits, regardless of how it is financed (buying a vehicle or machine to rent it out, a new business line, replacing equipment, expanding capacity). Builds the Chilean-style pure project cash flow (with tax, depreciation, working capital and salvage value), computes NPV (VAN), IRR (TIR, warning on multiple sign changes), payback, IVAN, and a one-variable sensitivity with the critical value that makes NPV zero (e.g. break-even occupancy). Triggers: «¿conviene comprar…?», «evalúa este proyecto», «calcula el VAN y la TIR», «¿con qué ocupación se paga?». Not for choosing how to finance it: that is evaluacion-financiera. Evalúa si un proyecto conviene por sí mismo: flujo puro, VAN, TIR, recuperación y sensibilidad.
---

# Evaluación económica · ¿conviene el proyecto?

Evalúa el **proyecto puro**: si el negocio conviene por sí mismo, como si se pagara entero con
plata propia. Cómo financiarlo (crédito, leasing, flujo del inversionista) es otro método:
`evaluacion-financiera`.

## Cuándo

- Comprar un activo para producir o arrendar (vehículo, máquina, local).
- Abrir una línea de negocio, ampliar capacidad, reemplazar un equipo.
- Cualquier pregunta «¿conviene?» o «¿cuánto tiene que vender para que se pague?».

## Qué decide el agente (el script no lo decide)

1. **Qué entra al flujo.** Solo lo **incremental**: lo que cambia si se hace el proyecto. Un costo
   que la empresa paga igual (el sueldo del dueño, la oficina) no entra. Un ingreso que se le quita
   a otro producto de la misma empresa se descuenta.
2. **Neto o bruto de IVA.** Si la empresa recupera el IVA crédito, todo va neto. Si no lo recupera
   (giro exento, vehículo sin derecho a crédito), el IVA de la compra es parte de la inversión.
   Se dice en la `nota` de la entrada.
3. **Ingresos.** `precio` por unidad y `cantidad`, o `capacidad` × `ocupacion` cuando lo que manda
   es cuánto se usa el activo (días arrendados, horas máquina). Con `ocupacion`, la sensibilidad
   entrega directamente la **ocupación crítica**.
4. **Costos.** Variables (por unidad de un ingreso, campo `por_unidad_de`) y fijos (por año). Lo que
   paga el cliente aparte (combustible, peajes) no es costo del proyecto.
5. **Inversiones.** Monto, año, vida útil tributaria (la tabla del servicio de impuestos del país),
   valor de desecho. Una reinversión a mitad de camino es otra inversión con su `anio`.
6. **Capital de trabajo.** Lo que hay que tener en caja antes de cobrar (seguros, permisos,
   inventario, desfase de cobro). Se recupera al final salvo `"recupera": false`.
7. **Pérdidas tributarias.** `arrastra` (proyecto aislado: la pérdida rebaja utilidades futuras del
   mismo proyecto) o `compensa` (la empresa tiene otras utilidades y la pérdida ahorra impuesto ese
   año). Por defecto `arrastra`, la conservadora.
8. **Qué es SUPUESTO.** Todo número que no vino del usuario ni de un documento lleva `"supuesto"`
   (`true` para el ítem entero, o la lista de campos) y su razonamiento en `fuente`. La salida los
   marca en amarillo. Nunca inventar un número sin marcarlo.
9. **Tasa e impuesto.** Salen del perfil. Si el perfil no los trae, el script exige `--tasa` o
   `--impuesto` y los marca SUPUESTO; el agente dice de dónde salió el valor que propuso.

## Qué calcula el script

`scripts/evaluar.py` (Python 3.11+, biblioteca estándar + openpyxl):

- **Flujo de caja del proyecto puro**, año 0 a N: ingresos − costos variables − costos fijos −
  depreciación + venta de activos − valor libro = utilidad antes de impuesto; − impuesto (tasa del
  perfil) = utilidad neta; + depreciación + valor libro (no son salidas de caja) − inversiones −
  capital de trabajo + su recuperación = flujo.
- **Valor de desecho comercial**: los activos se venden al final al `valor_desecho`; la ganancia
  sobre el valor libro paga impuesto y la pérdida lo rebaja. Con `metodo_desecho: contable` se
  venden a valor libro (sin efecto tributario).
- **Indicadores**: VAN, TIR (todas las raíces entre −95 % y 1.000 %; aviso si el flujo cambia de
  signo más de una vez), período de recuperación simple y descontado (interpolado dentro del año),
  IVAN = VAN ÷ inversión en valor presente.
- **Sensibilidad**: cada variable ±`--delta` (10 % por defecto) con las demás fijas, ordenadas de
  la que más mueve el VAN a la que menos, y el **valor crítico** de cada una (el que deja el VAN en
  cero, por bisección). El crítico de la tasa es la TIR. `--barrer` recorre una variable por
  valores dados.

```
python scripts/evaluar.py <entrada.json> [--perfil <nombre|ruta>] [--tasa 0.12] [--impuesto 0.27]
                          [--delta 0.10] [--barrer "ingresos[0].ocupacion=0.3,0.5,0.7"]
                          [--salida <carpeta>]
python scripts/evaluar.py --probar
```

El perfil se busca así: `--perfil` (nombre o ruta) · `$INGENIERO_DATOS/perfiles/` ·
`../ingeniero-agentico-datos/perfiles/` (si hay uno solo) · `perfiles/_plantilla.yaml`.
La entrada vacía está en `plantillas/entrada.json`.

## Cómo se lee la salida

`salida.xlsx` (y `salida.json` con lo mismo):

| Hoja | Qué tiene |
|---|---|
| SUPUESTOS | cada parámetro con su valor, su origen (perfil, argumento, campo de la entrada y fuente) y la marca `SUPUESTO` o `dato` |
| FLUJO | el flujo línea por línea, año por año, con la columna «Origen» |
| INDICADORES | decisión, VAN, TIR, cambios de signo, recuperación, IVAN y los avisos |
| SENSIBILIDAD | tornado (±x %) y valor crítico de cada variable; los barridos pedidos |

La decisión es el **VAN**: ≥ 0 conviene a la tasa exigida. La TIR acompaña; con varios cambios de
signo no se usa. Lo que se le cuenta a la persona es el VAN, el valor crítico de la variable que
más pesa (por ejemplo «se paga si se arrienda más de 154 días al año») y cuánto margen hay entre
el valor supuesto y el crítico.

## Errores típicos

- **Meter el financiamiento.** Intereses y cuotas del crédito no van aquí: van en
  `evaluacion-financiera`, sobre este flujo.
- **Olvidar sumar la depreciación de vuelta.** Se resta para calcular el impuesto y se suma porque
  no sale de la caja.
- **Valor de desecho sin impuesto.** Vender sobre el valor libro paga impuesto; el script lo hace.
- **Tasa nominal con flujos en pesos de hoy.** Si los montos no tienen inflación, la tasa es real.
- **Ocupación del activo nuevo = ocupación de la flota actual.** Lo que vale es la demanda
  **adicional** que hoy se pierde por no tener la unidad, no el promedio de las que ya existen.
- **Costos que se pagan igual.** Un sueldo o un arriendo que no cambia no es del proyecto.
- **Decidir con la TIR cuando el flujo cambia de signo varias veces.** Puede haber varias.

## Prueba

`python scripts/evaluar.py --probar` corre `pruebas/caso-ficticio.json` (Transportes del Valle,
furgón para arriendo) contra `pruebas/esperado.json`, verificado por un camino independiente, y
termina en `OK` o `FALLA`.
