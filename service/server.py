"""Biblioteca HTML local: inventario, búsqueda y vistas estáticas sin ejecutar scripts."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import argparse
import functools
import html
import json
import mimetypes
import re
import threading
import hashlib
import datetime as dt
import secrets
import os
import html_assistant
import library_chat
import connections
import folder_library
import jules_connector
import account_identity
import muse_bridge
import muse_agent
import voice_bridge
import html_indexer
import file_catalog
import chingaquedito
import version_store

BASE = Path(os.environ.get('BEE_LIBRARY_DIR',str(Path(__file__).resolve().parent))).resolve()
MAX_PREVIEW = 2 * 1024 * 1024
ALLOWED_ASSETS = {'.css', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.otf'}
catalog = {'total': 0, 'files': [], 'drives': [], 'categories': {}, 'generatedAt': None}
catalog_mtime = None
catalog_lock = threading.Lock()
records_by_id = {}
SESSION_TOKEN = secrets.token_urlsafe(24)

def reload_catalog():
    global catalog, catalog_mtime, records_by_id
    path = BASE / 'catalog.json'
    try:
        stamp = path.stat().st_mtime_ns
        if stamp == catalog_mtime:
            return
        with catalog_lock:
            if stamp != catalog_mtime:
                catalog = json.loads(path.read_text(encoding='utf-8'))
                moves=folder_library.aliases(BASE)
                if moves:
                    for record in catalog['files']:
                        record['path']=folder_library.mapped(record['path'],moves)
                records_by_id = {str(r['id']): r for r in catalog['files']}
                catalog_mtime = stamp
    except (OSError, ValueError):
        pass

def decode(data):
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return data.decode('utf-16', errors='replace')
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return data.decode('cp1252', errors='replace')

def offline(path):
    attrs = getattr(path.stat(), 'st_file_attributes', 0)
    return bool(attrs & (0x1000 | 0x40000 | 0x400000))

@functools.lru_cache(maxsize=256)
def metadata(path, stamp):
    p = Path(path)
    try:
        if offline(p):
            return {'title': p.stem, 'state': 'cloud', 'message': 'Archivo de nube sin descargar. No se abrió automáticamente.'}
        with p.open('rb') as f:
            text = decode(f.read(65536))
        match = re.search(r'<title\b[^>]*>(.*?)</title\s*>', text, re.I | re.S)
        title = html.unescape(re.sub(r'<[^>]+>', '', match.group(1))).strip() if match else p.stem
        return {'title': title[:180] or p.stem, 'state': 'ready', 'scripted': bool(re.search(r'<script\b', text, re.I))}
    except (OSError, ValueError):
        return {'title': p.stem, 'state': 'unavailable', 'message': 'Este archivo no se pudo leer; su ruta sigue en el inventario.'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, data, mime='application/json; charset=utf-8', status=200, preview=False, attachment=None,cookie=None):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        elif isinstance(data, str):
            data = data.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        if cookie:self.send_header('Set-Cookie',cookie)
        if preview:
            origin = f'http://127.0.0.1:{self.server.server_port}'
            # Previews are embedded same-origin (iframe/img/audio); never expose them to other sites via CORS.
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Content-Security-Policy', f"sandbox; default-src 'none'; script-src 'none'; style-src 'unsafe-inline' {origin}; img-src data: {origin}; font-src data: {origin}; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri {origin}; form-action 'none'")
        else:
            csp="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"
            if urlsplit(self.path).path=='/cuenta':
                domain=account_identity.config(BASE).get('authDomain','')
                if re.fullmatch(r'[a-zA-Z0-9.-]+',domain):
                    csp=csp.replace("script-src 'self' 'unsafe-inline'","script-src 'self' 'unsafe-inline' https://www.gstatic.com https://apis.google.com").replace("frame-src 'self'","frame-src 'self' https://"+domain+" https://accounts.google.com").replace("connect-src 'self'","connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://www.googleapis.com https://www.gstatic.com")
            self.send_header('Content-Security-Policy',csp)
        if attachment:
            self.send_header('Content-Disposition', f'attachment; filename="{attachment}"')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def get_record(self, value):
        key = str(value)
        if key not in records_by_id:
            raise ValueError('Archivo fuera del catálogo')
        return records_by_id[key]

    def do_GET(self):
        host = self.headers.get('Host', '').split(':')[0]
        if host not in ('127.0.0.1', 'localhost'):
            return self.send({'error': 'Solo acceso local'}, status=403)
        url = urlsplit(self.path)
        route = unquote(url.path)
        q = parse_qs(url.query)
        reload_catalog()
        try:
            if route == '/health':
                return self.send({'app': 'biblioteca-html-local', 'total': catalog['total']})
            if route in ('/','/archivos'):
                return self.send((BASE/'archivos.html').read_bytes(),'text/html; charset=utf-8')
            if route in ('/archivos.js','/primer-arranque.js'):
                return self.send((BASE/route[1:]).read_bytes(),'text/javascript; charset=utf-8')
            if route == '/api/library/index-status':
                return self.send(html_indexer.status())
            if route == '/api/files/kinds':
                return self.send(file_catalog.kinds_catalog())
            if route == '/api/files':
                return self.send(file_catalog.inventory(BASE,q.get('q',[''])[0],q.get('kind',['all'])[0]))
            if route == '/api/files/record':
                return self.send(file_catalog.record(BASE,q.get('id',[''])[0]))
            if route == '/api/files/preview':
                row=file_catalog.record(BASE,q.get('id',[''])[0]);p=Path(row['path'])
                # Vista previa aislada (CSP sandbox, sin scripts) para imágenes, HTML, audio y video acotados.
                previewable={'.png','.jpg','.jpeg','.gif','.webp','.avif','.svg','.html','.htm','.mp3','.wav','.m4a','.ogg','.mp4','.webm'}
                limit=64*1024*1024 if p.suffix.lower() in {'.mp4','.webm','.mp3','.wav','.m4a','.ogg'} else 8*1024*1024
                if p.suffix.lower() not in previewable or offline(p) or p.stat().st_size>limit:
                    return self.send({'error':'Vista previa no disponible'},status=404)
                if p.suffix.lower() in {'.html','.htm'}:
                    text=re.sub(r'<meta\b[^>]*http-equiv\s*=\s*[\"\x27]?refresh\b[^>]*>','',re.sub(r'<base\b[^>]*>','',decode(p.read_bytes()),flags=re.I),flags=re.I)
                    return self.send(text,'text/html; charset=utf-8',preview=True)
                return self.send(p.read_bytes(),mimetypes.guess_type(p.name)[0] or 'application/octet-stream',preview=True)
            if route == '/jules':
                return self.send((BASE/'jules.html').read_bytes(),'text/html; charset=utf-8')
            if route == '/jules.js':
                return self.send((BASE/'jules.js').read_bytes(),'text/javascript; charset=utf-8')
            if route in ('/api/muse/workspace','/api/muse/job'):
                if self.headers.get('X-Library-Token') != SESSION_TOKEN:
                    return self.send({'error':'Solicitud local no autorizada'},status=403)
                return self.send(muse_agent.workspace() if route.endswith('workspace') else muse_agent.job(q.get('id',[''])[0]))
            if route == '/api/account/desktop':
                if self.headers.get('X-Library-Token') != SESSION_TOKEN:
                    return self.send({'error':'Solicitud local no autorizada'},status=403)
                key,data=account_identity.poll_desktop(q.get('flow',[''])[0])
                return self.send(data,cookie='bee_identity='+key+'; Path=/; HttpOnly; SameSite=Strict; Max-Age=3600' if key else None)
            if route == '/api/jules/status':
                return self.send(jules_connector.status(BASE))
            if route in ('/cuenta','/muse','/hackaton','/apuntadora'):
                file={'/cuenta':'cuenta.html','/muse':'muse.html','/hackaton':'hackaton.html','/apuntadora':'apuntadora.html'}[route]
                return self.send((BASE/file).read_bytes(),'text/html; charset=utf-8')
            if route in ('/chingaquedito','/chingaquedito.html'):
                return self.send((BASE/'chingaquedito.html').read_bytes(),'text/html; charset=utf-8')
            if route == '/chingaquedito.js':
                return self.send((BASE/'chingaquedito.js').read_bytes(),'text/javascript; charset=utf-8')
            if route == '/api/chingaquedito':
                return self.send(chingaquedito.status(BASE))
            if route in ('/cuenta.js','/muse.js','/apuntadora-buscar.js','/apuntadora.js','/apuntadora.css','/guia.js','/guia.css'):
                return self.send((BASE/route[1:]).read_bytes(),'text/css; charset=utf-8' if route.endswith('.css') else 'text/javascript; charset=utf-8')
            if route == '/api/account/config':
                config=account_identity.config(BASE)
                return self.send({'config':config,'configured':len(config)==4})
            if route == '/api/account/status':
                return self.send(account_identity.current(self.headers.get('Cookie','')))
            if route in ('/carpetas','/carpetas.html'):
                return self.send((BASE/'carpetas.html').read_bytes(),'text/html; charset=utf-8')
            if route == '/carpetas.js':
                return self.send((BASE/'carpetas.js').read_bytes(),'text/javascript; charset=utf-8')
            if route == '/api/folders/browse':
                return self.send(folder_library.browse(BASE,q.get('path',[''])[0],q.get('hidden',['0'])[0]=='1'))
            if route == '/api/folders/search':
                return self.send(folder_library.search(BASE,q.get('q',[''])[0]))
            if route == '/api/folders/history':
                return self.send({'events':folder_library.events(BASE)[-30:][::-1],**folder_library.history(BASE,q.get('path',[''])[0])})
            if route == '/api/folders/archive':
                p=folder_library.archive_path(BASE,q.get('folder',[''])[0],q.get('version',[''])[0])
                return self.send(p.read_bytes(),'application/zip',attachment='bee-muse-version.zip')
            if route == '/abejitas':
                return self.send((BASE/'mascotas.html').read_bytes(),'text/html; charset=utf-8')
            if route in ('/companion.js','/companion.css','/voice.js'):
                return self.send((BASE/route[1:]).read_bytes(),'text/javascript; charset=utf-8' if route.endswith('.js') else 'text/css; charset=utf-8')
            if route.startswith('/mascotas/cyberbee-octohype/'):
                name=route.removeprefix('/mascotas/cyberbee-octohype/')
                allowed={'idle.gif','waving.gif','waiting.gif','running.gif','review.gif','jumping.gif','failed.gif','running-left.gif','running-right.gif','still.png'}
                if name not in allowed:return self.send({'error':'No encontrado'},status=404)
                return self.send((BASE/'mascotas'/'cyberbee-octohype'/name).read_bytes(),'image/png' if name.endswith('.png') else 'image/gif')
            if route == '/bee-sprites.css':
                return self.send((BASE/'bee-sprites.css').read_bytes(),'text/css; charset=utf-8')
            if route == '/iart-theme.css':
                return self.send((BASE/'iart-theme.css').read_bytes(),'text/css; charset=utf-8')
            if route.startswith('/mascotas/'):
                name=route.removeprefix('/mascotas/')
                if name not in ('sheet.png','animated.png','emotions.png','emotions-animation.png','bzzz.png'):
                    return self.send({'error':'No encontrado'},status=404)
                return self.send((BASE/'mascotas'/name).read_bytes(),'image/png')
            if route in ('/html', '/index.html'):
                return self.send((BASE / 'index.html').read_bytes(), 'text/html; charset=utf-8')
            if route in ('/conexiones','/conexiones.html'):
                return self.send((BASE/'conexiones.html').read_bytes(),'text/html; charset=utf-8')
            if route == '/conexiones.js':
                return self.send((BASE/'conexiones.js').read_bytes(),'text/javascript; charset=utf-8')
            if route == '/api/connections':
                return self.send(connections.status(BASE))
            if route in ('/privacidad','/terminos','/salida-publica'):
                file={'/privacidad':'PRIVACIDAD-BORRADOR.md','/terminos':'TERMINOS-BORRADOR.md','/salida-publica':'CTO-SALIDA-PUBLICA.md'}[route]
                return self.send((BASE/file).read_bytes(),'text/plain; charset=utf-8')
            if route == '/api/catalog':
                collection_id=q.get('collection',[''])[0]
                collection=next((c for c in library_chat.load(BASE)['collections'] if c['id']==collection_id),None)
                collection_paths={folder_library.remap(p,BASE) for p in collection['paths']} if collection else None
                terms = q.get('q', [''])[0].casefold().split()
                drive = q.get('drive', [''])[0]
                category = q.get('category', ['personal'])[0]
                sort = q.get('sort', ['newest'])[0]
                page = max(0, int(q.get('page', ['0'])[0]))
                def match_category(r):
                    if category == 'personal':
                        return r.get('personal',False)
                    if category == 'review':
                        return not r.get('personal',False) and r['category'] != 'tecnicos'
                    if category == 'copies':
                        return r.get('personal',False) and r.get('copies',1)>1
                    return r['category'] == category if category else r['category'] != 'tecnicos'
                selected = [r for r in catalog['files'] if (not drive or r['drive'] == drive) and match_category(r) and all(t in (r['path']+' '+r.get('title','')).casefold() for t in terms)]
                if sort == 'name':
                    selected.sort(key=lambda r: (r['name'].casefold(), r['path']))
                elif sort == 'size':
                    selected.sort(key=lambda r: -(r['bytes'] or 0))
                else:
                    selected.sort(key=lambda r: -(r['modified'] or 0))
                if collection_id:
                    selected=[r for r in selected if collection_paths is not None and r['path'] in collection_paths]
                matched_files = len(selected)
                if category in ('personal','copies'):
                    dedup = {}
                    for r in selected:
                        dedup.setdefault(r.get('group',str(r['id'])),r)
                    selected = list(dedup.values())
                page_size = 12
                start = page * page_size
                return self.send({'total': len(selected), 'matchedFiles':matched_files, 'allTotal': catalog['total'], 'personalCount':catalog.get('personalCount',0), 'personalGroups':catalog.get('personalGroups',0),'reviewCount':catalog.get('reviewCount',0), 'partial':catalog.get('partial', False), 'files': selected[start:start + page_size], 'page': page, 'pageSize': page_size, 'categories': catalog['categories'], 'drives': [{k: v for k, v in d.items() if k != 'listing'} for d in catalog['drives']], 'generatedAt': catalog['generatedAt']})
            if route == '/api/session':
                return self.send({'token':SESSION_TOKEN})
            if route == '/api/collections':
                return self.send(library_chat.load(BASE))
            if route == '/api/ai/status':
                return self.send(html_assistant.status())
            if route == '/api/resolve':
                lookup = os.path.normcase(folder_library.remap(q.get('path',[''])[0],BASE))
                record = next((r for r in catalog['files'] if os.path.normcase(r['path'])==lookup),None)
                return self.send(record if record else {'error':'No encontrado'},status=200 if record else 404)
            if route == '/api/versions':
                record = self.get_record(q['id'][0])
                same = [r for r in catalog['files'] if r.get('group')==record.get('group')]
                variants = [r for r in catalog['files'] if r.get('personal') and r['name'].casefold()==record['name'].casefold() and r.get('project')==record.get('project') and r.get('group')!=record.get('group')][:30]
                snapshots = version_store.history(BASE,record['id'])
                return self.send({'copies':same,'candidates':variants,'snapshots':snapshots})
            if route == '/api/versions/download':
                record = self.get_record(q['id'][0])
                raw, info = version_store.restore_version(BASE, str(record['id']), q.get('sha',[''])[0])
                return self.send(raw,'application/octet-stream',attachment='restaurado-%s.html'%info['sha256'][:16])
            if route == '/api/meta':
                record = self.get_record(q['id'][0])
                return self.send(metadata(record['path'], record['modified']))
            if route == '/api/record':
                return self.send(self.get_record(q['id'][0]))
            if route.startswith('/preview/'):
                record = self.get_record(route.split('/')[2])
                p = Path(record['path'])
                meta = metadata(record['path'], record['modified'])
                if meta['state'] != 'ready':
                    text = '<html><body style="font:24px system-ui;background:#f1f2f4;color:#555;padding:60px">' + html.escape(meta.get('message', 'Vista no disponible')) + '</body></html>'
                    return self.send(text, 'text/html; charset=utf-8', preview=True)
                if p.stat().st_size > MAX_PREVIEW:
                    text = '<html><body style="font:24px system-ui;padding:60px">Archivo grande: ' + html.escape(p.name) + '<p>La miniatura está pausada para cuidar la memoria. Puedes localizar o descargar el original.</p></body></html>'
                    return self.send(text, 'text/html; charset=utf-8', preview=True)
                with p.open('rb') as f:
                    text = decode(f.read(MAX_PREVIEW))
                text = re.sub(r'<base\b[^>]*>', '', text, flags=re.I)
                text = re.sub(r'<meta\b[^>]*http-equiv\s*=\s*[\"\x27]?refresh\b[^>]*>', '', text, flags=re.I)
                base = f'<base href="http://127.0.0.1:{self.server.server_port}/assets/{record["id"]}/">'
                if re.search(r'<head\b[^>]*>', text, re.I):
                    text = re.sub(r'(<head\b[^>]*>)', lambda m: m.group(1) + base, text, count=1, flags=re.I)
                else:
                    text = base + text
                return self.send(text, 'text/html; charset=utf-8', preview=True)
            if route.startswith('/assets/'):
                parts = route.split('/', 3)
                record = self.get_record(parts[2])
                root = Path(record['path']).parent.resolve()
                p = (root / parts[3]).resolve()
                if not p.is_relative_to(root) or p.suffix.lower() not in ALLOWED_ASSETS:
                    return self.send({'error': 'Recurso no permitido'}, status=403)
                if offline(p) or p.stat().st_size > 8 * 1024 * 1024:
                    return self.send({'error': 'Recurso no disponible para miniatura'}, status=404)
                return self.send(p.read_bytes(), mimetypes.guess_type(p.name)[0] or 'application/octet-stream', preview=True)
            if route == '/download':
                record = self.get_record(q['id'][0])
                p = Path(record['path'])
                if offline(p) or p.stat().st_size > 32 * 1024 * 1024:
                    return self.send({'error': 'Localiza el original en su carpeta; no se descargó desde nube.'}, status=409)
                return self.send(p.read_bytes(), 'application/octet-stream', attachment=f'original-{record["id"]}{p.suffix.lower()}')
            return self.send({'error': 'No encontrado'}, status=404)
        except (OSError, KeyError, IndexError, ValueError) as e:
            return self.send({'error': 'No se pudo leer este elemento.'}, status=404)

    def do_POST(self):
        global catalog_mtime
        host = self.headers.get('Host','').split(':')[0]
        origin = self.headers.get('Origin','')
        allowed_origins = {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        if host not in ('127.0.0.1','localhost') or origin not in allowed_origins or self.headers.get('X-Library-Token') != SESSION_TOKEN:
            return self.send({'error':'Solicitud local no autorizada'},status=403)
        folder_routes={'/api/folders/index','/api/folders/plan','/api/folders/apply','/api/folders/snapshot-plan','/api/folders/snapshot-save','/api/folders/create'}
        jules_routes={'/api/jules/key','/api/jules/forget','/api/jules/check'}
        account_routes={'/api/account/verify','/api/account/logout','/api/account/start-desktop','/api/account/finish-desktop'}
        muse_routes={'/api/muse/account','/api/muse/probe','/api/muse/workspace','/api/muse/start','/api/muse/transcribe'}
        chingaquedito_routes={'/api/chingaquedito/activar','/api/chingaquedito/frente','/api/chingaquedito/editar','/api/chingaquedito/estado','/api/chingaquedito/volver','/api/chingaquedito/idea','/api/chingaquedito/borrar-frente','/api/chingaquedito/borrar-idea'}
        if self.path not in ('/api/library/index','/api/files/ask','/api/snapshot','/api/versions/restore','/api/ai/analyze','/api/ai/chat','/api/collections/apply','/api/connections') and self.path not in folder_routes|jules_routes|account_routes|muse_routes|chingaquedito_routes:
            return self.send({'error':'No encontrado'},status=404)
        try:
            size = int(self.headers.get('Content-Length','0'))
            if not 0<size<(4000000 if self.path=='/api/muse/transcribe' else 120000 if self.path=='/api/muse/start' else 20000 if self.path in ('/api/library/index','/api/files/ask','/api/ai/chat','/api/collections/apply','/api/connections') or self.path in folder_routes|account_routes|chingaquedito_routes or self.path=='/api/muse/start' else 2048):
                raise ValueError()
            body = json.loads(self.rfile.read(size))
            if self.path in ('/api/library/index','/api/files/ask'):
                try:
                    if not isinstance(body,dict):raise ValueError('Solicitud no válida.')
                    if self.path=='/api/library/index':return self.send(html_indexer.start(BASE,body.get('roots')))
                    return self.send(file_catalog.ask(BASE,body.get('message')))
                except (ValueError,OSError) as error:return self.send({'error':str(error) if isinstance(error,ValueError) else 'No se pudo completar.'},status=400)
            if self.path in account_routes:
                try:
                    if not isinstance(body,dict):raise ValueError('Solicitud no válida.')
                    if self.path=='/api/account/logout':return self.send(account_identity.logout(self.headers.get('Cookie','')),cookie='bee_identity=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0')
                    if self.path=='/api/account/start-desktop':return self.send(account_identity.start_desktop(body.get('provider')))
                    if self.path=='/api/account/finish-desktop':return self.send(account_identity.finish_desktop(BASE,body.get('flow'),body.get('idToken')))
                    token,data=account_identity.verify(BASE,body.get('idToken'))
                    return self.send(data,cookie='bee_identity='+token+'; Path=/; HttpOnly; SameSite=Strict; Max-Age=3600')
                except (ValueError,TypeError) as error:return self.send({'error':str(error) if isinstance(error,ValueError) else 'No se pudo comprobar Google.'},status=400)
            if self.path in muse_routes:
                try:
                    if not isinstance(body,dict):raise ValueError('Solicitud no válida.')
                    if self.path=='/api/muse/transcribe':return self.send(voice_bridge.transcribe(body))
                    if self.path=='/api/muse/workspace':return self.send(muse_agent.workspace(body.get('path')))
                    if self.path=='/api/muse/start':return self.send(muse_agent.start(body),status=202)
                    if self.path=='/api/muse/account':return self.send(muse_bridge.account_status())
                    if not html_assistant.LOCK.acquire(blocking=False):raise ValueError('Muse está atendiendo otra solicitud.')
                    try:return self.send(muse_bridge.probe(BASE))
                    finally:html_assistant.LOCK.release()
                except (ValueError,OSError) as error:return self.send({'error':str(error) if isinstance(error,ValueError) else 'No se pudo comprobar Muse.'},status=400)
            if self.path in jules_routes:
                try:
                    if not isinstance(body,dict):raise ValueError('Solicitud no válida.')
                    if self.path=='/api/jules/key':result=jules_connector.save_key(BASE,body.get('key'))
                    elif self.path=='/api/jules/forget':result=jules_connector.forget_key(BASE)
                    else:result=jules_connector.check(BASE)
                    return self.send(result)
                except (ValueError,OSError,TypeError) as error:
                    return self.send({'error':str(error) if isinstance(error,ValueError) else 'No se pudo completar la conexión con Jules.'},status=400)
            if self.path in chingaquedito_routes:
                try:
                    if not isinstance(body,dict):raise ValueError('Solicitud no válida.')
                    if self.path=='/api/chingaquedito/activar':result=chingaquedito.activar(BASE,body.get('activo'))
                    elif self.path=='/api/chingaquedito/frente':result=chingaquedito.crear_frente(BASE,body)
                    elif self.path=='/api/chingaquedito/editar':result=chingaquedito.editar_frente(BASE,body)
                    elif self.path=='/api/chingaquedito/estado':result=chingaquedito.cambiar_estado(BASE,body)
                    elif self.path=='/api/chingaquedito/volver':result=chingaquedito.volver(BASE,body)
                    elif self.path=='/api/chingaquedito/borrar-frente':result=chingaquedito.borrar_frente(BASE,body)
                    elif self.path=='/api/chingaquedito/borrar-idea':result=chingaquedito.borrar_idea(BASE,body)
                    else:result=chingaquedito.guardar_idea(BASE,body)
                    return self.send(result)
                except (ValueError,OSError,TypeError) as error:
                    return self.send({'error':str(error) if isinstance(error,ValueError) else 'No se pudo guardar en la libreta local.'},status=400)
            if self.path in folder_routes:
                try:
                    if not isinstance(body,dict):raise ValueError('Solicitud no válida.')
                    if self.path=='/api/folders/index':result=folder_library.index(BASE,body.get('path'))
                    elif self.path=='/api/folders/create':result=folder_library.create_folder(BASE,body)
                    elif self.path=='/api/folders/plan':result=folder_library.plan(BASE,body)
                    elif self.path=='/api/folders/apply':
                        result=folder_library.apply_move(BASE,body.get('id'));catalog_mtime=None;reload_catalog()
                    elif self.path=='/api/folders/snapshot-plan':result=folder_library.snapshot_plan(BASE,body.get('path'))
                    else:result=folder_library.save_snapshot(BASE,body.get('id'))
                    return self.send(result)
                except (ValueError,OSError,TypeError) as error:
                    return self.send({'error':str(error) if isinstance(error,ValueError) else 'No se pudo completar. Revisa permisos y disponibilidad de la carpeta.'},status=400)
            if self.path == '/api/connections':
                try:
                    return self.send({'ok':True,'config':connections.save(BASE,body)})
                except (ValueError,TypeError):
                    return self.send({'error':'Revisa los campos. Solo identificadores públicos y URLs sin credenciales; no pegues claves.'},status=400)
            if self.path == '/api/versions/restore':
                try:
                    if not isinstance(body,dict):raise ValueError('Solicitud no válida.')
                    record = self.get_record(body.get('id'))
                    _,info = version_store.restore_version(BASE,str(record['id']),body.get('versionId') or body.get('sha256') or '')
                    return self.send({'ok':True,'versionId':info['versionId'],'sha256':info['sha256'],'bytes':info['bytes'],'verificado':True,'nota':'Bytes verificados contra su huella. El original y la copia guardada no se modificaron.'})
                except (ValueError,OSError,KeyError) as error:
                    return self.send({'error':str(error) if isinstance(error,ValueError) else 'No se pudo restaurar esta versión.'},status=400)
            reload_catalog()
            if self.path in ('/api/ai/chat','/api/collections/apply'):
                try:
                    if self.path=='/api/ai/chat':return self.send(library_chat.propose(catalog,body.get('message',''),body.get('history',[])))
                    return self.send(library_chat.apply(BASE,catalog,body.get('proposal')))
                except Exception as error:
                    return self.send({'error':str(error) if isinstance(error,ValueError) else 'No se pudo completar la solicitud. Revisa tu sesión de Muse Code.'},status=503)
            record = self.get_record(body['id'])
            if self.path == '/api/ai/analyze':
                try:
                    return self.send(html_assistant.analyze(record,str(body.get('model','')),BASE))
                except Exception as error:
                    message=str(error) if isinstance(error,ValueError) else 'Muse no completó el análisis. Revisa su sesión y disponibilidad.'
                    return self.send({'error':message},status=503)
            source = Path(record['path'])
            if offline(source) or source.stat().st_size>MAX_PREVIEW:
                return self.send({'error':'Esta versión no se guardó: el archivo está en nube o supera el límite de 2 MB.'},status=409)
            saved = version_store.save_version(BASE,record)
            return self.send({'ok':True,'alreadyExists':saved['alreadyExists'],'sha256':saved['sha256'],'versionId':saved['versionId'],'bytes':saved['bytes'],'manifiesto':saved['manifiesto']})
        except (OSError,KeyError,ValueError):
            return self.send({'error':'No se pudo guardar esta versión.'},status=400)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    reload_catalog()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.daemon_threads = True
    print(f'Biblioteca HTML: http://127.0.0.1:{server.server_port} — {catalog["total"]} archivos', flush=True)
    server.serve_forever()
