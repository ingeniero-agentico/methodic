# ingeniero-agentico · reglas del repo

Repo **público**. Todo lo que entra acá lo puede leer cualquiera.

## Reglas duras

1. **Cero datos reales.** Ningún RUT, nombre de empresa, cliente, proveedor, persona, patente, precio
   real ni ruta local. Los ejemplos y las pruebas usan casos ficticios (empresa «Ferretería Andes»,
   «Constructora Sur», proveedores «Proveedor A/B/C»). Los datos reales viven en
   `ingeniero-agentico-datos/`, fuera del repo.
2. **Una skill por método, no por ramo.** El ramo es fuente, no estructura.
3. **Todo número sale de un script.** La skill decide; el script calcula. Ninguna cifra que el
   usuario vaya a usar se calcula «de cabeza».
4. **Cada método trae una prueba que cuadra.** `pruebas/` tiene un caso ficticio con el resultado
   esperado, y `python scripts/<script>.py --probar` termina en `OK` o falla.
5. **Trazable.** Cada salida dice de qué entrada vino cada número (archivo, línea, supuesto).
   Un supuesto que no vino del usuario se marca `SUPUESTO` en la salida.
6. **El material de los cursos no se reproduce.** Se cita en `fuentes.md` (autor, título, edición,
   capítulo). Nada de láminas, pautas ni certámenes.
7. **El perfil manda.** Moneda, impuestos, tasas y criterios de la empresa se leen del perfil
   (`perfiles/_plantilla.yaml` define los campos). Ningún valor de una empresa va escrito dentro
   de una skill.

## Molde de un método

```
skills/<metodo>/
├── SKILL.md      frontmatter name + description (en inglés las condiciones de uso, cierra con una
│                 frase en español; máximo 1.024 caracteres, el límite del estándar Agent Skills y
│                 de claude.ai); cuerpo en español: cuándo, qué decide el agente, qué calcula
│                 el script, cómo se lee la salida, errores típicos
├── GUIA.md       el mismo método para una persona, paso a paso, con el caso ficticio
├── plantillas/   entradas vacías (YAML o JSON) y, si aplica, el Excel de salida
├── scripts/      Python 3.11+, solo biblioteca estándar + openpyxl; `--probar` corre la prueba
├── pruebas/      caso-ficticio.(yaml|json) + esperado.json
└── fuentes.md    ramos y bibliografía de donde sale el método
```

## Redacción

Español de Chile, directo. El inciso va entre paréntesis; la raya solo separa.
