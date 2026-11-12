# 🐝 EXPLORER_AUDITORIA_20261103 — BASE del handoff "Explorador inteligente"

**Handoff:** HANDOFF-MEMO-BEEMUSE-EXPLORER-20261103-001 · **Prioridad:** P1 subordinada al hackatón (deadline 2026-11-04 20:00)
**Auditoría:** solo lectura sobre `main` = `ca0fb99`, 2026-11-03 ~03:15 Aguascalientes (subagente Explore + MEMO). **Nada modificado.**
**Checkpoint reversible:** rama `feat/explorador-inteligente` = `ca0fb99` (publicada, 0 cambios). Hashes SHA-256 (16 primeros) en `main`: `html_indexer.py cc9437ee5893802a` · `file_catalog.py 90ccb4af0639aa56` · `folder_library.py 487e4289347775b8` · `index.html 6ff32ca00017d55b` · `archivos.js 1f5cb852c4a39cf0` · `carpetas.js c2c65c2159582814` · `tools_mcp.py 3a9ef64b4c4624fa`.

## Correcciones de hecho al handoff
- "10 000 archivos / 12 s" es el límite del **índice general** (`folder_library.walk`, :97), no del HTML. El índice HTML corta en 10 000 HTML, 200 000 entradas o **90 s** (`html_indexer.py:16-18`).
- La ruta `/` sirve **Mis archivos** (`archivos.html`, `server.py:136`); la biblioteca HTML está en `/html` (`server.py:213`).

## Componentes existentes (evidencia)
| Componente | Archivo:línea | Qué hace | Límite observado |
|---|---|---|---|
| `/`, `/archivos` (Mis archivos) | server.py:136 | todas las extensiones | 120 resultados en UI |
| `/html` (Biblioteca HTML) | server.py:213 | catálogo HTML | 12 por página (server.py:256) |
| `/carpetas` | server.py:182 | navegar, indexar, buscar, mover, versiones | 1000 entradas/carpeta (folder_library.py:80) |
| Indexador HTML | html_indexer.py:46-105 | hilo + os.scandir, catalog.json atómico | 10 000 HTML / 200 000 entradas / 90 s; lee ≤64 MB total, archivos ≤2 MB |
| Raíces HTML | html_indexer.py:23-36 | 1–12 raíces; rechaza UNC, symlink, reparse, BASE, SKIP | 12 raíces |
| Estado índice HTML | html_indexer.py:13,20; server.py:140 | `/api/library/index-status` | **sin cancelación** |
| Índice general | folder_library.py:89-129 | SQLite `indice-carpetas.sqlite`: files(path, root, kind, bytes, modified), scans | 10 000 archivos o 12 s por raíz |
| Inventario Mis archivos | file_catalog.py:14-36; server.py:142 | subcadena AND en ruta + categoría SQL `file_kind`; orden modified | limit ≤50 000 (120 default); 12 términos |
| Búsqueda Carpetas | folder_library.py:139-147; server.py:188 | subcadena en ruta, modified DESC | 100 resultados |
| `/api/catalog` | server.py:224-258 | q, drive, category, collection; orden newest/name/size; dedupe por group | página 12 |
| Versiones HTML | server.py:269-278, 410-417; version_store.py | copias exactas (sha256), variantes, snapshots con manifiesto | snapshot ≤2 MB, no nube |
| Snapshot carpeta | folder_library.py:193-236 | ZIP + sha256 por archivo + diff | 500 archivos / 50 MB; plan caduca 300 s |
| Mover carpeta | folder_library.py:154-191 | plan (vista previa) → apply (os.rename) → undo | mismo disco; sin sobrescribir; rutas protegidas (:29-33) |
| MCP | tools_mcp.py:177-223 | library_status, search_html, search_files, indexed_file, read_indexed_text, inbeebox_* | limit ≤100; 250 000 filas / 5 s; 64 000 chars |
| Android | MainActivity.java:65-66 | SAF por sufijo, abre con Intent; sin índice | 5000 entradas |

