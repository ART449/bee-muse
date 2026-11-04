"""Start the packaged backend against an empty library and check /health; works on every OS."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'desktop'/'backend'/('bee-muse-service.exe' if sys.platform=='win32' else 'bee-muse-service')
TEMPLATE=ROOT/'desktop'/'library-template'
STARTUP_SECONDS=float(os.environ.get('BEE_SMOKE_TIMEOUT','10'))
URL_PATTERN=re.compile(r'http://127\.0\.0\.1:(\d+)')


def wait_for_url(process,captured):
    """Read stdout on a thread so a silent binary cannot block the step forever."""
    def pump():
        for line in process.stdout:
            captured.append(line)
    threading.Thread(target=pump,daemon=True).start()
    deadline=time.monotonic()+STARTUP_SECONDS
    while time.monotonic()<deadline:
        match=next((URL_PATTERN.search(line) for line in captured if URL_PATTERN.search(line)),None)
        if match:return int(match.group(1))
        if process.poll() is not None:break
        time.sleep(0.2)
    return None


def check_health(port):
    with urlopen(f'http://127.0.0.1:{port}/health',timeout=5) as response:
        payload=json.loads(response.read().decode('utf-8'))
    if not isinstance(payload,dict) or 'app' not in payload:
        raise SystemExit('Unexpected /health payload: '+json.dumps(payload))
    return payload


def main():
    if not BINARY.is_file():raise SystemExit('Packaged backend not found: '+str(BINARY))
    if not TEMPLATE.is_dir():raise SystemExit('Library template not found: '+str(TEMPLATE))
    # Keep the child's cwd outside the temp dir so Windows can delete it afterwards.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
        library=Path(scratch)/'library'
        shutil.copytree(TEMPLATE,library)
        env={**os.environ,'BEE_LIBRARY_DIR':str(library)}
        process=subprocess.Popen([str(BINARY),'--port','0'],cwd=ROOT,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        captured=[]
        try:
            port=wait_for_url(process,captured)
            if port is None:
                raise SystemExit('Backend did not announce http://127.0.0.1:<port> within %.0fs. Output:\n%s'%(STARTUP_SECONDS,''.join(captured)))
            payload=check_health(port)
            print('Smoke OK on port',port,'->',json.dumps(payload))
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)


if __name__=='__main__':main()
