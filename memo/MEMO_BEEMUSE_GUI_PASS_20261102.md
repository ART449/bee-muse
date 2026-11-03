# 🐝 MEMO_BEEMUSE_GUI_PASS_20261102 — pasada visual de la GUI 0.5.0 con biblioteca sintética

**Ejecutada por:** MEMO · **Cuándo:** 2026-11-02 23:41–23:53 Aguascalientes · **Nodo:** HP Victus / Windows
**Binario:** `I:\Bee-Muse\2026-11-02\release-0.5.0\Windows\Bee-Muse-win32-x64\Bee-Muse.exe` (SHA-256 `3335e3c3…91d1`, sin modificar)
**Perfil:** limpio, `BEE_MUSE_DATA_DIR` en tmp de la sesión; biblioteca = copia de `hackathon-evidence\synthetic-library`; documentos = 3 HTML sintéticos en `%LOCALAPPDATA%\Temp\beemuse-demo-docs`. **Ningún archivo personal.**
**Driver:** Playwright-python por CDP (`--remote-debugging-port=9222`) sobre la ventana real; capturas en `gui-pass/shots/`.
**Cuota Muse consumida:** 4 solicitudes (probe automático del panel, job UI #1, job UI #2, 2 reproducciones de diagnóstico → una por CLI y una por source).

## Resultado por paso del guion

| Paso del guion | Qué se hizo | Resultado | Evidencia |
|---|---|---|---|
| Arranque | exe + perfil sintético | ventana `Bee-Muse · IArtLabs · 0.5.0`, backend `bee-muse-service.exe` x2, UI en `http://127.0.0.1:59421/muse` | `01-muse-landing.png`, `02-muse-hero.png` |
| Conexión Muse | panel "Tu conexión con Muse" | `muse-wonder-1.0 · Meta`; probe real automático: **10.49 s, 16 260 in / 141 out**, "Muse respondió y la prueba cumplió el resultado esperado" | `02-muse-hero.png`, `profile/library/muse-evidence.json` |
| Biblioteca HTML (antes) | vista `/html` | 0 piezas — el `catalog.json` copiado no es el índice HTML | `03-biblioteca-html.png` |
| Indexar | `POST /api/library/index {roots:[docs]}` con token de sesión (misma llamada que hace la UI tras el diálogo nativo) | **3 HTML encontrados, 1 disco, 0 errores, "Indexación terminada"** | `06-biblioteca-indexada.png`, `index-status` JSON |
| 1·Encontrar | Apuntadora: "Demo Dos" → "Buscar mis HTML" | **1 coincidencia: "Demo Dos Sintetico"** con ruta | `07-apuntadora-resultado.png` |
| 3·Señalar | "Señalar en mi biblioteca" | navega a `/html?point=28533c71…`; tarjeta resaltada en amarillo, abejita + toast **"Aquí está: demo-dos.html"** | `08-senalado-en-biblioteca.png` |
| Carpeta de trabajo | `#workspacePath` + "Usar carpeta" | "Muse puede trabajar en la carpeta elegida con sus controles de permisos." | — |
| Muse → herramienta → archivo | chat: *"Crea un archivo llamado demo-note.txt… 'Bee-Muse demo' y dime cuánto es 17 por 23"* → "Enviar a Muse" | chat muestra **Tú / Muse: "Muse está trabajando…"**, mascota "Trabajando". **`demo-note.txt` creado en disco a las 23:46 con el contenido exacto "Bee-Muse demo"** | `09-muse-enviando.png`, `ls` del workspace |
| Respuesta en UI | sondeo del job | ⚠️ la ventana cambió sola a `/apuntadora` y se abrió una ventana "Navegador Bee-Muse"; la respuesta del job #1 no quedó visible ni persistida | lista de páginas CDP |
| Muse (2º intento, id capturado) | *"Lee demo-note.txt… y 17 por 23"* | ❌ **`state: failed` en 8 s: "La sesión no pudo completarse. Revisa el proyecto antes de repetirla."** (mensaje genérico = excepción que NO es `ValueError`) | `11-muse-respuesta-final.png`, job `774a33ad…` |
| Diagnóstico A — CLI directo | mismo comando que `converse()` (`muse-bin-1.4.14`, preset `native-basic`, MCP `bee-muse-tools.exe`) en dir persistente | ✅ **returncode 0, 9.7 s, "Bee-Muse demo", 17×23 = 391**; 2 llamadas, 55 262 in (27 508 caché) / 329 out | `gui-pass/repro/output.jsonl`, `error.txt` (solo avisos de workspace untrusted) |
| Diagnóstico B — `converse()` desde source | venv + `mcp==1.30.0`, misma biblioteca/carpeta | ✅ **OK 10.0 s: "…`Bee-Muse demo`… Y 17 por 23 es 391."** | salida del comando |
| Dictado (STT) | — | **NO probado en esta pasada** (sin WAV a mano; el panel mostraba "Muse no pudo transcribir el audio" al cargar) | — |
| Vista Hackatón | `/hackaton` | renderiza el recorrido 1·Encontrar 2·Reconocer 3·Señalar 4·Organizar; declara "no acredita inscripción ni envío" | `05-hackaton.png` |

## Veredicto de la pasada

- **Demostrable hoy, de punta a punta y con evidencia:** arranque → Muse conectado (probe real) → indexar → encontrar → señalar → Muse ejecuta una acción real en la carpeta autorizada (archivo creado).
- **Defecto real encontrado (P1 para el video):** el **backend empaquetado 0.5.0** marca el job del agente como `failed` con el mensaje genérico aunque la acción se ejecute. El CLI y el mismo código desde source responden bien → es una diferencia del entorno congelado (PyInstaller), no de Muse ni del flujo. La excepción real no se registra en ningún log (`service.log` vacío).
- **Efecto colateral observado:** tras el job #1 la ventana principal saltó a `/apuntadora` y se abrió "Navegador Bee-Muse"; no reproducido aún. Anotar para BeeCode.

## Mitigaciones para grabar el video (sin tocar el paquete)

1. **Grabar con el backend desde source** (`python run.py` o `service/server.py` con `BEE_LIBRARY_DIR`) sirviendo la UI, o la app de escritorio con `desktop/` + Electron — así la respuesta de Muse aparece en el chat. Declarar en el video que es la misma versión del código `19ed27d`.
2. O grabar con el exe 0.5.0 y mostrar **el archivo creado en el explorador** como resultado (es real), sin mostrar el mensaje de error; honestamente etiquetado "respuesta textual pendiente de corrección de empaquetado".
3. PR propuesto (`fix/muse-job-error-logging`): registrar `traceback.format_exc()` en `muse_agent.start.run` para que `service.log` muestre la causa; la build de CI resultante permitirá cerrar el bug.

## Archivos

- Capturas: `I:\Bee-Muse\2026-11-02\memo-cierre\gui-pass-20261102\shots\` (01–11)
- Reproducción CLI: `…\gui-pass-20261102\repro\` (`output.jsonl`, `error.txt`, `prompt.txt`, `response-schema.json`)
- Driver: `…\gui-pass-20261102\drive.py` (Playwright por CDP, reutilizable para la grabación)
- Workspace de demo: `%LOCALAPPDATA%\Temp\beemuse-demo-docs\` (3 HTML + `demo-note.txt`)
- La app 0.5.0 **quedó abierta** en Victus con el perfil sintético (no toca tu perfil real de `%APPDATA%\Bee-Muse`).