## Existe vs falta (contra los criterios del handoff)
| Requisito | Estado | Evidencia |
|---|---|---|
| Búsqueda por nombre/ruta | **EXISTE** (subcadena, sin ranking) | file_catalog.py:20; server.py:241 |
| Parcial / exacta | PARCIAL (solo "contiene"; exacta solo por id) | — |
| Filtro por extensión | **FALTA en UI web** (existe en MCP `search_files` y Android) | tools_mcp.py:68-85 |
| Orden tamaño/fecha/nombre | EXISTE solo en Biblioteca HTML; Mis archivos solo fecha; **por tipo FALTA** | index.html:17 |
| Multi-disco | PARCIAL: Windows enumera discos; Linux solo `home`; Mis archivos sin filtro de disco | folder_library.py:12-16 |
| Conteo y espacio usado | conteos sí; **suma de espacio FALTA** | — |
| Indexación incremental | **FALTA** (recorrido completo y reemplazo; sin reanudación) | PLAN-HACKATON.md:29 |
| Cancelación | **FALTA** | — |
| Control de RAM | PARCIAL (presupuestos 64 MB/2 MB; pero `walk` acumula en memoria y catálogo HTML entero en RAM) | server.py:48 |
| Categorías configurables | **FALTA** (KINDS fijo: photos, documents, media, code, other) | file_catalog.py:10 |
| Duplicados por hash | EXISTE solo HTML ≤2 MB; **FALTA en Mis archivos** | html_indexer.py:85 |
| Archivos grandes | PARCIAL (orden "Mayor tamaño" en HTML) | — |
| Agrupación por proyecto | EXISTE para HTML (project = carpeta padre; colecciones) | library_chat.py:62-82 |
| Reportes de espacio | **FALTA** | — |
| Modo claro/oscuro | **FALTA** (solo oscuro fijo) | iart-theme.css:2 |
| Navegación por teclado | MÍNIMA (skip-link, Escape, Enter; sin flechas/atajos) | index.html:14,57,78 |
| No borrar sin autorización | **CUMPLE** (no existe borrar/copiar/mover entre discos; mover = plan→apply→undo) | folder_library.py:166 |
| Conserva búsqueda HTML original | **CUMPLE** (ruta `/html` intacta) | server.py:213 |

## Portabilidad
- `roots()` Windows = `GetLogicalDrives`; Linux = solo `Path.home()` (sin /mnt, /media). Rutas protegidas solo Windows. `valid_name` aplica nombres reservados Windows en todos los SO. `st_file_attributes` no existe en POSIX. Jules exige Windows.
- Android: SAF sin permisos globales, sin índice persistente.

## Tests existentes / huecos
Cubren: búsqueda y lectura de seleccionados, todas las extensiones (+ exclusión .env), límites y tipos, >50 000 registros, symlink, cliente MCP. **No hay tests** de `html_indexer` (límites, parcial, SKIP, dedupe), de `walk`, de plan/apply de movimientos, ni de orden/paginación de `/api/catalog`.

## Plan P1 propuesto (rama `feat/explorador-inteligente`, sin tocar la RC)
1. **Motor** (`folder_library.py` + `file_catalog.py`): añadir columna `drive` y `sha256` (opcional, lazy, ≤N MB) al SQLite; filtros por extensión, rango de tamaño y fecha; orden por tamaño/nombre/tipo; `SUM(bytes)` por raíz/disco/categoría; **cancelación** (flag compartido leído por `walk`) y recorrido **incremental** (comparar `modified`/`bytes` con la tabla `scans`).
2. **Categorías configurables**: `categorias.json` en la biblioteca con la tabla del handoff (código/web, agentes/docs, sistema, comprimidos, juegos, 3D, multimedia, documentos, otros); `file_kind` lee ese archivo; un archivo puede caer en varias.
3. **UI Mis archivos** (`archivos.html/js`): barra superior (buscador, disco/carpeta, filtros rápidos, estado de indexación), panel lateral por categoría + Duplicados + Grandes, tabla (nombre, ext, tamaño, ruta, fecha, categoría, estado), panel inteligente (resumen de espacio, recuperable, relacionados, recomendaciones con riesgo). `prefers-color-scheme` + alternador; navegación con flechas/atajos.
4. **Inteligencia** (P2): duplicados por hash en todos los tipos, archivos grandes, relación por proyecto, reportes de espacio, recomendaciones explicadas vía Muse/MCP. **Nunca borrar**; toda acción = plan → vista previa → riesgo → apply → undo (patrón ya existente).
5. **Experimento** (GO_EXPERIMENTO): dataset sintético, índice frío/caliente, métricas (tiempo de indexación, latencia, RAM pico, CPU, precisión de clasificación, duplicados, errores de permisos, reversiones) con logs + capturas + hashes. Sin comparar con Everything salvo medición reproducible.
6. **Portabilidad** (P3): `roots()` Linux (/mnt, /media, montajes), rutas protegidas POSIX, tests por SO; Android: evaluar MediaStore/SAF con índice local.

**Responsables (roster INBEEBOX real):** MEMO coordinación · CODEX (rol BeeCode) implementación · CLAUDIO auditoría/seguridad (rol Guardián) · ArT QA/UX.
