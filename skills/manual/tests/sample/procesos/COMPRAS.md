---
process: COMPRAS
title: Comprar material
status: En revisión
revision: B
date: 16-10-2026
owner: dueña
---
# COMPRAS · Comprar material

## SIPOC
| Proveedores | Entradas | Proceso | Salidas | Clientes |
|---|---|---|---|---|
| Bodega, 3 distribuidores | Solicitud, cotizaciones | Comprar material | Orden de compra | Bodega, contabilidad |

## Operación
- Frecuencia: dos o tres veces por semana · Origen: entrevista · dueña · 16-10-2026
- Fallas habituales: un proveedor no responde y se compra al de siempre · Origen: entrevista · dueña · 16-10-2026
- Archivos: carpeta Compras, una planilla por mes · Origen: entrevista · dueña · 16-10-2026

## Pasos
1. **COMPRAS-01** Bodega pide el material por WhatsApp.
   - Responsable: bodega · Herramienta: WhatsApp
   - Origen: entrevista · dueña · 16-10-2026
2. **COMPRAS-02** Compras pide tres cotizaciones por correo a los distribuidores.
   - Responsable: compras · Herramienta: correo
   - Origen: entrevista · dueña · 16-10-2026
3. **COMPRAS-03** ◆ Se comparan las cotizaciones y se elige proveedor → `procurement`.
   - Responsable: compras · Herramienta: planilla
   - Origen: documento · comparativo-agosto.xlsx, hoja 1
4. **COMPRAS-04** ◆ Sobre $500.000 aprueba la dueña.
   - Responsable: dueña
   - Origen: SUPUESTO · monto no confirmado
5. **COMPRAS-05** Se emite la orden de compra desde la plantilla.
   - Responsable: compras · Herramienta: plantilla-oc.xlsx
   - Origen: observado · bitácora, línea 1

## Huecos
- Monto de aprobación de COMPRAS-04 · declarado el 16-10-2026

## Historial
| Rev. | Fecha | Cambio | Aprobó |
|---|---|---|---|
| A | 16-10-2026 | Creado en la entrevista | — |
| B | 16-10-2026 | COMPRAS-03 enlazado al comparativo | dueña |
