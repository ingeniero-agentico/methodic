# Cartografiar · fuentes

El método no sale de un ramo: es una herramienta del propio orquestador. Se apoya en:

| Fuente | Qué aporta |
|---|---|
| **Bases de Datos** (ramo) | el índice antes que la lectura: una tabla de huellas (clave, tamaño, fecha, hash) decide qué hay que volver a procesar, igual que una carga incremental |
| **Visualización de la Información** (ramo) | el resumen por niveles: primero el panorama (carpetas), después el detalle (archivos) y solo lo más relevante cuando no cabe |
| graphify (herramienta abierta) | la forma del grafo (`nodes` con `id`, `label`, `type`, `source_file`; `links` con `source`, `target`, `relation`, `confidence`) para que ambos grafos se puedan fusionar |
| NetworkX, formato *node-link* | el estándar de esa forma (`directed`, `multigraph`, `graph`, `nodes`, `links`) |
| Obsidian (convención de enlaces) | los `[[wikilinks]]`, que se resuelven por ruta o por nombre único del archivo |
| Git (idea de la huella) | un cambio es un cambio de contenido (hash), no de fecha |
