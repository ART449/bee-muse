# 🐝 MEMO_BEEMUSE_BLOQUEOS

**Fecha:** 2026-11-02 · **Deadline:** 2026-11-04 20:00 Aguascalientes
Formato por tarea: `TASK_ID | NODO | RESPONSABLE | REPO@COMMIT | ESTADO | PRUEBA | EVIDENCIA | SHA256 | SIGUIENTE_ACCION`

---

## A. Bloqueos en la RUTA CRÍTICA (sin esto no hay entrega)

| TASK_ID | NODO | RESPONSABLE | REPO@COMMIT | ESTADO | PRUEBA | EVIDENCIA | SHA256 | SIGUIENTE_ACCION |
|---|---|---|---|---|---|---|---|---|
| BLK-01 | Victus | **ArT** (grabación física) + Pixel/PM (guion) | bee-muse@19ed27d | **BLOQUEADO — humano** | ¿Existe video ≤3 min reproducible? | `I:\Bee-Muse\2026-11-02\hackathon-video\capture\` vacío | — | Grabar siguiendo `MEMO_BEEMUSE_DEMO_SCRIPT.md`; cerrar antes la ventana del portable viejo (28-oct); subir a YouTube no listado/Drive; verificar link desde navegador sin sesión |
| BLK-02 | GitHub | BeeCode (PR) + **ArT** (decide licencia) | bee-muse@19ed27d | **FALLÓ — falta LICENSE** | `ls LICENSE` en el árbol | No existe LICENSE en HEAD | — | ArT elige (MIT recomendada); añadir `LICENSE` por PR a main; revisar que las 9 animaciones CyberBee/OctoHype tengan licencia compatible |
| BLK-03 | Navegador ArT | **ArT** | — | **BLOQUEADO — humano** | ¿Comprobante de envío (pantalla/email)? | `HACKATHON-SUBMISSION.md`: "DRAFT — NOT SUBMITTED" | — | Copiar drafts en inglés del packet al formulario cerebralvalley; completar equipo/encuesta con respuestas reales; leer consentimiento promocional; Submit; guardar captura + email |

**Alternativa reversible si BLK-01 se atora:** grabar solo la pantalla de Windows (OBS / Xbox Game Bar `Win+G`) con el backend compilado 0.5.0 y la biblioteca sintética de `hackathon-evidence\synthetic-library`; narración de voz después. No se necesita Pixel ni Firebase para un video honesto.

---

## B. Bloqueos de integración (NO bloquean la entrega; se declaran como roadmap)

| TASK_ID | NODO | RESPONSABLE | REPO@COMMIT | ESTADO | PRUEBA | EVIDENCIA | SHA256 | SIGUIENTE_ACCION |
|---|---|---|---|---|---|---|---|---|
| INT-01 | Paneles Meta + Firebase | **ArT** (consola) | bee-muse@19ed27d | **BLOQUEADO — secreto en consola** | login/logout real con Facebook | `META.md`: `oauth_redirect_uris: null`; Firebase `CONFIGURATION_NOT_FOUND` | — | En developers.facebook.com/apps/1747909204005226 poner redirect `https://byflow-d3a0f.firebaseapp.com/__/auth/handler`; en Firebase Auth habilitar proveedor Facebook con App ID + secreto. **Revisar antes si `byflow-d3a0f` ya sirve a ByFlow.** El secreto NUNCA por chat |
| INT-02 | Pixel 10 Pro XL | ArT + Investigator | bee-muse@df1944b | **NO VERIFICADO** | ronda física: abrir app, pulsar, arrastrar, asistente, avisos | Solo build CI + 5 tests unitarios | APK `457814a8…a83b` | Instalar `app-debug.apk`, emparejar con gateway HTTPS, registrar resultados. Si no hay tiempo: **declararlo "APK compilado, sin ronda física"** en el video |
| INT-03 | Victus | ArT | bee-muse@db5e46e | **NO VERIFICADO** | dictado con micrófono real en GUI | Solo WAV sintético transcrito | — | Probar mic en la GUI 0.5.0; si falla, mostrar en el video la transcripción del WAV con etiqueta honesta |
| INT-04 | — | BeeCode | — | **BLOQUEADO — fork correcto** | — | `HANDOFF.md`: `beecode-work` es Crush; `ART449/beecode` es app Android | — | **Fuera del hackatón.** No mezclar (candado). El bueno es el fork opencode en Debian `~/src/bee-code` |
| INT-05 | Multinodo | OctoHype | — | **NO VERIFICADO** | Muse→INBEEBOX→dispositivo end-to-end | INBEEBOX solo /health ok | — | **No mostrar en el video como funcionando.** Mencionar como arquitectura/roadmap |
| INT-06 | INSPIBEE | OctoHype | — | **NO VERIFICADO** | transferencia paquete v3 | handoff: Taildrop/SSH/SMB fallaron | — | Opcional; alternativa: `/execute` en :8002 (sin auth, LAN only) o copiar por USB. No persigue la entrega |
| INT-07 | Índice | BeeCode | bee-muse@19ed27d | **CONOCIDO** | continuidad >10 000 archivos / 12 s | `PLAN-HACKATON.md` | — | Roadmap declarado; no tocar antes del 4-nov |
| INT-08 | Visión | — | — | **NO IMPLEMENTADO** | SAM/OCR | `PLAN-HACKATON.md` | — | Roadmap; no afirmar en video ni formulario |

---

## C. Drift documental (bajo costo, alto valor de credibilidad)

| TASK_ID | NODO | RESPONSABLE | REPO@COMMIT | ESTADO | PRUEBA | EVIDENCIA | SHA256 | SIGUIENTE_ACCION |
|---|---|---|---|---|---|---|---|---|
| DOC-01 | GitHub | BeeCode (PR) | bee-muse@19ed27d | **DRIFT** | `gh repo view` | 4 docs dicen "privado"; el repo es público | — | PR que actualice `HANDOFF.md`, `META.md`, `PLAN-HACKATON.md`, `HACKATHON-SUBMISSION.md` → "público, historial escaneado y limpio el 2026-11-02" |
| DOC-02 | GitHub | Guardián | bee-muse@19ed27d | **OK** | secret-scan historial completo | 20 commits, 0 hallazgos reales | — | Ninguna. Marcar el checkbox del gate en `HACKATHON-SUBMISSION.md` |

---

## D. Lo que MEMO descarta como bloqueo (falsos positivos del handoff)

- "Builds android fallidas 2b8daff/ac8c274" → resuelto en `c1f2ece`. **No es bloqueo.**
- "ZIP demo v2 7.3 MB" → no está en esta máquina, pero **no se necesita**: la entrega real es `release-0.5.0` en I:.
- "Fallos CI Windows/macOS" → las 12 corridas más recientes son `success` salvo la ya corregida.
- "Repo público sin revisar" → historial escaneado, limpio.
