"""Local folder explorer, bounded index, reviewed moves and content snapshots."""
import ctypes,datetime as dt,hashlib,json,os,re,sqlite3,threading,time,uuid,zipfile
from contextlib import contextmanager
from pathlib import Path

LOCK=threading.RLock()
PLANS={}
SKIP={'.git','node_modules','__pycache__','.venv','venv','vendor','.cache','.rustup','.gradle','.cargo','$recycle.bin','system volume information','windows','program files','program files (x86)','programdata','appdata'}
PRIVATE={'.env','auth.json','credentials.json','token.json','id_rsa','id_ed25519'}
MAX_FILES=500;MAX_BYTES=50*1024*1024

def roots():
    if os.name=='nt':
        mask=ctypes.windll.kernel32.GetLogicalDrives()
        return [str(Path(chr(65+i)+':/')) for i in range(26) if mask&(1<<i)]
    return [str(Path.home())]

def path(value,base,write=False,parent=False):
    if not isinstance(value,str) or len(value)>1500:raise ValueError('Ubicación no válida.')
    p=Path(value)
    if not p.is_absolute() or str(p).startswith(('\\\\','//')):raise ValueError('Elige una carpeta de un disco conectado.')
    # Resolve the exact target and reject reparse points rather than following them for writes.
    if write:
        for part in [p,*p.parents]:
            if part.exists() and getattr(part.lstat(),'st_file_attributes',0)&0x400:
                raise ValueError('No se mueven carpetas a través de enlaces o uniones.')
    p=p.resolve(strict=True)
    if not any(p.is_relative_to(Path(r).resolve()) for r in roots()):raise ValueError('Ubicación fuera de los discos permitidos.')
    if write:
        protected=[base.resolve()]
        if os.name=='nt':protected += [Path(os.environ.get('WINDIR','C:/Windows')).resolve(),Path('C:/Program Files').resolve(),Path('C:/Program Files (x86)').resolve(),Path('C:/ProgramData').resolve()]
        if (not parent and p==Path(p.anchor)) or any(p==v or p.is_relative_to(v) or (not parent and v.is_relative_to(p)) for v in protected) or any(x.lower().startswith('.') or x.lower() in SKIP for x in p.parts[1:]):
            raise ValueError('Esta ubicación está protegida. Elige una carpeta de trabajo propia.')
    return p

