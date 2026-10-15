# Fuentes · evaluacion-financiera

El método se cita; el material de los cursos no se reproduce.

## Ramos (Ingeniería Civil Industrial)

| Ramo | Qué aporta al método |
|---|---|
| Finanzas (2026-1) | valoración, CAPM y beta (desapalancado y apalancado), estructura de capital y costo de capital; teoría de portafolio como base del riesgo sistemático |
| Finanzas (2026-2) | valor del dinero en el tiempo, tasas equivalentes, anualidades (cuota de un crédito), VAN; renta fija (flujo de una deuda y su tasa interna) |
| Taller de Evaluación Técnica de Proyectos | flujo de caja del proyecto puro como entrada; separación entre proyecto y financiamiento |

## Bibliografía

- Sapag Chain, N., Sapag Chain, R. y Sapag Puelma, J. M. *Preparación y evaluación de proyectos*
  (6.ª ed.). McGraw-Hill, 2014. Caps. 1 y 2 (el proyecto como decisión de inversión); los
  capítulos de construcción de flujos de caja (flujo del proyecto y flujo del inversionista con
  préstamo, intereses como gasto y amortización después de impuesto) y de tasa de descuento
  (costo de la deuda, costo del capital propio, costo ponderado). El curso entrega los caps. 1 y 2;
  la edición de ese extracto no está verificada.
- Blank, L. y Tarquin, A. *Ingeniería económica* (7.ª ed.). McGraw-Hill, 2012. ISBN
  978-607-15-0761-7. Cap. 2 (factores; P/A y A/P, base de la cuota francesa), cap. 4 (tasas
  nominales y efectivas; de mensual a anual), cap. 7 (tasa de rendimiento y raíces múltiples),
  cap. 10 (financiamiento del proyecto: costo de la deuda y del capital propio, mezcla
  deuda-capital y costo promedio ponderado), cap. 16 (depreciación), cap. 17 (análisis después de
  impuestos: flujo después de impuestos y efecto de la depreciación sobre el impuesto).
- Támara Ayús, A. L., Chica Arrieta, I. E. y Montiel Ensuncho, A. «Metodología de cálculo del
  beta: beta de los activos, beta apalancado y beta corregido por cash». *Revista Espacios*,
  vol. 38, n.º 34, 2017, p. 15. Apunte del ramo de Finanzas para el CAPM de la GUIA.

## Normativa chilena que usa el caso típico

- Ley 18.010, arts. 6 y 6 bis: interés corriente e interés máximo convencional (la CMF publica el
  certificado cada mes en el Diario Oficial). Referencia de mercado para la tasa de un crédito.
- Ley 20.555 y su reglamento: la CAE como costo anual de un crédito con gastos incluidos.
- DL 3.475, impuesto de timbres y estampillas: 0,066 % por mes de plazo con tope de 0,8 % (SII,
  Circular 17 de 2015). Va en `impuesto_credito` del caso.
- Ley sobre Impuesto a la Renta (DL 824), art. 31: intereses, cuotas de leasing y rentas de
  arriendo como gasto; art. 31 n.º 5 y 5 bis: depreciación normal y acelerada; art. 14 letra D:
  régimen Pro Pyme (depreciación instantánea, gasto lo efectivamente pagado).
- Ley 21.540 (15-02-2023) y SII, Circular 14 de 2023: derogan el art. 37 bis (leasing como activo
  del arrendatario); la cuota de leasing vuelve a ser gasto. Si un país trata el leasing como
  activo, el caso se modela como crédito.

La tasa de impuesto, la tasa de descuento y el horizonte **no** se escriben aquí: los da el perfil
de cada empresa.
