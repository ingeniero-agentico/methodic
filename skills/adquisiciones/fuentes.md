# Adquisiciones · fuentes

El método se cita; el material de los cursos no se reproduce.

## Ramos de donde sale

| Ramo | Qué aporta al método |
|---|---|
| **Gestión de Operaciones** | abastecimiento: selección de proveedores, comparación de ofertas, cobertura parcial, plazos y condiciones de entrega |
| **Optimización** | el reparto como problema lineal: minimizar Σ costo × cantidad sujeto a cubrir la demanda de cada ítem y no pasar lo disponible de cada proveedor |
| **Contabilidad y Costos** | costo de adquisición: precio neto efectivo (después de descuentos), IVA aparte del costo, el sobrante comprado se carga al costo del material |

## Por qué la cascada es la decisión correcta (y cuándo deja de serlo)

Sin costos fijos por orden, cada ítem es un problema lineal separable: minimizar
Σ cᵢ·xᵢ con Σ xᵢ = demanda y 0 ≤ xᵢ ≤ disponibleᵢ. La solución óptima es asignar en orden
creciente de costo unitario hasta cubrir la demanda (el mismo argumento de la mochila fraccionaria).
La cascada es ese óptimo, no una aproximación.

Deja de ser óptima cuando aparece algo que no es lineal en la cantidad, y entonces el problema pasa
a ser entero mixto:

- un costo fijo por orden o por despacho (conviene concentrar en menos proveedores);
- compras mínimas, o descuentos por volumen que dependen del total de la orden;
- unidades de venta enteras (tiras, cajas): la cascada redondea hacia arriba y declara la sobra,
  que es una heurística razonable pero no siempre el mínimo.

Esta versión no modela esos casos: los deja a la revisión humana (SKILL.md, «Revisar antes de
emitir»).

## Bibliografía

- Monczka, R. M.; Handfield, R. B.; Giunipero, L. C.; Patterson, J. L. *Purchasing and Supply Chain
  Management*. 7.ª ed. Cengage Learning, 2021. Capítulos sobre evaluación y selección de
  proveedores, y sobre gestión de costos de compra.
- van Weele, A. J. *Purchasing and Supply Chain Management: Analysis, Strategy, Planning and
  Practice*. 7.ª ed. Cengage Learning, 2018. Proceso de compra: especificación, selección,
  contratación y orden.
- Chopra, S.; Meindl, P. *Supply Chain Management: Strategy, Planning, and Operation*. 7.ª ed.
  Pearson, 2019. Capítulo de decisiones de abastecimiento (sourcing) y costo total.
- Heizer, J.; Render, B.; Munson, C. *Operations Management: Sustainability and Supply Chain
  Management*. 13.ª ed. Pearson, 2020. Capítulo de administración de la cadena de suministro.
- Hillier, F. S.; Lieberman, G. J. *Introduction to Operations Research*. 11.ª ed. McGraw-Hill,
  2021. Programación lineal, problema de transporte y programación entera.
- Horngren, C. T.; Datar, S. M.; Rajan, M. V. *Cost Accounting: A Managerial Emphasis*. 16.ª ed.
  Pearson, 2018. Costeo de materiales y asignación de costos.

## De dónde salió el criterio

De compras reales de una pyme industrial (datos privados, fuera de este repo). Las reglas duras de
`SKILL.md` (unitario derivado del total, cuadratura contra el subtotal impreso, compra en la unidad
del proveedor, descarte declarado y no borrado, cambio de moneda puesto por quien paga) nacieron de
errores que pasaron en esas compras. El script reproduce al centavo el reparto de un caso real de
64 ítems y 5 proveedores.
