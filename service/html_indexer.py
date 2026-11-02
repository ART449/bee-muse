"""Opt-in HTML inventory for a fresh client. No brands, user paths or remote calls."""
from pathlib import Path
import datetime as dt
import hashlib
import html
import json
import os
import re
import threading
import time

LOCK=threading.Lock()
STATE={'running':False,'scannedEntries':0,'htmlFound':0,'skipped':0,'errors':0,'partial':False,'completedAt':None}
SKIP={'.git','.svn','.hg','node_modules','vendor','site-packages','venv','.venv','__pycache__','.cache','.rustup','.cargo','.gradle','.npm','.nuget','.m2','windows','program files','program files (x86)','programdata','appdata','$recycle.bin','system volume information'}
SUFFIXES={'.html','.htm','.xhtml'}
MAX_ENTRIES=200000
MAX_HTML=10000
MAX_SECONDS=90

def status():
    with LOCK:return dict(STATE)

def selected_roots(values,base):
    if not isinstance(values,list) or not 1<=len(values)<=12:raise ValueError('Elige entre una y doce carpetas propias.')
    roots=[]
    for value in values:
        if not isinstance(value,str) or len(value)>1500:raise ValueError('Ubicación no válida.')
        p=Path(value)
        if not p.is_absolute() or value.startswith(('\\\\','//')) or p.is_symlink():raise ValueError('Elige una carpeta local, sin enlaces.')
        p=p.resolve(strict=True)
        if not p.is_dir() or getattr(p.lstat(),'st_file_attributes',0)&0x400:raise ValueError('Elige una carpeta local, sin enlaces.')
        if p==base.resolve() or p.is_relative_to(base.resolve()):raise ValueError('Elige tus proyectos, no los archivos internos de Beamuse.')
        if p.name.lower() in SKIP:raise ValueError('Esa carpeta contiene archivos de programas. Elige tus proyectos.')
        if not any(p.is_relative_to(old) for old in roots):
            roots=[old for old in roots if not old.is_relative_to(p)];roots.append(p)
    return roots

def start(base,values):
    roots=selected_roots(values,base)
    with LOCK:
        if STATE['running']:raise ValueError('Ya hay una indexación HTML en curso.')
        STATE.clear();STATE.update(running=True,scannedEntries=0,htmlFound=0,skipped=0,errors=0,partial=False,completedAt=None)
    threading.Thread(target=scan,args=(base,roots),daemon=True).start()
    return status()

def scan(base,roots):
    started=time.monotonic();records=[];seen=set();groups={};counts={};entries=skipped=errors=0;partial=False
    budget=64*1024*1024
    def progress():
        with LOCK:STATE.update(scannedEntries=entries,htmlFound=len(records),skipped=skipped,errors=errors,partial=partial)
    try:
        for root in roots:
            stack=[root]
            while stack:
                if entries>=MAX_ENTRIES or len(records)>=MAX_HTML or time.monotonic()-started>MAX_SECONDS:
                    partial=True;break
                current=stack.pop()
                try:
                    with os.scandir(current) as listing:
                        for entry in listing:
                            entries+=1
                            if entries%100==0:progress()
                            if entries>=MAX_ENTRIES or len(records)>=MAX_HTML or time.monotonic()-started>MAX_SECONDS:partial=True;break
                            try:
                                if entry.is_symlink():skipped+=1;continue
                                st=entry.stat(follow_symlinks=False)
                                if getattr(st,'st_file_attributes',0)&(0x400|0x1000|0x40000|0x400000):skipped+=1;continue
                                p=Path(entry.path)
                                if entry.is_dir(follow_symlinks=False):
                                    if entry.name.lower() not in SKIP and p.resolve()!=base.resolve():stack.append(p)
                                    else:skipped+=1
                                    continue
                                if p.suffix.lower() not in SUFFIXES:continue
                                key=os.path.normcase(str(p.resolve()))
                                if key in seen:continue
                                seen.add(key)
                                ident=hashlib.sha256(key.encode()).hexdigest()[:20]
                                title=p.stem;digest=None
                                if st.st_size<=2*1024*1024 and st.st_size<=budget:
                                    raw=p.read_bytes();budget-=len(raw)
                                    digest=hashlib.sha256(raw).hexdigest()
                                    text=raw[:65536].decode('utf-8-sig',errors='replace')
                                    match=re.search(r'<title\b[^>]*>(.*?)</title\s*>',text,re.I|re.S)
                                    if match:title=html.unescape(re.sub('<[^>]+>','',match.group(1))).strip()[:180] or p.stem
                                group='sha256:'+digest if digest else 'path:'+ident
                                groups[group]=groups.get(group,0)+1
                                drive=p.drive or str(root)
                                counts[drive]=counts.get(drive,0)+1
                                records.append({'id':ident,'path':str(p),'name':p.name,'title':title,'drive':drive,'bytes':st.st_size,'modified':st.st_mtime,'category':'proyectos','personal':True,'origin':'carpeta-elegida-por-usuario','project':p.parent.name,'cloud':False,'group':group})
                            except OSError:errors+=1;partial=True
                except OSError:errors+=1;partial=True
            if partial and (entries>=MAX_ENTRIES or len(records)>=MAX_HTML or time.monotonic()-started>MAX_SECONDS):break
        previous={'files':[]}
        try:previous=json.loads((base/'catalog.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):pass
        # Complete rescans replace only the chosen roots. Partial scans preserve older entries.
        merged={r['path']:r for r in previous.get('files',[]) if partial or not any(Path(r['path']).is_relative_to(root) for root in roots)}
        merged.update({r['path']:r for r in records});records=list(merged.values());groups={};counts={}
        for row in records:groups[row['group']]=groups.get(row['group'],0)+1;counts[row['drive']]=counts.get(row['drive'],0)+1
        for row in records:row['copies']=groups[row['group']]
        stamp=dt.datetime.now(dt.timezone.utc).isoformat()
        catalog={'total':len(records),'files':records,'drives':[{'DeviceID':drive,'VolumeName':'Carpetas elegidas','files':count,'statErrors':errors if i==0 else 0} for i,(drive,count) in enumerate(counts.items())],'categories':{'proyectos':len(records)},'generatedAt':stamp,'personalCount':len(records),'personalGroups':len(groups),'reviewCount':0,'partial':partial,'scope':'Solo carpetas elegidas. No se infiere autoría ni se indexan todos los tipos de archivo.'}
        target=base/'catalog.json';temp=base/'catalog-index.tmp';temp.write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8');os.replace(temp,target)
        progress()
        with LOCK:STATE.update(running=False,completedAt=stamp,total=len(records),groups=len(groups),partial=partial)
    except Exception:
        progress()
        with LOCK:STATE.update(running=False,error='No se pudo completar la indexación. El inventario anterior se conserva.',partial=True)
