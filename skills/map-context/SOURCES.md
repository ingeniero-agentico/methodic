# Map context · sources

The method does not come from a course: it is a tool of the orchestrator itself. It rests on:

| Source | What it contributes |
|---|---|
| **Databases** (course) | the index before the reading: a fingerprint table (key, size, date, hash) decides what has to be processed again, the same as an incremental load |
| **Information Visualization** (course) | summary by levels: first the overview (folders), then the detail (files) and only the most relevant when it does not fit |
| graphify (open tool) | the shape of the graph (`nodes` with `id`, `label`, `type`, `source_file`; `links` with `source`, `target`, `relation`, `confidence`) so both graphs can be merged |
| NetworkX, *node-link* format | the standard for that shape (`directed`, `multigraph`, `graph`, `nodes`, `links`) |
| Obsidian (link convention) | `[[wikilinks]]`, resolved by path or by the file's unique name |
| Git (the idea of the fingerprint) | a change is a change of content (hash), not of date |
| Document control (revision practice) | a document that declares which one it replaces (`Replaces:`) retires the previous one from the reading set without deleting it |
