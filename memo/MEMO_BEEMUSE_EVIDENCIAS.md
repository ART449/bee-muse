# 🐝 MEMO_BEEMUSE_EVIDENCIAS

**Fecha:** 2026-11-02 · Todo lo listado fue **verificado directamente en esta sesión** salvo donde se marque "(reportado por el repo)".

---

## 1. Verificado por MEMO esta sesión (primera mano)

| EVID_ID | Qué | Cómo se verificó | Resultado | SHA256 / identificador |
|---|---|---|---|---|
| EV-01 | Repo `ART449/bee-muse` público | `gh api repos/ART449/bee-muse` | `visibility: public`, `private: false`, creado 2026-11-02T04:05:06Z, push 2026-11-03T03:08:19Z | HEAD `19ed27d` |
| EV-02 | Historial sin secretos | Subagente security-reviewer: `git grep` sobre `rev-list --all` (20 commits) + listado de todos los paths históricos | **LIMPIO.** 0 credenciales, 0 `.env`, 0 keystore/jks/pem, `firebase-web.json` nunca presente. Único match: `service/chingaquedito.py:45` = lista de prefijos detectores, no un secreto | 20 commits escaneados |
| EV-03 | CI real (12 corridas más recientes) | `gh run list --repo ART449/bee-muse` | 11 `success` + 1 `failure` (`41509772891`, `ac8c274`) corregida en `41510052508` | ver tabla §3 |
| EV-04 | APK Android 0.5.0 íntegro | `sha256sum I:\Bee-Muse\2026-11-02\release-0.5.0\Android\app-debug.apk` | **Coincide** con `release-validation.json` | `457814a8de1a06dd625d3dae54993e29da18e8edb9469a741dced77fbd47a83b` |
| EV-05 | Release 0.5.0 completo en I: | `find release-0.5.0` | Android/, Desktop/{Linux-X64, Windows-X64, macOS-ARM64}, Windows/ extraído, LEEME.txt, release-validation.json, compiled-voice-proof.json | source desktop `5807c659dfef2681d5f3bb407874635ce2f93505`, android `df1944bd246381ada8958ac534eaaa7cabc8f087` |
| EV-06 | Backend Windows compilado + STT Meta | lectura de `compiled-voice-proof.json` | `packagedBackendStarted: true`, `emptyLibrary: true`, `metaVoiceTranscribed: true`, transcript "Hola, esta es una prueba de voz de Bemius." | packageSource `5807c65…3505` |
| EV-07 | Video NO grabado | `find I:\…\hackathon-video -type f` + `ls capture/` | `capture/` vacío; 0 archivos .mp4/.webm/.mov en todo I:\Bee-Muse | — |
| EV-08 | Evidencia de demo ya capturada | `ls I:\…\hackathon-evidence\` | `web-muse.html` (5 425 B), `web-archivos.html` (4 969 B), `prueba-catalogo.json`, `synthetic-library/`, `service-8877.log` | fechas 2-nov 20:52–23:03 |
| EV-09 | Repo android es solo spec | `git log` local + README | 1 commit `8082e24`; README: "specification only" | — |
| EV-10 | ZIPs de Downloads | `ls -la` + `sha256sum` | 10 copias idénticas de 3 168 B / 3 archivos; NO es el ZIP de 7.3 MB | `471d25ea18988303cd337fcfc4b113ef3e6422d4258b1980e400ec1d2d90fa28` |
| EV-11 | LICENSE ausente | `ls` raíz del clon `19ed27d` | No existe LICENSE | — |
| EV-12 | Disco I: accesible | `ls /i/Bee-Muse/2026-11-02` | Escrituras del 2-nov hasta 23:03; sin errores E/S hoy | — |

## 2. Reportado por el repo (VALIDATION.md / HANDOFF.md) — NO re-ejecutado por MEMO

| EVID_ID | Qué | Fuente | Nota |
|---|---|---|---|
| RP-01 | 18 pruebas automatizadas aprobadas | `VALIDATION.md` | Reproducible: `pip install -r requirements-mcp.txt && python -m unittest discover -s tests -v` (sin cuota) |
| RP-02 | Prueba real Muse: creó archivo + cálculo | `VALIDATION.md`, `HANDOFF.md` | Evidencia local `runtime/live-probe-windows.json` (gitignored). Reproducible: `python scripts/verify_real_muse.py` (consume cuota) |
| RP-03 | Muse + MCP `search_html` devolvió archivo exacto | `VALIDATION.md` | — |
| RP-04 | INBEEBOX `/health` → `status: ok`, `service: inbeebox-api` | `VALIDATION.md` | Solo salud; no circuito completo |
| RP-05 | Navegador aislado desktop (example.com, rechaza esquemas locales) | `VALIDATION.md` | Script `scripts/verify_browser.cjs` |
| RP-06 | App Meta `1747909204005226` registrada, portfolio IArtLabs, FB_LOGIN | `META.md` | Confirmado por lecturas MCP posteriores (según el repo) |
| RP-07 | 3 paquetes desktop descargados y SHA-256 comprobados, 14 symlinks Mac | `VALIDATION.md` | Coherente con `release-validation.json` (EV-05) |
| RP-08 | Traslado a I: con recibos | `HANDOFF.md` | `I:\Bee-Muse\2026-11-02\verified-moves.json` existe (EV-12) |

## 3. Corridas CI (estado consultado 2026-11-02 ~23:20 local)

| Run ID | Workflow | Commit | Estado |
|---|---|---|---|
| 41514484719 | Build and test Bee-Muse | `5807c65` build: portable bundles | success |
| 41513553354 | Build and test Bee-Muse | `db5e46e` fix(voice) | success |
| 41512152076 | Build Bee-Muse Android | `df1944b` | success |
| 41512152029 | Build and test Bee-Muse | `df1944b` | success |
| 41511899607 / 41511899465 | Android / Desktop | `6440c19` | success / success |
| 41511118741 / 41511118490 | Android / Desktop | `ab46c9b` | success / success |
| 41510052508 | Build Bee-Muse Android | `c1f2ece` fix notificaciones | success |
| **41509772891** | Build Bee-Muse Android | **`ac8c274`** | **failure** (corregido en el siguiente) |
| 41500896693 | Build and test Bee-Muse | `7ee7de5` | success |

## 4. Candado cumplido

Ninguna prueba fue simulada ni inventada. Lo que MEMO no pudo ejecutar (ronda Pixel, mic real, login Facebook, circuito INBEEBOX) queda **NO VERIFICADO**, no "OK".
