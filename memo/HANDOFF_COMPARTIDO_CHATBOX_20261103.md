# HANDOFF COMPARTIDO · MEMO + CODEX + CLAUDIO + OCTOHYPE · 2026-11-03 08:52

**Base:** checkpoint inmutable `2026-11-03_0847_cierre-hackaton-bee-muse-ensayo.md` (mismo directorio / MEMO_RACK). Art lo declara handoff para los cuatro: lo que falta se hace entre todos, sin retrasar video, LICENSE y formulario (deadline 2026-11-04 20:00).

## Requisito elemental de Art: CHATBOX CENTRALIZADO
Un solo hilo en Bee-Muse con todas las funciones: buscar e indexar (HTML y todos los tipos), señalar con la abejita, Muse (texto y dictado), tarjetas con previews aislados, navegador Bee-Muse, estado de Android/gateway e INBEEBOX, mascota viva junto a los mensajes. Componer sobre lo existente (/muse de PR #5, /apuntadora, /archivos, APIs y MCP); nunca reescribir.

## Reparto (folio INBEEBOX `task-beemuse-chatbox-20261103`, msgs 02b9fb/#general y 8c5a4b/#ops)
| ID | Dueño | Qué |
|---|---|---|
| CB-CODEX-1 | CODEX | rama `feat/chatbox-central` desde `feat/chat-visual-mvp`: comandos naturales + botones rápidos (indexa, busca, señala, dicta, abre navegador, estado android, estado colmena) reutilizando endpoints; resultado como tarjeta; historial persistente; tests + capturas |
| CB-CLAUDIO-1 | CLAUDIO | Guardián: token+Origin, sin rutas nuevas de escritura, previews solo sandbox, sin XSS; revisa el PR |
| CB-OCTOHYPE-1 | OCTOHYPE | regresión de las 4 vistas tras cada commit (unittest + visual_mvp.py), hashes release vs rama, inconsistencias a #forense |
| CB-MEMO-1 | MEMO | coordinar, evidencias, LICENSE + README hoy, video y formulario; veto: nada a main/RC sin ensayo verde |

## Cómo acusar
POST `http://127.0.0.1:8002/channels/general/messages` (X-API-Key del archivo local, trilineal) citando el id de tarea y la hora. Sesiones sin acceso al hub: relevo por Art a MEMO (como hizo CLAUDIO).
