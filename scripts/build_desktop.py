"""Build the native backend on the current platform, then stage clean assets."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
DESKTOP=ROOT/'desktop'
version_args=['--version-file',str(ROOT/'scripts'/'backend-version.txt')] if sys.platform=='win32' else []
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--onefile',
    '--name','bee-muse-service','--distpath',str(DESKTOP/'backend'),
    '--workpath',str(DESKTOP/'build'/'python'),'--specpath',str(DESKTOP/'build'),
    '--collect-data','imageio_ffmpeg','--copy-metadata','imageio-ffmpeg',
    *version_args,str(ROOT/'service'/'server.py')],cwd=ROOT,check=True)
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--onefile',
    '--name','bee-muse-tools','--distpath',str(DESKTOP/'backend'),
    '--workpath',str(DESKTOP/'build'/'mcp'),'--specpath',str(DESKTOP/'build'),
    *version_args,str(ROOT/'service'/'tools_mcp.py')],cwd=ROOT,check=True)
template=DESKTOP/'library-template'
template.mkdir(parents=True,exist_ok=True)
for path in (ROOT/'service').iterdir():
    if path.suffix in ('.html','.js','.css'):shutil.copy2(path,template/path.name)
shutil.copytree(ROOT/'service'/'mascotas',template/'mascotas',dirs_exist_ok=True)
catalog={'total':0,'files':[],'drives':[],'categories':{},'generatedAt':None,'personalCount':0,'personalGroups':0,'reviewCount':0}
(template/'catalog.json').write_text(json.dumps(catalog),encoding='utf-8')
(template/'organizacion.json').write_text('{"collections":[]}',encoding='utf-8')
print('Backend and empty library template prepared for',sys.platform)