def read_events(base):
    try:return json.loads((base/'movimientos.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):return []

def write_events(base,events):
    target=base/'movimientos.json';temp=base/'movimientos.tmp'
    temp.write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temp,target)

def events(base):
    with LOCK:
        rows=read_events(base);changed=False
        for e in rows:
            if e['state']!='planned':continue
            source=Path(e['source']);target=Path(e['target'])
            if not source.exists() and target.exists() and target.stat().st_ino==e['inode']:e['state']='done'
            else:e['state']='failed'
            changed=True
        if changed:write_events(base,rows)
        return rows

def remap(value,base):
    p=Path(value)
    for e in events(base):
        if e['state']=='done' and p.is_relative_to(Path(e['source'])):p=Path(e['target'])/p.relative_to(Path(e['source']))
    return str(p)

def aliases(base):
    return [(Path(e['source']),Path(e['target'])) for e in events(base) if e['state']=='done']

def mapped(value,moves):
    p=Path(value)
    for source,target in moves:
        if p.is_relative_to(source):p=target/p.relative_to(source)
    return str(p)

def browse(base,value='',show_hidden=False):
    if not value:return {'roots':roots(),'path':'','parent':None,'entries':[],'truncated':False}
    p=path(value,base)
    if not p.is_dir():raise ValueError('Elige una carpeta.')
    items=[];count=0
    with os.scandir(p) as listing:
        for entry in listing:
            if not show_hidden and (entry.name.startswith('.') or entry.name.lower() in SKIP):continue
            count+=1
            if len(items)>=1000:continue
            try:
                st=entry.stat(follow_symlinks=False);link=bool(getattr(st,'st_file_attributes',0)&0x400) or entry.is_symlink()
                items.append({'name':entry.name,'path':entry.path,'directory':entry.is_dir(follow_symlinks=False),'link':link,'bytes':st.st_size,'modified':st.st_mtime})
            except OSError:items.append({'name':entry.name,'path':entry.path,'unavailable':True})
    items.sort(key=lambda x:(not x.get('directory',False),x['name'].casefold()))
    return {'roots':roots(),'path':str(p),'parent':str(p.parent) if p.parent!=p else '', 'entries':items,'total':count,'truncated':count>1000}

@contextmanager
def db(base):
    conn=sqlite3.connect(base/'indice-carpetas.sqlite',timeout=10)
    conn.execute('CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY,root TEXT,kind TEXT,bytes INTEGER,modified REAL)')
    conn.execute('CREATE TABLE IF NOT EXISTS scans(root TEXT PRIMARY KEY,at TEXT,count INTEGER,partial INTEGER,skipped INTEGER)')
    try:
        with conn:yield conn
    finally:conn.close()

def walk(p,limit=10000,seconds=12):
    rows=[];skipped=0;partial=False;start=time.monotonic()
    def err(error):
        nonlocal partial;partial=True
    for current,dirs,files in os.walk(p,followlinks=False,onerror=err):
        if time.monotonic()-start>seconds:return rows,True,skipped
        allowed=[]
        for d in dirs:
            try:
                child=Path(current)/d
                if d.lower() not in SKIP and not d.startswith('.') and not child.is_symlink() and not (getattr(child.lstat(),'st_file_attributes',0)&0x400):allowed.append(d)
            except OSError:partial=True
        dirs[:]=allowed
        for name in files:
            if len(rows)>=limit or time.monotonic()-start>seconds:return rows,True,skipped
            f=Path(current)/name
            try:
                st=f.lstat()
                if f.is_symlink() or getattr(st,'st_file_attributes',0)&(0x400|0x1000|0x40000|0x400000):skipped+=1;continue
                rows.append((f,st))
            except OSError:partial=True
    return rows,partial,skipped

def index(base,value):
    p=path(value,base)
    if not p.is_dir():raise ValueError('Elige una carpeta para indexar.')
    rows,partial,skipped=walk(p)
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    with LOCK,db(base) as conn:
        if not partial:conn.execute('DELETE FROM files WHERE root=?',(str(p),))
        conn.executemany('INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)',[(str(f),str(p),f.suffix.lower() or 'sin extensión',st.st_size,st.st_mtime) for f,st in rows])
        conn.execute('INSERT OR REPLACE INTO scans VALUES(?,?,?,?,?)',(str(p),stamp,len(rows),int(partial),skipped))
    return {'ok':True,'root':str(p),'files':len(rows),'partial':partial,'skipped':skipped,'at':stamp}

def seed_catalog(base,catalog):
    with LOCK,db(base) as conn:
        if conn.execute('SELECT 1 FROM scans WHERE root=?',('catalogo-html-personal-v2',)).fetchone():return
        conn.execute('DELETE FROM files WHERE root=?',('catalogo-html',));conn.execute('DELETE FROM scans WHERE root=?',('catalogo-html',))
        rows=[r for r in catalog.get('files',[]) if r.get('personal')]
        conn.executemany('INSERT OR IGNORE INTO files VALUES(?,?,?,?,?)',[(r['path'],'catalogo-html-personal-v2',Path(r['path']).suffix.lower(),r.get('bytes') or 0,r.get('modified') or 0) for r in rows])
        conn.execute('INSERT OR REPLACE INTO scans VALUES(?,?,?,?,?)',('catalogo-html-personal-v2',catalog.get('generatedAt') or '',len(rows),int(bool(catalog.get('partial'))),0))

def search(base,query):
    if not isinstance(query,str) or len(query)>200:raise ValueError('Búsqueda demasiado larga.')
    with db(base) as conn:
        moves=aliases(base)
        rows=conn.execute('SELECT path,kind,bytes,modified FROM files '+('' if moves else 'WHERE instr(lower(path),lower(?))>0 ')+'ORDER BY modified DESC LIMIT '+('50000' if moves else '100'),() if moves else (query,)).fetchall()
        scans=[dict(zip(['root','at','count','partial','skipped'],r)) for r in conn.execute('SELECT * FROM scans')]
    files=[{'path':mapped(r[0],moves),'kind':r[1],'bytes':r[2],'modified':r[3]} for r in rows]
    if moves:files=[r for r in files if query.casefold() in r['path'].casefold()]
    return {'files':files[:100],'scans':scans,'limit':100,'boundedAfterMoves':bool(moves)}

def valid_name(value):
    if not isinstance(value,str) or not value.strip() or len(value)>150 or any(c in value for c in '<>:"/\\|?*') or value.endswith((' ','.')) or value in ('.','..') or any(ord(c)<32 for c in value):raise ValueError('Nombre de carpeta no válido.')
    if value.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:raise ValueError('Nombre reservado por el sistema.')
    return value

def plan(base,body):
    undo=body.get('undo')
    with LOCK:
        if undo:
            row=next((e for e in events(base) if e['id']==undo and e['state']=='done' and not e.get('undoneBy')),None)
            if not row:raise ValueError('Ese movimiento no se puede deshacer desde aquí.')
            source=path(row['target'],base,True);parent=path(str(Path(row['source']).parent),base,True,parent=True);name=Path(row['source']).name
        else:
            source=path(body.get('source'),base,True);parent=path(body.get('destination'),base,True,parent=True);name=valid_name(body.get('name') or source.name)
        if not source.is_dir() or not parent.is_dir():raise ValueError('Origen y destino deben ser carpetas.')
        target=(parent/name).resolve()
        if target.exists() or target==source or target.is_relative_to(source):raise ValueError('El destino existe o está dentro del origen. No se sobrescribe ni se mezcla.')
        if source.drive.lower()!=target.drive.lower():raise ValueError('Los movimientos son dentro del mismo disco. Entre discos requiere copia y verificación, aún no habilitada.')
        if not target.is_relative_to(parent):raise ValueError('Destino fuera de la carpeta elegida.')
        st=source.stat();key=uuid.uuid4().hex
        for old in list(PLANS):
            if PLANS[old]['expires']<time.time():PLANS.pop(old,None)
        data={'id':key,'kind':'move','source':str(source),'target':str(target),'inode':st.st_ino,'mtime':st.st_mtime_ns,'expires':time.time()+300,'undo':undo}
        PLANS[key]=data
        return {k:v for k,v in data.items() if k not in ('inode','mtime')}

def apply_move(base,key):
    with LOCK:
        row=PLANS.pop(key,None)
        if not row or row.get('kind')!='move' or row['expires']<time.time():raise ValueError('La vista previa venció. Prepara el movimiento otra vez.')
        source=path(row['source'],base,True);target=Path(row['target']);parent=path(str(target.parent),base,True,parent=True)
        st=source.stat()
        if st.st_ino!=row['inode'] or st.st_mtime_ns!=row['mtime'] or target.exists() or target.parent!=parent:raise ValueError('La carpeta cambió desde la vista previa. Revisa de nuevo.')
        log=events(base);event={**row,'state':'planned','at':dt.datetime.now(dt.timezone.utc).isoformat()};log.append(event);write_events(base,log)
        try:os.rename(source,target)
        except OSError:
            event['state']='failed';write_events(base,log);raise ValueError('No se pudo mover. Puede estar en uso o faltar permiso; el origen se conserva.') from None
        event['state']='done'
        if row.get('undo'):
            for e in log:
                if e['id']==row['undo']:e['undoneBy']=row['id']
        write_events(base,log)
        return {'ok':True,'event':event}

def snapshot_plan(base,value):
    p=path(value,base)
    if not p.is_dir():raise ValueError('Elige una carpeta para guardar su versión.')
    rows,partial,skipped=walk(p,MAX_FILES+1,12)
    selected=[];excluded=skipped
    for f,st in rows:
        if f.name.lower() in PRIVATE or f.name.lower().startswith('.env') or f.suffix.lower() in ('.pem','.key','.pfx','.p12') or (f.suffix.lower() in ('.json','.txt','.yaml','.yml') and re.search(r'(^|[-_.])(keys?|secrets?|credentials?|tokens?)([-_.]|$)',f.name,re.I)):
            excluded+=1;continue
        selected.append({'relative':str(f.relative_to(p)),'bytes':st.st_size,'modified':st.st_mtime_ns})
    size=sum(r['bytes'] for r in selected)
    if partial or len(rows)>MAX_FILES or size>MAX_BYTES:raise ValueError('La carpeta supera el límite de versión: 500 archivos o 50 MB. Elige una subcarpeta más pequeña.')
    if not selected:raise ValueError('No hay archivos accesibles para guardar.')
    key=uuid.uuid4().hex
    PLANS[key]={'id':key,'kind':'snapshot','source':str(p),'files':selected,'expires':time.time()+300}
    return {'id':key,'source':str(p),'files':selected,'bytes':size,'excluded':excluded,'note':'Versión local de los archivos enumerados. Se omiten dependencias, enlaces, archivos de nube sin descargar y nombres comunes de credenciales. No garantiza detectar todos los secretos.'}

def save_snapshot(base,key):
    with LOCK:
        item=PLANS.pop(key,None)
        if not item or item.get('kind')!='snapshot' or item['expires']<time.time():raise ValueError('Prepara la versión otra vez.')
        p=path(item['source'],base);rows=[];chunks=[];size=0
        for row in item['files']:
            original=p/row['relative'];st=original.lstat()
            if original.is_symlink() or getattr(st,'st_file_attributes',0)&(0x400|0x1000|0x40000|0x400000):raise ValueError('Un archivo dejó de estar disponible. Prepara la versión otra vez.')
            f=path(str(original),base)
            if not f.is_relative_to(p):raise ValueError('Archivo fuera de la carpeta.')
            st=f.lstat()
            if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['modified'] or f.is_symlink():raise ValueError('Un archivo cambió desde la vista previa. No se guardó la versión.')
            data=f.read_bytes();size+=len(data)
            after=f.stat()
            if after.st_mtime_ns!=st.st_mtime_ns or after.st_size!=st.st_size or len(data)!=st.st_size:raise ValueError('Un archivo cambió durante la lectura. Prepara la versión otra vez.')
            if size>MAX_BYTES:raise ValueError('La versión supera 50 MB.')
            chunks.append((row['relative'],data));rows.append({**row,'sha256':hashlib.sha256(data).hexdigest()})
        folder=hashlib.sha256(str(p).encode()).hexdigest()[:20];dest=base/'versiones-carpetas'/folder;dest.mkdir(parents=True,exist_ok=True)
        previous=history(base,str(p))['versions'];prev=previous[0]['files'] if previous else []
        old={r['relative']:r['sha256'] for r in prev};new={r['relative']:r['sha256'] for r in rows}
        version=uuid.uuid4().hex
        manifest={'id':version,'folder':folder,'source':str(p),'at':dt.datetime.now(dt.timezone.utc).isoformat(),'files':rows,'bytes':size,'added':[k for k in new if k not in old],'changed':[k for k in new if k in old and new[k]!=old[k]],'removed':[k for k in old if k not in new]}
        temp=dest/(version+'.tmp')
        with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as archive:
            for relative,data in chunks:archive.writestr(relative.replace('\\','/'),data)
        temp.replace(dest/(version+'.zip'))
        (dest/(version+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        return {'ok':True,'version':manifest}

def history(base,value):
    target=remap(value,base);versions=[]
    for file in (base/'versiones-carpetas').glob('*/*.json'):
        try:
            row=json.loads(file.read_text(encoding='utf-8'))
            if remap(row['source'],base)==target:versions.append(row)
        except (OSError,ValueError):continue
    return {'versions':sorted(versions,key=lambda x:x['at'],reverse=True)[:30]}

def archive_path(base,folder,version):
    if not isinstance(folder,str) or not isinstance(version,str) or len(folder)!=20 or len(version)!=32 or any(c not in '0123456789abcdef' for c in folder+version):raise ValueError('Versión no válida.')
    return base/'versiones-carpetas'/folder/(version+'.zip')

def create_folder(base,body):
    with LOCK:
        parent=path(body.get('path'),base,True,parent=True)
        name=valid_name(body.get('name'));target=parent/name
        if not target.resolve().is_relative_to(parent):raise ValueError('Destino fuera de la carpeta elegida.')
        target.mkdir(exist_ok=False)
        return {'ok':True,'path':str(target)}
