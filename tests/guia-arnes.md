# Arnés de la guía de primer uso

Prueba de lógica de `service/guia.js` sin la app: blancos falsos, secuencia completa (permiso → paso 1 → clic real → paso 2 → cancelación por mouse → Esc → Saltar → sin blancos). Corre en Chrome headless con tiempo virtual; no sustituye el recorrido a mano en el perfil de revisión.

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-first-run --user-data-dir="$env:TEMP\bm-guia-ud" --window-size=1280,900 --virtual-time-budget=15000 --dump-dom "file:///RUTA/AL/REPO/tests/guia-arnes.html" | Select-String -Pattern "^[a-z_0-9]+=" -AllMatches
```

Con `--force-prefers-reduced-motion` el cursor aparece directo en cada blanco; en ese modo mover el mouse no cancela (no hay viaje), solo Esc y "Saltar guía". Esperado: `detenida_por_esc=true`, `detenida_por_saltar=true`, `marca_guardada=1`, `FIN=true`, y con blancos presentes `detenida_por_mouse=true` en el modo normal.
