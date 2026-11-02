"""Run the local Bee-Muse service with isolated, persistent user data."""
import argparse
import os
from pathlib import Path
import runpy
import shutil
import sys
import threading
import webbrowser

ROOT=Path(__file__).resolve().parent


def default_data():
    if os.name=='nt':return Path(os.environ['APPDATA'])/'Bee-Muse'
    if sys.platform=='darwin':return Path.home()/'Library'/'Application Support'/'Bee-Muse'
    return Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local'/'share')))/'Bee-Muse'


def prepare(target):
    target=Path(target).resolve()
    target.mkdir(parents=True,exist_ok=True)
    for source in (ROOT/'service').iterdir():
        if source.suffix in ('.html','.css','.js'):
            shutil.copy2(source,target/source.name)
    shutil.copytree(ROOT/'service'/'mascotas',target/'mascotas',dirs_exist_ok=True)
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Bee-Muse · servicio local de IArtLabs')
    parser.add_argument('--library',type=Path)
    parser.add_argument('--port',type=int,default=8767)
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('Puerto inválido.')
    # Reuse an existing configured library without copying private state into source.
    location=args.library
    if location is None:
        import json
        try:location=Path(json.loads((default_data()/'desktop.json').read_text(encoding='utf-8'))['library'])
        except (OSError,ValueError,KeyError,TypeError):location=default_data()/'library'
    target=prepare(location)
    os.environ['BEE_LIBRARY_DIR']=str(target)
    sys.path.insert(0,str(ROOT/'service'))
    if args.open:
        timer=threading.Timer(1.5,lambda:webbrowser.open('http://127.0.0.1:'+str(args.port)+'/muse'))
        timer.daemon=True;timer.start()
    sys.argv=[str(ROOT/'service'/'server.py'),'--port',str(args.port)]
    runpy.run_path(str(ROOT/'service'/'server.py'),run_name='__main__')
