"""Release planning only. Never stores credentials or claims OAuth authorization."""
import json
import os
import threading
from pathlib import Path
from urllib.parse import urlsplit

LOCK = threading.Lock()
SERVICES = [
    dict(id='jules',name='Jules · Google',group='Agentes de desarrollo',purpose='Consultar repositorios autorizados y seguir tareas de programación en la nube de Google.',permission='Clave propia de Jules. Esta integración usa solo consultas de lectura; la clave puede permitir más operaciones en el proveedor.',fields=[],docs='https://jules.google/docs/api/reference/',next='Abre el panel de Jules, inicia sesión en Google, autoriza repositorios en GitHub y añade tu clave en el apartado seguro. No se sustituye el cerebro Muse ni se comparten sus cuentas.'),
    dict(id='privateNetwork', name='Beatscale · Tailscale / Headscale', group='Infraestructura privada', purpose='Acceder al servidor propio y sus servicios sin hacer públicos sus paneles.', permission='Acceso por dispositivo, identidad y servicio. La red privada no sustituye la autenticación de la aplicación.', fields=['baseUrl'], docs='https://tailscale.com/kb/1018/acls', next='Comprobar qué implementa Beatscale y elegir el control de red. Es opcional y no se distribuyen claves de la red a usuarios públicos.'),
    dict(id='custom', name='Otro servicio · Skytur por identificar', group='Herramientas', purpose='Reservar una conexión para el servicio que falta identificar.', permission='Sin permisos concedidos ni peticiones externas.', fields=['baseUrl'], docs='', next='Confirmar nombre, función y API antes de implementar el adaptador.'),
    dict(id='identity', name='Acceso · Firebase Auth', group='Acceso', purpose='Entrar con Google o GitHub y administrar la cuenta.', permission='Identidad básica. No concede acceso a Drive, repositorios ni discos.', fields=['projectId','clientId'], docs='https://firebase.google.com/docs/auth', next='Registrar aplicación, proveedores y dominios. Verificar sesiones en el servidor.'),
    dict(id='github', name='GitHub', group='Código', purpose='Relacionar repositorios, versiones, comprobaciones y despliegues.', permission='GitHub App: metadatos, contenido, Actions y deployments en lectura; solo repositorios elegidos. Escritura aparte.', fields=['appId','clientId','callbackUrl'], docs='https://docs.github.com/en/apps/creating-github-apps', next='Crear GitHub App, registrar retorno y webhook; implementar instalación, firma y tokens.'),
    dict(id='drive', name='Google Drive', group='Archivos', purpose='Añadir archivos que el usuario elija desde Drive.', permission='Picker y drive.file: acceso a archivos elegidos, sin barrer todo Drive. Aunque el permiso permite cambios, la primera integración será de lectura.', fields=['projectId','clientId','callbackUrl'], docs='https://developers.google.com/workspace/drive/api/guides/api-specific-auth', next='Habilitar Drive y Picker, configurar consentimiento OAuth, retorno y revisión aplicable.'),
    dict(id='gitea', name='GitBee · Gitea', group='Código', purpose='Mantener el repositorio propio y comprobar el espejo con GitHub.', permission='Cuenta de servicio con acceso limitado al repositorio. Escritura y sincronización bajo acción explícita.', fields=['baseUrl'], docs='https://docs.gitea.com/development/api-usage', next='Añadir adaptador, credencial en almacén seguro y verificación de commits del espejo.'),
    dict(id='railway', name='Railway', group='Publicación', purpose='Ver builds, servicios, registros y versión desplegada.', permission='Credencial limitada al proyecto cuando esté disponible. Desplegar requiere una acción separada.', fields=['projectId'], docs='https://docs.railway.com/guides/public-api', next='Implementar adaptador de lectura y asociar commit, servicio y URL; después, publicación revisable.'),
    dict(id='cloudflare', name='Cloudflare', group='Publicación', purpose='Relacionar dominios y DNS con el destino publicado.', permission='Token limitado a la zona; comenzar con DNS de lectura. Cambios de DNS separados.', fields=['accountId','zoneId'], docs='https://developers.cloudflare.com/fundamentals/api/get-started/', next='Añadir adaptador, verificar zona y permisos y mostrar el destino real.'),
    dict(id='privateAi', name='IA propia · Full', group='Inteligencia', purpose='Usar el modelo de IART Labs desde su servidor privado.', permission='El cliente no recibe credenciales del servidor ni acceso directo al motor.', fields=['baseUrl','model'], docs='', next='Implementar pasarela autenticada, aislamiento por usuario, cuotas y salud del servidor. Aún no conectada.'),
    dict(id='api', name='APIs · Free Developer', group='Inteligencia', purpose='Conectar el proveedor del usuario con un adaptador compatible.', permission='Claves en almacén seguro del sistema o servidor; nunca en campos de esta pantalla.', fields=['baseUrl','model'], docs='', next='Implementar adaptadores y bóveda; proteger peticiones de red y limitar gasto. No hay proxy genérico habilitado.'),
    dict(id='mcp', name='Herramientas MCP', group='Herramientas', purpose='Añadir capacidades concretas de otros servicios.', permission='Permisos por herramienta; lectura inicial. Acciones con efectos requieren revisión.', fields=['baseUrl'], docs='https://modelcontextprotocol.io/docs/learn/architecture', next='Implementar cliente, autenticación, lista de herramientas permitidas y límites. No ejecutar servidores arbitrarios.'),
]
FIELDS = {s['id']:set(s['fields']) for s in SERVICES}

def load(base):
    try:
        value=json.loads((base/'conexiones.json').read_text(encoding='utf-8'))
        return validate(value)
    except (OSError, ValueError, TypeError):
        return {'edition':'free','services':{}}

def validate(value):
    if not isinstance(value,dict) or set(value)-{'edition','services'}:
        raise ValueError('Configuración no válida.')
    edition=value.get('edition','free')
    if edition not in ('free','full'):raise ValueError('Edición no válida.')
    services=value.get('services',{})
    if not isinstance(services,dict) or set(services)-FIELDS.keys():raise ValueError('Servicio desconocido.')
    cleaned={}
    for service, fields in services.items():
        if not isinstance(fields,dict) or set(fields)-FIELDS[service]:raise ValueError('Solo se aceptan identificadores públicos.')
        cleaned[service]={}
        for key, val in fields.items():
            if not isinstance(val,str) or len(val)>300 or any(ord(c)<32 for c in val):raise ValueError('Campo no válido.')
            val=val.strip()
            if val.startswith(('sk-','ghp_','github_pat_')) or 'BEGIN PRIVATE KEY' in val:raise ValueError('No pegues claves ni tokens aquí.')
            if val and key in ('baseUrl','callbackUrl'):
                parsed=urlsplit(val)
                if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('Usa una URL sin claves, parámetros ni credenciales.')
                if parsed.scheme=='http' and parsed.hostname not in ('localhost','127.0.0.1','::1'):raise ValueError('Las direcciones remotas requieren HTTPS.')
            cleaned[service][key]=val
    return {'edition':edition,'services':cleaned}

def save(base, value):
    value=validate(value)
    with LOCK:
        dest=base/'conexiones.json'
        temp=base/'conexiones.tmp'
        temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(temp,dest)
    return value

def status(base):
    config=load(base)
    order=['identity','github','drive','gitea','railway','cloudflare','jules','privateAi','api','mcp','privateNetwork','custom']
    return dict(config=config, services=sorted(SERVICES,key=lambda s:order.index(s['id'])), mode='local', publicReady=False,
                note='Guardar datos de preparación no conecta cuentas. OAuth, bóveda y adaptadores están pendientes.')
