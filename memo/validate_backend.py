"""Valida el backend compilado con el fix (PR #2) por su API HTTP, sin Electron."""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXE = HERE / "pkg" / "Bee-Muse-win32-x64" / "resources" / "backend" / "bee-muse-service.exe"
LIBRARY = Path(r"C:\Users\javie\.claude\jobs\94298895\tmp\gui-pass\profile\library")
WORK = Path(r"C:\Users\javie\AppData\Local\Temp\beemuse-demo-docs")
LOG = HERE / "service.log"
MESSAGE = "Lee el archivo demo-note.txt de esta carpeta y dime su contenido exacto. Despues dime cuanto es 17 por 23."

env = {**os.environ, "BEE_LIBRARY_DIR": str(LIBRARY), "PYTHONUTF8": "1"}
log = LOG.open("wb")
proc = subprocess.Popen([str(EXE), "--port", "0"], cwd=LIBRARY, env=env, stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=log, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
origin = None
buf = b""
t0 = time.monotonic()
while time.monotonic() - t0 < 45:
    chunk = proc.stdout.read1(4096) if hasattr(proc.stdout, "read1") else proc.stdout.readline()
    buf += chunk
    m = re.search(rb"http://127\.0\.0\.1:(\d+)", buf)
    if m:
        origin = "http://127.0.0.1:" + m.group(1).decode()
        break
    if proc.poll() is not None:
        break
print("backend:", origin, "| pid", proc.pid)
if not origin:
    print("NO ARRANCÓ"); sys.exit(1)


def call(route, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(origin + route, data=data, method="POST" if data else "GET")
    if data:
        req.add_header("Content-Type", "application/json")
        req.add_header("Origin", origin)  # puerta de origen local del servicio
    if token: req.add_header("X-Library-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace") or "{}")


try:
    _, s = call("/api/session"); tok = s["token"]
    print("workspace:", call("/api/muse/workspace", {"path": str(WORK)}, tok))
    st, started = call("/api/muse/start", {"message": MESSAGE, "history": []}, tok)
    print("start:", st, started)
    jid = started.get("id")
    if not jid:
        raise SystemExit("start falló: " + json.dumps(started, ensure_ascii=False))
    t1 = time.monotonic()
    while time.monotonic() - t1 < 180:
        time.sleep(2)
        _, job = call("/api/muse/job?id=" + jid, token=tok)
        if job.get("state") != "running":
            break
    print("job tras", round(time.monotonic() - t1, 1), "s:", json.dumps({k: job.get(k) for k in ("state", "error")}, ensure_ascii=False))
    if job.get("state") == "completed":
        r = job["result"]
        print("MESSAGE:", r.get("message")); print("tools:", r.get("tools"), "| workspace:", r.get("workspace"))
finally:
    proc.terminate()
    try: proc.wait(10)
    except subprocess.TimeoutExpired: proc.kill()
    log.close()
    print("=== service.log ==="); print(LOG.read_text("utf-8", "replace")[-1500:] or "(vacío)")
    time.sleep(1)
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq bee-muse-tools.exe"], capture_output=True, text=True)
    print("bee-muse-tools huérfanos:", sum(1 for l in r.stdout.splitlines() if "bee-muse-tools" in l))
