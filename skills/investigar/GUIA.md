# Guía · investigar

Cómo cerrar los huecos de un cálculo con datos que aguanten una pregunta («¿de dónde sale ese
número?»), paso a paso, con el caso ficticio de `pruebas/caso-ficticio.json`.

## La pregunta

**Ferretería Andes** (empresa ficticia) evalúa comprar una grúa horquilla eléctrica al contado o
con leasing. El cálculo (`evaluacion-financiera`) está listo, pero le faltan cuatro números:

| Hueco | Pregunta | Precisión |
|---|---|---|
| H1 | Tasa mensual de leasing para una pyme, equipo de bodega, 36 meses | ±0,05 puntos |
| H2 | Tasa máxima legal para operaciones de ese monto | exacta |
| H3 | Valor de venta de la grúa al año 5 | ±15 % |
| H4 | Gastos de escritura e inscripción del contrato | ±$20.000 |

La precisión no es un adorno: dice cuándo parar. Si el cálculo tolera ±15 %, buscar el tercer
decimal es perder el tiempo.

## Paso 1 · El barrido de obtenibilidad, antes de buscar

Para cada hueco, qué fuentes existen y cuáles se pueden abrir:

| Fuente | Acceso | Hueco |
|---|---|---|
| Certificado mensual del regulador (ficticio) | abierta | H2 |
| Portal de remates de equipos | lo baja la persona (pide cuenta registrada) | H3 |
| Tasas de leasing de bancos | sin fuente pública (se cotizan) | H1 |
| Arancel del registro | abierta | H4 |

**Lo que está tras un login o un CAPTCHA no se intenta saltar:** se anota para la persona. Y que
nadie publique la tasa de leasing también es un dato: dice que el hueco se cierra cotizando, no
buscando.

¿Por qué antes? Porque relevancia y acceso son independientes: la fuente que más sirve suele ser
la menos accesible. Si el acceso se revisa al final, la búsqueda se hace dos veces.

## Paso 2 · Un dato concreto por hueco

Para H1 llegan tres cifras:

| Dato | Valor | Fuente | Nivel |
|---|---|---|---|
| F1 | 1,45 % mensual | cotización Proveedor A | C |
| F2 | 1,62 % mensual | cotización Banco B (incluye seguro) | C |
| F3 | 1,10 % mensual | un foro | D |

Cada una lleva valor, unidad, fecha del dato, fuente, fecha de consulta y nivel (ficha completa en
`plantillas/ficha-dato.md`). F3 es D: **orienta, pero no entra al cálculo** salvo marcado
SUPUESTO. Y si una cifra se leyó en el resumen de un buscador y no en el original, queda «por
confirmar», aunque venga de un organismo oficial.

## Paso 3 · Las contradicciones, juntas y con razón

F1 y F2 miden lo mismo y F2 es 11,7 % más alta: supera el umbral de 10 %. No se promedian. Se
ponen juntas y se elige con una razón que alguien pueda revisar:

> Manda F1: F1 y F2 son cotizaciones del mismo equipo; F2 trae un seguro dentro de la tasa. F3 es
> un foro y no compite.

Las razones típicas: el dato vigente sobre el anterior, la fuente primaria sobre la prensa, lo
medido sobre lo teórico, el segmento exacto sobre el promedio general. Cuando dos cifras **parecen**
responder lo mismo pero miden cosas distintas (un promedio de todo el sistema contra el de un
tramo), la razón es decir qué mide cada una.

## Paso 4 · La cadena de cálculo, también auditada

H2 viene anual (30 % lineal, F4) y el cálculo lo pide mensual. El mensual no se escribe a mano: es
un dato `calculado` con su fórmula, `F5 = F4 / 12 = 2,5 %`. El validador lo recalcula y revisa
que no tenga un nivel mejor que su peor insumo: un cálculo nunca es más confiable que el dato más
débil que usa.

## Paso 5 · Lo que no se encontró se declara

H3 no tiene fuente abierta: queda «sin dato», con la gestión que lo cierra («pedir tasación por
escrito a dos distribuidores de equipos usados»). Un hueco declarado cuesta menos que un dato
falso; el cálculo sigue con su SUPUESTO y la persona sabe qué pedir.

H4 mezcla: el arancel oficial de inscripción (F7, A) entra como dato; la notaría solo tiene un foro
(F6, D), y entra como SUPUESTO.

## Paso 6 · Validar y escribir

```
python scripts/validar_investigacion.py pruebas/caso-ficticio.json
```

El validador revisa los campos, los niveles, las fechas, que cada hueco tenga dato o gestión, que
ningún D entre sin SUPUESTO, la cadena de cálculo y las contradicciones. Termina en `OK` o lista
los errores. En el caso ficticio da OK con cuatro avisos: el arancel es de hace más de un año, el
arancel tiene una sola fuente, la notaría no tiene fecha y el portal de remates lo tiene que abrir
la persona.

Recién con `OK` se escribe `INVESTIGACION.md` (formato en `plantillas/`), pegando las tablas que
imprime `--tabla`.

## Paso 7 · ¿Cambia la decisión?

Si el cálculo ya existe y declaró un umbral («el leasing gana si la plata rinde más de X %»), la
investigación termina diciendo si el dato encontrado cruza ese umbral. Si hay que recalcular, se
corre el script del método sobre una **copia** de la entrada en `contexto/sensibilidad/`: la
entrada y la salida del caso no se tocan hasta que la persona decida.

## Lista de chequeo

- [ ] Cada hueco tiene pregunta, precisión, método y campo de destino.
- [ ] El barrido se hizo antes de buscar y dice qué tiene que bajar la persona.
- [ ] Cada dato tiene valor, unidad, fecha, fuente, fecha de consulta y nivel.
- [ ] Ningún D ni «por confirmar» entra al cálculo sin SUPUESTO.
- [ ] Las contradicciones están juntas y con razón.
- [ ] Los números derivados son datos `calculado` con fórmula, no cuentas en una nota.
- [ ] El validador termina en `OK`.
- [ ] `INVESTIGACION.md` dice si cambia la decisión.
