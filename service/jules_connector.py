"""Read-only Jules API adapter. Owner-local Windows credential storage."""
import ctypes,json,os,threading,time,urllib.request,urllib.error
from ctypes import wintypes
from urllib.parse import urlsplit

BASE_URL='https://jules.googleapis.com/v1alpha'
LOCK=threading.RLock()
LAST_OK=None

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def crypt(data,decrypt=False):
    if os.name!='nt':raise ValueError('El guardado cifrado de esta versión requiere Windows. También puedes usar JULES_API_KEY en el servidor local.')
    source=ctypes.create_string_buffer(data);blob=Blob(len(data),ctypes.cast(source,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    api=ctypes.windll.crypt32
    function=api.CryptUnprotectData if decrypt else api.CryptProtectData
    function.restype=wintypes.BOOL
    function.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    if not function(ctypes.byref(blob),None,None,None,None,1,ctypes.byref(out)):raise ValueError('Windows no pudo acceder a la clave cifrada para este usuario.')
    try:return ctypes.string_at(out.data,out.size)
    finally:
        free=ctypes.windll.kernel32.LocalFree;free.argtypes=[ctypes.c_void_p];free.restype=ctypes.c_void_p;free(out.data)

def key_path(base):return base/'.credentials'/'jules.dpapi'

def valid_key(value):
    return isinstance(value,str) and 20<=len(value)<=512 and all(33<=ord(c)<=126 for c in value)

def read_key(base):
    value=os.environ.get('JULES_API_KEY','').strip()
    if value:
        if not valid_key(value):raise ValueError('La variable JULES_API_KEY no tiene un formato válido. No se envió la clave.')
        return value,'environment'
    p=key_path(base)
    if p.exists():
        try:value=crypt(p.read_bytes(),True).decode('utf-8')
        except (OSError,UnicodeError,ValueError):raise ValueError('No se pudo abrir la clave cifrada. Puedes volver a guardarla para este usuario de Windows.') from None
        if not valid_key(value):raise ValueError('La clave guardada no tiene un formato válido. Vuelve a añadirla.')
        return value,'windows'
    return None,None

def status(base):
    return {'configured':bool(os.environ.get('JULES_API_KEY','').strip()) or key_path(base).exists(),
            'verified':LAST_OK is not None,'lastVerified':LAST_OK,'readOnly':True,
            'storage':'Windows DPAPI · usuario actual' if os.name=='nt' else 'Variable de entorno',
            'apiVersion':'v1alpha','provider':'Google Jules'}

def save_key(base,value):
    global LAST_OK
    if not valid_key(value):raise ValueError('Pega únicamente la clave API de Jules, sin espacios ni instrucciones.')
    encrypted=crypt(value.encode('utf-8'))
    with LOCK:
        p=key_path(base);p.parent.mkdir(exist_ok=True);temp=p.with_suffix('.tmp');temp.write_bytes(encrypted);os.replace(temp,p);LAST_OK=None
    note='Clave guardada cifrada en este equipo. Falta comprobarla con Jules.'
    if os.environ.get('JULES_API_KEY','').strip():note+=' El servidor prioriza la variable JULES_API_KEY que ya tiene configurada.'
    return {'ok':True,**status(base),'note':note}

def forget_key(base):
    global LAST_OK
    with LOCK:
        key_path(base).unlink(missing_ok=True);LAST_OK=None
    return {'ok':True,**status(base),'note':'Se quitó la copia guardada; no revoca la clave en Google. Si hay JULES_API_KEY en el entorno, sigue disponible.'}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def request(base,resource):
    if resource not in ('sources','sessions'):raise ValueError('Operación no permitida en esta conexión de lectura.')
    key,_=read_key(base)
    if not key:raise ValueError('Falta tu clave API de Jules. Añádela en esta pantalla; no la pegues en el chat.')
    req=urllib.request.Request(BASE_URL+'/'+resource+'?pageSize=20',headers={'X-Goog-Api-Key':key,'Accept':'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=20) as response:
            raw=response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024:raise ValueError('La respuesta de Jules superó el límite de lectura.')
            data=json.loads(raw)
            if not isinstance(data,dict):raise ValueError('Jules devolvió una respuesta no válida.')
            return data
    except urllib.error.HTTPError as error:
        text={400:'Jules rechazó la solicitud. Revisa la disponibilidad de la API en tu cuenta.',401:'Jules no aceptó la clave. Revísala en su configuración.',403:'La cuenta o clave no tiene permiso para consultar Jules.',429:'Jules alcanzó un límite de uso. Vuelve a consultar más tarde.'}
        raise ValueError(text.get(error.code,'Jules no completó la consulta. No se enviaron tareas.')) from None
    except (urllib.error.URLError,TimeoutError,OSError):raise ValueError('No se pudo contactar con Jules. La conexión no quedó verificada.') from None
    except (json.JSONDecodeError,UnicodeDecodeError):raise ValueError('Jules devolvió una respuesta que no se pudo leer.') from None

def safe_url(value):
    if not isinstance(value,str):return None
    p=urlsplit(value)
    return value if p.scheme=='https' and p.hostname=='jules.google.com' and p.path.startswith('/session/') and not p.username and not p.password and not p.query and not p.fragment else None

def check(base):
    global LAST_OK
    if not LOCK.acquire(blocking=False):raise ValueError('Ya hay una consulta a Jules en curso.')
    try:
        LAST_OK=None
        sources=request(base,'sources');sessions=request(base,'sessions')
        repos=[]
        for row in sources.get('sources',[])[:20]:
            if not isinstance(row,dict):continue
            repo=row.get('githubRepo',{})
            if not isinstance(repo,dict):repo={}
            repos.append({'name':str(row.get('name',''))[:300],'owner':str(repo.get('owner',''))[:100],'repo':str(repo.get('repo',''))[:150]})
        tasks=[]
        for row in sessions.get('sessions',[])[:20]:
            if not isinstance(row,dict):continue
            tasks.append({'name':str(row.get('name',''))[:150],'title':str(row.get('title') or 'Tarea sin título')[:200],'state':str(row.get('state','UNKNOWN'))[:60],'url':safe_url(row.get('url'))})
        LAST_OK=time.time()
        return {**status(base),'sources':repos,'sessions':tasks,'moreSources':bool(sources.get('nextPageToken')),'moreSessions':bool(sessions.get('nextPageToken')),
                'note':'Consulta de lectura: hasta 20 repositorios y 20 tareas. No se creó, aprobó ni modificó ninguna tarea.'}
    finally:LOCK.release()
