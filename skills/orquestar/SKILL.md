---
name: orquestar
description: Use when an engineering or business task arrives and it needs more than one step or it is not obvious which method applies — "¿me conviene comprar esto?", "¿a quién le compro?", "¿a cuánto lo vendo?", "¿cómo lo financio?", a folder of quotes, a project idea or an investment to decide, or when the person asks to "lanzar agentes", "orquestar", "investigar y calcular". Maps the relevant environment first, decides between a first-time run (research) and a cheap re-read, proposes a plan of agents with one skill per stage, waits for approval, launches them in parallel where possible, audits and consolidates one traceable answer. Recibe el encargo, cartografía el contexto, propone el plan de agentes, lo lanza con aprobación y entrega una sola respuesta auditada.
---

# Orquestar un encargo

Corres en la **conversación principal**: eres el único que puede lanzar agentes. Los agentes de
`agents/` son trabajadores de una etapa; ninguno lanza a otro. El contrato completo está en
`ARQUITECTURA.md` (raíz del repo): léelo si algo de acá no alcanza.

**No resuelves de cabeza.** Cada número sale del script de un método, y cada dato externo de la
investigación con su fuente.

## 0. Entender el encargo y encontrar los datos

1. Reescribe el encargo en una línea: qué decisión hay que tomar y para quién.
2. Perfil de la empresa: `INGENIERO_DATOS` → `../ingeniero-agentico-datos/perfiles/` → plantilla.
   Si hay más de un perfil y el encargo no dice cuál, **pregunta**.
3. Carpeta del caso: `<datos>/casos/<metodo>-<caso>/` (créala si es nuevo). Ahí vive `contexto/`.
4. Elige el método o la cadena:

| El encargo pregunta… | Método |
|---|---|
| A quién le compro, qué falta cotizar | `adquisiciones` |
| Cuánto costó, a cuánto vendo, cuánto gano | `costo-y-precio` |
| ¿Conviene este proyecto o inversión? | `evaluacion-economica` |
| ¿Cómo lo financio? | `evaluacion-financiera` |

Cadenas: cotizaciones → `adquisiciones` → `costo-y-precio`. Inversión → `evaluacion-economica` →
(si VAN ≥ 0) `evaluacion-financiera`. Si ninguno calza, dilo; no fuerces uno.

## 1. Cartografiar (siempre, es barato)

Lanza el agente `cartografo` sobre las carpetas que toca el encargo (las del caso, las que la
persona nombró, el perfil). Devuelve el **modo** y la ruta de `contexto/MAPA.md`.

- `primera-vez`: no había mapa o cambió más del umbral.
- `relectura`: hay mapa y cambió poco. Desde acá **lees el mapa, no las carpetas**, y solo los
  archivos que el cartógrafo listó como cambiados.

La persona puede forzar el modo («hazlo en relectura», «investiga desde cero»). Su palabra manda.

## 2. Planificar y pedir

Con el mapa (y sin abrir más archivos de los necesarios), escribe `contexto/PLAN.md`:

```
Encargo: <una línea>
Modo: primera-vez | relectura        Agentes: N        Costo estimado: bajo | medio | alto

| # | Etapa      | Agente       | Skill                 | Modelo  | Entrada            | Salida                | Depende de |
|---|------------|--------------|-----------------------|---------|--------------------|-----------------------|------------|
| 1 | Investigar | investigador | investigar            | opus    | huecos del mapa    | INVESTIGACION.md      | —          |
| 2 | Ejecutar   | ejecutor     | evaluacion-economica  | sonnet  | entrada.json       | salida.json           | 1          |
| 3 | Ejecutar   | ejecutor     | evaluacion-financiera | sonnet  | salida.json de 2   | salida.json           | 2          |
| 4 | Auditar    | auditor      | auditar               | opus    | todo lo anterior   | AUDITORIA.md          | 2, 3       |

Huecos que justifican investigar: <lista, o «ninguno»>
Supuestos que se usarán si no se investiga: <lista>
```

Reglas del plan:
- **Investigar solo si hay huecos** que el cálculo necesita. En relectura, por defecto no.
- **Modelos:** relectura → `haiku` o `sonnet` en todo menos auditar. Primera vez → `opus` en
  investigar y auditar. El auditor nunca baja de `sonnet`.
- **Paralelo** lo que no depende entre sí; en secuencia lo encadenado.
- **El auditor va siempre** si hay números que alguien va a usar.
- Costo: bajo ≤ 2 agentes económicos · medio 3 a 4 · alto ≥ 5 o dos `opus`.

**Muéstrale el plan a la persona y espera.** Responde «sí», cambia una fila o pide otro modo.
No lances ningún agente antes. Si la persona dice «sin agentes» o el entorno no los permite,
haz cada etapa tú, en orden, en esta conversación.

## 3. Lanzar

- Lanza en **un mismo mensaje** todos los agentes de una ola sin dependencias pendientes.
- A cada uno le pasas: su fila del plan, la ruta de `contexto/`, el perfil, la carpeta del caso y
  qué devolver. Nada más: el resto lo lee del mapa.
- Al terminar una ola, revisa que la salida exista antes de lanzar la siguiente. Si un agente
  falla, no lo reemplazas con un cálculo tuyo: lo informas y propones el arreglo.

## 4. Consolidar

Con `AUDITORIA.md` a la vista. Si hay **NO CONFORME**, esa es la primera línea de la respuesta.

1. **La decisión** en una frase (qué conviene y por cuánto).
2. **Los supuestos que la deciden**: los dos o tres que la dan vuelta, con su umbral.
3. **Dónde quedó** cada salida.
4. **Qué falta** preguntarle a quien decide.

Al cerrar, el cartógrafo ya dejó `huellas.json`: la próxima vez sobre el mismo caso será relectura.

## Errores típicos

- Leer las carpetas completas en relectura «para estar seguro»: anula el ahorro. Si el mapa no
  basta, el arreglo es mejorar el mapa, no saltárselo.
- Lanzar el investigador por costumbre: solo con huecos declarados.
- Dar la respuesta antes de la auditoría.
- Escribir `contexto/` dentro del repo público: va siempre en la carpeta de datos.
