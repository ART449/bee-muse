"""Create portable bundles before artifact upload loses modes and symlinks."""
import hashlib
import json
from pathlib import Path
import platform
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ready=ROOT/'desktop'/'ready'
output=ROOT/'desktop'/'release'
output.mkdir(parents=True,exist_ok=True)
folders=sorted(p for p in ready.iterdir() if p.is_dir() and p.name.startswith('Bee-Muse-'))
if not folders:raise SystemExit('No packaged Bee-Muse application was found.')
system=platform.system()
label='macOS' if system=='Darwin' else system
arch='arm64' if platform.machine().lower() in ('arm64','aarch64') else 'x64'
version=json.loads((ROOT/'desktop'/'package.json').read_text(encoding='utf-8'))['version']
name='Bee-Muse-'+version+'-'+label+'-'+arch
if system=='Windows':
    archive=output/(name+'.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        for folder in folders:
            for file in sorted(folder.rglob('*')):
                if file.is_file():bundle.write(file,file.relative_to(ready))
else:
    archive=output/(name+'.tar.gz')
    with tarfile.open(archive,'w:gz',dereference=False) as bundle:
        for folder in folders:bundle.add(folder,arcname=folder.name)
with archive.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
archive.with_name(archive.name+'.sha256').write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
print('Portable bundle:',archive.name)
