# ingeniero-agentico

Métodos de ingeniería industrial convertidos en **skills para agentes de IA**: cada método trae la
skill que ejecuta el agente, la guía para una persona, plantillas, el cálculo en un script y una
prueba que tiene que cuadrar.

Sirve para cualquier empresa. Los datos de cada empresa viven **fuera de este repo**, en un perfil
propio (ver «Datos privados»).

## Métodos

| Método | Qué resuelve | Estado |
|---|---|---|
| [adquisiciones](skills/adquisiciones/) | A quién comprar qué, cuando cada proveedor cubre solo una parte | v1 |
| [costo-y-precio](skills/costo-y-precio/) | Cuánto cuesta de verdad un trabajo y a cuánto venderlo | v1 |
| [evaluacion-economica](skills/evaluacion-economica/) | Si un proyecto o inversión conviene: flujo de caja, VAN, TIR, sensibilidad | v1 |
| [evaluacion-financiera](skills/evaluacion-financiera/) | Cómo financiarlo: crédito, leasing, arriendo o compra al contado | v1 |

Cada método se prueba con `python skills/<metodo>/scripts/<script>.py --probar`: corre un caso
ficticio cuyo resultado se calculó por un segundo camino, y termina en `OK` o falla.

## Cómo se trabaja un encargo

```
/nuevo-encargo ¿me conviene comprar otra camioneta para arrendarla?
```

La skill `orquestar` lo lleva por seis etapas (detalle en [ARQUITECTURA.md](ARQUITECTURA.md)):

1. **Cartografiar:** un agente barato hace el mapa de las carpetas que toca el encargo.
2. **Investigar:** solo si faltan datos; cada dato con fuente, fecha y fiabilidad.
3. **Planificar y pedir:** te muestra qué agentes lanzará, con qué skill y modelo. Espera tu sí.
4. **Ejecutar:** un agente por método, en paralelo cuando no dependen entre sí.
5. **Auditar:** un agente independiente vuelve a correr cada cálculo y compara.
6. **Consolidar:** una respuesta con la decisión, los supuestos que la deciden y qué falta.

**Dos modos.** La *primera vez* sobre un tema se investiga y se mapea completo. Las siguientes son
*relectura*: se lee el mapa en vez de las carpetas, con modelos económicos. El modo lo decide la
comparación de huellas de los archivos, no el modelo.

## Cómo está ordenado

```
ingeniero-agentico/
├── skills/        los métodos + orquestar · cartografiar · investigar · auditar
├── agents/        trabajadores de una etapa: cartografo · investigador · ejecutor · auditor
├── commands/      /nuevo-encargo
├── grafo/         notas enlazadas método ↔ ramo ↔ patrón, para Obsidian y graphify
└── perfiles/      la plantilla del perfil de empresa (vacía)
```

La forma es la de un plugin de Claude Code: más adelante se agrega `.claude-plugin/plugin.json`
y se instala con `/plugin install`, sin mover nada.

## Instalar (por ahora)

Copia la carpeta del método que necesites a `~/.claude/skills/`, o usa
`npx skills add <usuario>/ingeniero-agentico`.

## Datos privados

Cada skill busca el perfil de la empresa en este orden:

1. La ruta en la variable de entorno `INGENIERO_DATOS`.
2. La carpeta hermana `../ingeniero-agentico-datos/`.
3. Si no encuentra ninguna, trabaja con `perfiles/_plantilla.yaml` y te pide los datos que falten.

Esa carpeta lleva `perfiles/<empresa>.yaml` y `casos/<caso>/`. **Nunca se sube a este repo.**

## De dónde sale

Cada método nace de ramos de Ingeniería Civil Industrial y de su uso en empresas reales. El
`fuentes.md` de cada método cita la bibliografía; el material de los cursos no se reproduce.

## Licencia

Código y scripts: MIT. Guías y notas: CC BY-SA 4.0. Ver `LICENSE`.
