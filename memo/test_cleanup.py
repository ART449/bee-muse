"""Prueba sin cuota: ¿un hijo onefile (bee-muse-tools.exe) que hereda error.txt
impide limpiar el TemporaryDirectory cuando se mata al bootloader (como hace Muse)?"""
import subprocess
import tempfile
import time
import traceback
from pathlib import Path

TOOLS = r"I:\Bee-Muse\2026-11-02\release-0.5.0\Windows\Bee-Muse-win32-x64\resources\backend\bee-muse-tools.exe"
LIB = r"C:\Users\javie\.claude\jobs\94298895\tmp\gui-pass\profile\library"
FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def scenario(label, kill_delay_before_cleanup):
    print(f"--- {label}")
    try:
        with tempfile.TemporaryDirectory(prefix='bee-muse-agent-') as tmp:
            root = Path(tmp)
            with (root / 'output.jsonl').open('w+b') as out, (root / 'error.txt').open('w+b') as err:
                # Igual que Muse: el MCP hereda stderr; stdin/stdout por pipe.
                p = subprocess.Popen([TOOLS, '--library', LIB], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=err, creationflags=FLAGS)
                time.sleep(3)  # dejar que el bootloader extraiga y arranque al hijo Python
                p.kill()       # Muse mata al bootloader al terminar
                p.wait(5)
            time.sleep(kill_delay_before_cleanup)
        print("cleanup OK")
    except Exception as e:
        print("CLEANUP FAILED:", type(e).__name__, str(e)[:200])
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq bee-muse-tools.exe'], capture_output=True, text=True)
    survivors = [l for l in r.stdout.splitlines() if 'bee-muse-tools' in l]
    print("procesos bee-muse-tools vivos tras el kill:", len(survivors))
    for l in survivors:
        print("  ", l.strip())


scenario("A: limpiar inmediatamente tras matar (como converse())", 0)
time.sleep(4)
scenario("B: esperar 3 s antes de limpiar", 3)
