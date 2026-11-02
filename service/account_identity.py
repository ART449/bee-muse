"""Google identity via Firebase; no provider access tokens or public filesystem authorization."""
import base64,json,secrets,time,threading,urllib.request,urllib.error
from http.cookies import SimpleCookie

LOCK=threading.RLock();SESSIONS={}
def config(base):
    try:
        c=json.loads((base/'firebase-web.json').read_text(encoding='utf-8'))
        return {k:c[k] for k in ('apiKey','authDomain','projectId','appId') if isinstance(c.get(k),str)}
    except (OSError,ValueError,TypeError):return {}

def current(cookie):
    try:
        jar=SimpleCookie();jar.load(cookie or '');key=jar['bee_identity'].value
    except (KeyError,ValueError):return {'authenticated':False}
    with LOCK:
        row=SESSIONS.get(key)
        if not row or row['expires']<time.time():
            SESSIONS.pop(key,None);return {'authenticated':False}
        return {'authenticated':True,'user':{k:row[k] for k in ('uid','name','email')},'expires':row['expires'],'scope':'Identidad de Bee-Muse. No autoriza otras APIs ni convierte el servidor local en multiusuario.'}

def verify(base,token):
    c=config(base)
    if len(c)!=4:raise ValueError('Falta la configuración pública de Firebase.')
    if not isinstance(token,str) or not 100<len(token)<15000 or token.count('.')!=2:raise ValueError('No se recibió una identidad válida de Google.')
    try:
        payload=token.split('.')[1];claims=json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
        if not isinstance(claims,dict) or claims.get('aud')!=c['projectId'] or claims.get('iss')!='https://securetoken.google.com/'+c['projectId']:raise ValueError()
        provider=claims.get('firebase',{})
        if not isinstance(provider,dict) or provider.get('sign_in_provider')!='google.com' or not isinstance(claims.get('exp'),(int,float)) or claims['exp']<=time.time():raise ValueError()
    except (ValueError,TypeError,KeyError,AssertionError):raise ValueError('La identidad recibida no pertenece al acceso Google de Bee-Muse o ya venció.') from None
    req=urllib.request.Request('https://identitytoolkit.googleapis.com/v1/accounts:lookup?key='+c['apiKey'],data=json.dumps({'idToken':token}).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=15) as response:data=json.loads(response.read(131072))
        user=data['users'][0]
        if user.get('disabled') or user.get('localId')!=claims.get('sub') or not user.get('emailVerified'):raise ValueError()
    except (urllib.error.URLError,OSError,ValueError,KeyError,IndexError,TypeError):raise ValueError('Google no pudo verificar esta sesión. Vuelve a iniciar sesión.') from None
    key=secrets.token_urlsafe(32)
    with LOCK:
        for old in list(SESSIONS):
            if SESSIONS[old]['expires']<time.time():SESSIONS.pop(old,None)
        if len(SESSIONS)>=100:raise ValueError('Hay demasiadas sesiones locales. Reinicia la aplicación para limpiarlas.')
        SESSIONS[key]={'uid':str(user['localId'])[:150],'name':str(user.get('displayName') or 'Cuenta de Google')[:150],'email':str(user.get('email',''))[:254],'expires':min(claims['exp'],time.time()+3600)}
    return key,current('bee_identity='+key)

def logout(cookie):
    try:
        jar=SimpleCookie();jar.load(cookie or '')
        with LOCK:SESSIONS.pop(jar['bee_identity'].value,None)
    except (KeyError,ValueError):pass
    return {'authenticated':False}
