# 🐝 MEMO_BEEMUSE_DEMO_SCRIPT — video 3:00

**Regla de oro:** cada segundo muestra algo que **ya está verificado** (ver `MEMO_BEEMUSE_EVIDENCIAS.md`). Lo no verificado se dice con la palabra "roadmap", nunca se simula.
**Datos:** solo biblioteca sintética (`I:\Bee-Muse\2026-11-02\hackathon-evidence\synthetic-library`) y el ejecutable **0.5.0** de `release-0.5.0\Windows\Bee-Muse-win32-x64`.
**Antes de grabar:** cerrar la ventana del portable viejo (28-oct); NO matar procesos Electron auxiliares a ciegas. Nada de archivos personales, sesiones, tokens ni cuenta de Windows en pantalla.
**Idioma:** narración en inglés (jurado), UI puede estar en español — decirlo en voz alta en 0:05.

---

## Preparación (fuera de cámara, ~10 min)

1. Abrir `Bee-Muse-win32-x64\Bee-Muse.exe` con perfil limpio apuntando a la biblioteca sintética.
2. Tener listo un archivo WAV sintético (el de `compiled-voice-proof`) para el tramo STT.
3. Tener una terminal con `python -m unittest discover -s tests -v` ya ejecutado y visible (18 OK) para mostrar en 2:15.
4. Tener la página de GitHub `ART449/bee-muse` abierta en la pestaña de commits.
5. Grabador: OBS o `Win+G`. 1080p. Cursor visible.
6. Mascotas CyberBee/OctoHype: aparecen solas como estados de la app (idle/running/review); **no** añadir overlays extra.

---

## Guion

### 0:00–0:30 · Problema
> "Finding the right file in a large personal library, and then asking an AI to *do something* with it, usually means copying paths around and trusting the model blindly. Bee-Muse is a local, permission-scoped workspace: Meta Muse is the brain, Bee-Muse gives it reusable tools, and every action leaves a verifiable trace."

**Pantalla:** app 0.5.0 abierta, biblioteca sintética cargada, mascota en idle.

### 0:30–1:00 · Arquitectura
> "Three layers. A local index and version-aware library. A conversation backed by Muse Code — model `muse-wonder-1.0`. And an MCP tool interface that Muse — or any other agent — can query. Desktop on Windows, Linux and Mac; a native Android client that compiles in CI."

**Pantalla:** `MCP.md` o un diagrama simple; luego `service/muse_bridge.py` 2 s con el nombre del modelo.

### 1:00–2:15 · Demo real del flujo (el corazón)
**Usuario → Muse → Bee-Muse → herramienta → acción controlada → resultado → evidencia**

1. **(1:00)** Escribir: *"Find the HTML file in my library about [término del catálogo sintético]"*.
   > "Muse calls the `search_html` tool through MCP. It gets the exact file name from the index — it never walks the disk."
   **Pantalla:** respuesta con el nombre exacto; mostrar el log de la herramienta. *(Verificado: RP-03)*

2. **(1:25)** Escribir: *"Create a file called demo-note.txt in the temp folder with the text 'Bee-Muse demo' and tell me 17×23."*
   > "A real write — but only into a path the user authorized. Arbitrary paths are refused."
   **Pantalla:** archivo creado + respuesta 391. Abrir el archivo en el explorador. *(Verificado: RP-02)*

3. **(1:50)** Subir el WAV sintético al dictado.
   > "Meta's voice transcription, through the compiled Windows backend. Speech-to-text only — spoken replies use the system voice, not Meta TTS."
   **Pantalla:** transcript "Hola, esta es una prueba de voz de Bemius." *(Verificado: EV-06)*
   Si el mic real no está probado: **no usar mic**; usar el WAV.

### 2:15–2:45 · Evidencias
> "Eighteen automated tests, no model quota. CI green on Windows, Linux, macOS and Android. Release 0.5.0 with SHA-256 receipts. Full git history secret-scanned before going public."

**Pantalla:** terminal con 18 OK → pestaña Actions en verde → `release-validation.json` con el SHA del APK.

### 2:45–3:00 · Alcance honesto y cierre
> "What's built during the event: Muse conversations, MCP tools, the native Android client, the isolated browser, the voice decoder fix and the portable release — commits `d85ecf1` to `5807c65` on top of a recovered baseline. Roadmap, not yet verified: Facebook login, physical Android round, visual understanding. Bee-Muse: tools for AI, not another AI."

**Pantalla:** lista de commits en GitHub; cerrar con la mascota en `review`.

---

## Qué NO decir ni mostrar
- Que el login con Facebook funciona (OAuth sin cerrar).
- Gestos/asistente en el Pixel como probados (solo compila).
- Orquestación multinodo Muse→INBEEBOX→dispositivo como funcionando (solo /health).
- SAM/OCR/visión.
- Que todo se construyó durante el evento (la base `f50750b` es recuperada).

## Post-grabación
1. Reproducir completo; comprobar ≤3:00 y texto legible.
2. Guardar en `I:\Bee-Muse\2026-11-02\hackathon-video\capture\bee-muse-demo-v1.mp4` y calcular SHA-256 → anotarlo en `MEMO_BEEMUSE_RELEASE_MANIFEST.json`.
3. Subir (YouTube no listado o Drive público). Abrir el link desde una ventana de incógnito.
4. Pegar el link en el formulario.
