# RELEVO · Informe de observabilidad de agentes (GO-EXP-COLMENA-OBS-001)

**Procedencia:** pegado por ArT en la sesión de MEMO el 2026-11-03 (~02:10 Aguascalientes). **Autor no identificado** en el texto (dice "Primer informe"); no verificado contra ninguna sesión ni canal. Tratar como RELEVO, no como evidencia.
**Naturaleza:** revisión documental + propuesta; el propio informe declara "prueba propuesta; no ejecutada" y "no he inspeccionado el sistema".
**Relación con el hackatón Bee-Muse:** ninguna directa. **Prioridad asignada por MEMO: P2, después del 2026-11-04 20:00.**

## Lo que vale la pena conservar

1. Separar siempre: identidad del agente · instancia en ejecución · evidencia de sus acciones.
2. Esquema de evento propuesto para CCP/INBEEBOX: `agent_id, instance_id, run_id, task_id, event_id, parent_event_id, catalog_version, context_version, action, result, evidence_ref`. Hoy un mensaje INBEEBOX lleva `sender`, `channel`, `task_id` solo dentro del texto (protocolo `inbeebox-task/1`).
3. Para efectos compartidos: reserva temporal + número de generación + clave de idempotencia.
4. Experimento sintético reproducible (100 semillas, control vs tratamiento, 6 escenarios con criterios fijados de antemano, JSONL + CSV + manifiesto SHA-256). Reversión: borrar la carpeta del experimento.

## Observación de MEMO

- El caso "nombre fuera de catálogo" ya ocurrió hoy: INBEEBOX rechazó mencionar a CLAUDIO/CODEX porque no están en el roster, aunque existen mensajes antiguos firmados por ellos. Coincide con la tesis del informe.
- Las referencias (Soei 2026-10-29, VerifyMAS v3 2026-10-30, TraceElephant ACL 2026, AcMAS ICML 2026, Who&When ICML 2025) NO fueron comprobadas por MEMO.

## Texto íntegro relevado

(ver `RELEVO_INFORME_OBS_COLMENA_20261103.txt` junto a este archivo)
