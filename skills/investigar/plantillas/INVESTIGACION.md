# Investigación · <encargo en pocas palabras> · DD-MM-AAAA

- **Etapa:** 1 · Investigar, modo <primera vez | hueco nuevo en relectura>.
- **Origen de los huecos:** <contexto/MAPA.md · contexto/PLAN.md · encargo>.
- **Datos máquina-legibles:** `datos-investigados.json` (esta página lo resume).
- **Validación:** `python validar_investigacion.py <caso>/contexto/datos-investigados.json` → **OK**
  (N huecos, N datos, 0 errores, N avisos).

## Respuesta corta

Tres a cinco líneas: qué se cerró (con la cifra y su fuente), qué quedó sin dato y si cambia la
decisión.

## Huecos

| Id | Pregunta | Precisión que pide el cálculo | Para qué campo | Estado | Dato elegido |
|---|---|---|---|---|---|

## Barrido de obtenibilidad (antes de investigar)

| Id | Fuente | Acceso | Huecos | Nota |
|---|---|---|---|---|

Acceso: `abierta` · `lo_baja_la_persona` (login, CAPTCHA, pago, página que no carga sin navegador)
· `sin_fuente_publica` · `no_responde`.

## Datos

Pegar la salida de `validar_investigacion.py --tabla`. Ninguna cifra se copia a mano.

Notas que cambian la lectura de un dato: <solo las que importan>.

## Contradicciones

| Datos | Manda | Por qué |
|---|---|---|

## Cadena de cálculo

Solo si hay datos `calculado`: eslabón por eslabón, con el id de cada insumo y su nivel.

## Lo que tiene que bajar o pedir la persona

1. <gestión concreta que cierra un hueco sin dato>

## Qué cambiaría en el caso

Si ya hay un cálculo: si el dato mueve la decisión, contra el umbral que el cálculo declaró. Si se
recalculó, la copia de la entrada y su salida están en `sensibilidad/`; la entrada y la salida del
caso no se tocan.

## Avisos del validador

- <código · dato · qué significa>
