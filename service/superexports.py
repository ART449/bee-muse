"""Superexportaciones: vaciar espacio con vista previa, copia verificada y retiro con candado.

Flujo en cuatro pasos, cada uno es una función independiente que recibe `base`
(carpeta de datos de Bee-Muse) y un `body` JSON ya decodificado:

1. previsualizar(base, body)  -> recorre los orígenes y clasifica por colores.
                                 NO toca disco: no copia, no mueve, no borra.
2. preparar(base, body)       -> fija destino y selección; comprueba espacio.
                                 Sigue sin tocar nada.
3. copiar(base, body)         -> copia a destino, SHA-256 del origen y del
                                 destino releído; escribe recibo en
                                 base/superexports-recibos/<id>.json.
                                 Los originales se conservan.
4. retirar(base, body)        -> SOLO con confirmar=True + frase exacta +
                                 recibo verificado + reverificación en el
                                 momento. Modo 'cuarentena' (renombrar en el
                                 mismo disco, reversible) o 'borrar'.

Colores:
  verde    regenerable por herramienta (node_modules, __pycache__, .venv, build…)
  amarillo grande y copiable: modelos, ISOs, archivos comprimidos, video…
  rojo     copiable pero con riesgo de dependencia: repo git, AppData, enlaces,
           credenciales, bases de datos, modificado hace poco, Ollama…
  gris     no se pudo leer

Las clasificaciones son heurísticas por nombre, ruta y atributos. No analizan
contenido ni quién referencia cada archivo, así que un verde puede tener una
dependencia desconocida. El módulo no promete que retirar no rompe nada.
"""
import datetime as dt
import contextlib
import hashlib
import json
import os
import shutil
import stat
import threading
import time
import uuid
from pathlib import Path

LOCK = threading.RLock()
PLANES = {}       # id -> vista previa (expira)
OPERACIONES = {}  # id -> operación preparada / en curso / terminada
RECIBOS_DIR = 'superexports-recibos'
EXPIRA_PLAN = 15 * 60
EXPIRA_OPERACION = 60 * 60
MIN_BYTES_DEFECTO = 50 * 1024 * 1024
MAX_GRUPOS = 4000
MAX_ARCHIVOS_LISTADOS = 40      # por grupo en la vista previa
MAX_SEGUNDOS_RECORRIDO = 90
MAX_ARCHIVOS_RECORRIDO = 400000
DIAS_RECIENTE = 7
CHUNK = 1024 * 1024
FRASE_RETIRAR = 'RETIRAR ORIGINALES'
FRASE_BORRAR = 'BORRAR ORIGINALES'
CARPETA_CUARENTENA = '_superexport_retirado'
COLORES = ('verde', 'amarillo', 'rojo', 'gris')

REGENERABLES = {
    'node_modules': 'npm ci / npm install', '__pycache__': 'Python lo recrea solo',
    '.venv': 'python -m venv + pip install -r requirements', 'venv': 'python -m venv + pip install -r requirements',
    'dist': 'volver a compilar', 'build': 'volver a compilar', 'release': 'volver a compilar', 'out': 'volver a compilar',
    'target': 'cargo build / mvn package', '.cache': 'la herramienta lo recrea', '.gradle': 'gradle lo recrea',
    '.next': 'next build', '.turbo': 'turbo lo recrea', 'coverage': 'volver a correr pruebas',
    '.pytest_cache': 'pytest lo recrea', '.mypy_cache': 'mypy lo recrea', '.parcel-cache': 'parcel lo recrea',
    'npm-cache': 'npm lo recrea', '_cacache': 'npm lo recrea', '.nuget': 'dotnet restore',
}
PESADOS = {'.gguf', '.safetensors', '.pt', '.pth', '.ckpt', '.onnx', '.iso', '.img', '.vhd', '.vhdx', '.vmdk', '.qcow2',
           '.zip', '.7z', '.rar', '.tar', '.gz', '.tgz', '.xz', '.bz2', '.mp4', '.mkv', '.mov', '.avi', '.webm',
           '.exe', '.msi', '.dmg', '.apk', '.appimage', '.asar', '.wim', '.esd', '.bak', '.pak', '.psd', '.blend', '.wav', '.flac'}
BASES_DATOS = {'.sqlite', '.sqlite3', '.db', '.mdb', '.accdb', '.ldb', '.wal', '.shm'}
CREDENCIALES = {'.env', 'auth.json', 'credentials.json', 'token.json', 'id_rsa', 'id_ed25519', '.credentials'}
CREDENCIAL_EXT = {'.pem', '.key', '.pfx', '.p12', '.jks', '.keystore'}
NUNCA_EXPORTAR = {'.git'}
PRIVADAS = {'.ssh', '.aws', '.azure', '.credentials', '.gnupg', '.vault', 'vault', 'secrets',
            'credentials', '_negro_no_tocar', '_rojo_cuarentena', '_rojo_cuarentena_no_borrar',
            CARPETA_CUARENTENA}
ATTR_REPARSE = 0x400
ATTR_OFFLINE = 0x1000
ATTR_RECALL = 0x40000 | 0x400000


def _ahora():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def _id():
    return uuid.uuid4().hex[:16]


def _es_reparse(p):
    try:
        st = p.lstat()
    except OSError:
        return False
    return bool(getattr(st, 'st_file_attributes', 0) & ATTR_REPARSE) or p.is_symlink()


def _sin_enlaces(p):
    """No resolver primero: eso ocultaría una unión que estaba en la ruta elegida."""
    p = Path(os.path.abspath(p))
    for parte in [p, *p.parents]:
        if os.path.lexists(parte) and _es_reparse(parte):
            raise ValueError('Enlace, unión o placeholder no permitido: %s' % parte)
    return p


def _exclusion(p, st=None):
    p = Path(p)
    partes = {x.lower() for x in p.parts}
    nombre = p.name.lower()
    if partes & (PRIVADAS | NUNCA_EXPORTAR) or nombre in CREDENCIALES or nombre.startswith('.env') or p.suffix.lower() in CREDENCIAL_EXT:
        return 'credencial o zona protegida'
    if p.suffix.lower() in BASES_DATOS or nombre.endswith(('-wal', '-shm', '-journal')):
        return 'base de datos o registro transaccional'
    if st is not None:
        if getattr(st, 'st_file_attributes', 0) & (ATTR_REPARSE | ATTR_OFFLINE | ATTR_RECALL):
            return 'enlace o archivo de nube no disponible localmente'
        if not stat.S_ISREG(st.st_mode):
            return 'no es un archivo regular'
    return None


def _identidad(st):
    return {'dev': st.st_dev, 'ino': st.st_ino, 'bytes': st.st_size, 'mtime': st.st_mtime_ns}


def _coincide(st, fila):
    return all(_identidad(st)[k] == fila[k] for k in ('dev', 'ino', 'bytes', 'mtime'))


def _ruta_fila(op, fila, destino=False):
    p = _sin_enlaces(fila['destino'] if destino else fila['origen'])
    roots = [Path(op['destino'])] if destino else [Path(r) for r in op['origenes']]
    if not any(p.is_relative_to(_sin_enlaces(r)) and p != r for r in roots):
        raise ValueError('El archivo salió de su raíz autorizada.')
    if not destino:
        st = p.lstat()
        motivo = _exclusion(p, st)
        if motivo or not _coincide(st, fila):
            raise ValueError(motivo or 'El archivo cambió de identidad o metadatos.')
    return p


@contextlib.contextmanager
def _directorios_fijos(paths):
    """En Windows impedir reemplazar ancestros mientras se opera sobre sus hijos."""
    if os.name != 'nt':
        for p in paths:
            _sin_enlaces(p)
        yield
        return
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    handles = []
    unique = {str(q): q for p in paths for q in Path(p).parents if q.exists()}
    try:
        for p in sorted(unique.values(), key=lambda x: len(x.parts)):
            _sin_enlaces(p)
            # FILE_READ_ATTRIBUTES, SHARE_READ|WRITE (sin SHARE_DELETE), OPEN_EXISTING,
            # BACKUP_SEMANTICS|OPEN_REPARSE_POINT. Un ancestro no se puede renombrar.
            h = create(str(p), 0x80, 0x3, None, 3, 0x02200000, None)
            if h == ctypes.c_void_p(-1).value:
                raise OSError(ctypes.get_last_error(), 'No se pudo fijar un directorio; no se modifica nada.')
            handles.append(h)
            _sin_enlaces(p)
        yield
    finally:
        for h in reversed(handles):
            close(h)


@contextlib.contextmanager
def _lectura_fija(p, retirar=False):
    """Windows: negar escritores y borradores concurrentes; borrar luego por el mismo handle."""
    _sin_enlaces(p)
    if os.name != 'nt':
        if retirar:
            raise ValueError('El retiro requiere el bloqueo nativo de Windows en esta versión. La copia sí está disponible.')
        fd = os.open(p, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    else:
        import ctypes
        import msvcrt
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                           wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        h = create(str(p), 0x80000000 | (0x10000 if retirar else 0), 1, None, 3, 0x00200000, None)
        if h == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error(), 'Archivo en uso o sin permisos; no se retira.')
        fd = msvcrt.open_osfhandle(h, os.O_RDONLY | os.O_BINARY)
    with os.fdopen(fd, 'rb') as f:
        st = os.fstat(f.fileno())
        if _exclusion(p, st):
            raise ValueError(_exclusion(p, st))
        yield f


def _hash_handle(f):
    f.seek(0)
    h = hashlib.sha256()
    for bloque in iter(lambda: f.read(CHUNK), b''):
        h.update(bloque)
    return h.hexdigest()


def _retirar_handle(f, destino_q=None):
    import ctypes
    import msvcrt
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    call = kernel.SetFileInformationByHandle
    call.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    call.restype = wintypes.BOOL
    if destino_q is None:
        class Disposition(ctypes.Structure):
            _fields_ = [('DeleteFile', wintypes.BOOL)]
        info = Disposition(True)
        kind = 4
    else:
        value = str(destino_q)
        class Rename(ctypes.Structure):
            _fields_ = [('ReplaceIfExists', ctypes.c_ubyte), ('RootDirectory', wintypes.HANDLE),
                        ('FileNameLength', wintypes.DWORD), ('FileName', wintypes.WCHAR * (len(value) + 1))]
        info = Rename(False, None, len(value.encode('utf-16-le')), value)
        kind = 3
    if not call(msvcrt.get_osfhandle(f.fileno()), kind, ctypes.byref(info), ctypes.sizeof(info)):
        raise OSError(ctypes.get_last_error(), 'Windows no autorizó retirar el archivo; se conserva.')


def _protegidas(base):
    rutas = [Path(base).resolve()]
    if os.name == 'nt':
        rutas += [Path(os.environ.get('WINDIR', 'C:/Windows')), Path('C:/Program Files'),
                  Path('C:/Program Files (x86)'), Path('C:/ProgramData')]
    else:
        rutas += [Path(x) for x in ('/bin', '/boot', '/dev', '/etc', '/lib', '/lib64', '/proc', '/root', '/sbin', '/sys', '/usr', '/var')]
    salida = []
    for r in rutas:
        try:
            salida.append(r.resolve())
        except OSError:
            continue
    return salida


def _ruta(valor, base, escritura=False, raiz_permitida=False):
    """Valida una ruta absoluta de un disco local. Rechaza UNC, sistema, la base y reparse al escribir."""
    if not isinstance(valor, str) or not valor.strip() or len(valor) > 1500:
        raise ValueError('Ubicación no válida.')
    p = Path(valor.strip())
    if not p.is_absolute() or str(p).startswith(('\\\\', '//')):
        raise ValueError('Elige una carpeta de un disco conectado, con ruta absoluta.')
    try:
        resuelta = p.resolve(strict=True)
    except OSError:
        raise ValueError('La ubicación no existe o no se puede abrir: %s' % valor) from None
    if not raiz_permitida and resuelta == Path(resuelta.anchor):
        raise ValueError('No se trabaja sobre la raíz completa de un disco. Elige una carpeta.')
    for prot in _protegidas(base):
        if resuelta == prot or resuelta.is_relative_to(prot) or (escritura and prot.is_relative_to(resuelta)):
            raise ValueError('Esta ubicación está protegida (sistema o datos de Bee-Muse): %s' % resuelta)
    if escritura:
        for parte in [p, *p.parents]:
            if parte.exists() and _es_reparse(parte):
                raise ValueError('No se escribe a través de enlaces o uniones: %s' % parte)
    return resuelta


def _nombre_seguro(p):
    partes = [x.strip(':\\/ ') for x in p.parts]
    nombre = '__'.join(x for x in partes if x)
    nombre = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in nombre)
    return nombre[:120] or 'origen'


# --------------------------------------------------------------------- clasificación

def _motivos_rojo(p, st, contexto):
    riesgos = []
    nombre = p.name.lower()
    partes = [x.lower() for x in p.parts]
    if contexto.get('git'):
        riesgos.append({'tipo': 'git', 'detalle': 'Dentro de un repositorio Git (%s). Retirar aquí deja el repo inconsistente; muévelo con git o excluye.' % contexto['git']})
    if contexto.get('reparse'):
        riesgos.append({'tipo': 'enlace', 'detalle': 'Debajo de un enlace o unión (%s). Otra ruta puede depender de esta ubicación.' % contexto['reparse']})
    if 'appdata' in partes or 'programdata' in partes:
        riesgos.append({'tipo': 'appdata', 'detalle': 'Datos de aplicación: el programa dueño espera encontrarlos aquí.'})
    if '.ollama' in partes or ('models' in partes and 'blobs' in partes):
        riesgos.append({'tipo': 'ollama', 'detalle': 'Modelos de Ollama: moverlos sin cambiar OLLAMA_MODELS rompe los modelos. Copiar y luego apuntar la variable.'})
    if nombre in CREDENCIALES or p.suffix.lower() in CREDENCIAL_EXT or nombre.startswith('.env'):
        riesgos.append({'tipo': 'credencial', 'detalle': 'Parece credencial o llave. No se exporta por defecto.'})
    if p.suffix.lower() in BASES_DATOS:
        riesgos.append({'tipo': 'base-datos', 'detalle': 'Base de datos: puede estar abierta por otro proceso; copiarla en uso da copias corruptas.'})
    if st is not None and time.time() - st.st_mtime < DIAS_RECIENTE * 86400:
        riesgos.append({'tipo': 'reciente', 'detalle': 'Modificado en los últimos %d días: probablemente en uso.' % DIAS_RECIENTE})
    if st is not None and getattr(st, 'st_file_attributes', 0) & (ATTR_OFFLINE | ATTR_RECALL):
        riesgos.append({'tipo': 'nube', 'detalle': 'Archivo de nube sin descargar; copiarlo lo descargaría primero.'})
    return riesgos


def _clasificar_archivo(p, st, contexto):
    riesgos = _motivos_rojo(p, st, contexto)
    if any(r['tipo'] == 'credencial' for r in riesgos):
        return 'rojo', 'credencial', riesgos, False
    if riesgos:
        return 'rojo', 'con dependencias', riesgos, True
    if p.suffix.lower() in PESADOS:
        return 'amarillo', 'pesado copiable', [], True
    return 'amarillo', 'grande sin clasificar', [{'tipo': 'desconocido', 'detalle': 'No reconozco el tipo; cópialo y revisa antes de retirar.'}], True


def _grupo_dir(p, regen, contexto, limite_tiempo):
    """Suma bytes y archivos de una carpeta regenerable sin descender a la lista completa."""
    total = 0
    cuenta = 0
    mayores = []
    parcial = False
    st_mas_reciente = 0
    for actual, dirs, archivos in os.walk(p, followlinks=False):
        if time.monotonic() > limite_tiempo:
            parcial = True
            break
        dirs[:] = [d for d in dirs if not _es_reparse(Path(actual) / d)]
        for nombre in archivos:
            f = Path(actual) / nombre
            try:
                st = f.lstat()
            except OSError:
                parcial = True
                continue
            if f.is_symlink():
                continue
            cuenta += 1
            total += st.st_size
            st_mas_reciente = max(st_mas_reciente, st.st_mtime)
            if len(mayores) < MAX_ARCHIVOS_LISTADOS * 4:
                mayores.append((st.st_size, str(f)))
    mayores.sort(reverse=True)
    riesgos = list(contexto_riesgos(contexto))
    if parcial:
        riesgos.append({'tipo': 'parcial', 'detalle': 'No se terminó de recorrer; el tamaño es una cota inferior.'})
    color = 'rojo' if any(r['tipo'] in ('git', 'enlace') for r in riesgos) else 'verde'
    return {
        'id': _id(), 'tipo': 'carpeta', 'path': str(p), 'nombre': p.name, 'bytes': total, 'archivos': cuenta,
        'color': color, 'categoria': 'regenerable', 'regenerar': regen, 'riesgos': riesgos, 'exportable': True,
        'modificado': st_mas_reciente, 'muestra': [{'path': ruta, 'bytes': b} for b, ruta in mayores[:MAX_ARCHIVOS_LISTADOS]],
        'parcial': parcial,
    }


def contexto_riesgos(contexto):
    if contexto.get('git'):
        yield {'tipo': 'git', 'detalle': 'Dentro de un repositorio Git (%s). node_modules/.venv suelen estar en .gitignore, pero compruébalo antes de retirar.' % contexto['git']}
    if contexto.get('reparse'):
        yield {'tipo': 'enlace', 'detalle': 'Debajo de un enlace o unión (%s).' % contexto['reparse']}


def _recorrer(origen, min_bytes, incluir_ocultos, limite_tiempo, contador):
    grupos = []
    parcial = False
    pila = [(origen, {'git': None, 'reparse': None})]
    while pila:
        actual, contexto = pila.pop()
        if time.monotonic() > limite_tiempo or contador[0] > MAX_ARCHIVOS_RECORRIDO:
            parcial = True
            break
        try:
            entradas = list(os.scandir(actual))
        except OSError:
            grupos.append({'id': _id(), 'tipo': 'carpeta', 'path': str(actual), 'nombre': actual.name, 'bytes': 0, 'archivos': 0,
                           'color': 'gris', 'categoria': 'sin acceso', 'riesgos': [{'tipo': 'acceso', 'detalle': 'No se pudo leer.'}],
                           'exportable': False, 'modificado': 0, 'muestra': [], 'parcial': True})
            continue
        ctx = dict(contexto)
        if any(e.name == '.git' for e in entradas) and not ctx['git']:
            ctx['git'] = str(actual)
        for e in entradas:
            contador[0] += 1
            ruta = Path(e.path)
            nombre = e.name
            if nombre in NUNCA_EXPORTAR:
                continue
            if not incluir_ocultos and nombre.startswith('.') and nombre.lower() not in REGENERABLES and not nombre.lower().startswith('.env'):
                continue
            try:
                es_dir = e.is_dir(follow_symlinks=False)
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            reparse = _es_reparse(ruta)
            if es_dir:
                if reparse:
                    grupos.append({'id': _id(), 'tipo': 'enlace', 'path': str(ruta), 'nombre': nombre, 'bytes': 0, 'archivos': 0,
                                   'color': 'rojo', 'categoria': 'enlace', 'exportable': False, 'modificado': st.st_mtime, 'muestra': [], 'parcial': False,
                                   'riesgos': [{'tipo': 'enlace', 'detalle': 'Es una unión o enlace simbólico; su contenido vive en otra ruta. No se recorre ni se exporta.'}]})
                    continue
                if nombre.lower() in REGENERABLES:
                    grupos.append(_grupo_dir(ruta, REGENERABLES[nombre.lower()], ctx, limite_tiempo))
                    continue
                pila.append((ruta, ctx))
                continue
            if reparse or e.is_symlink():
                continue
            if st.st_size < min_bytes:
                continue
            color, categoria, riesgos, exportable = _clasificar_archivo(ruta, st, ctx)
            grupos.append({'id': _id(), 'tipo': 'archivo', 'path': str(ruta), 'nombre': nombre, 'bytes': st.st_size, 'archivos': 1,
                           'color': color, 'categoria': categoria, 'riesgos': riesgos, 'exportable': exportable,
                           'modificado': st.st_mtime, 'muestra': [{'path': str(ruta), 'bytes': st.st_size}], 'parcial': False})
            if len(grupos) >= MAX_GRUPOS:
                parcial = True
                break
    return grupos, parcial


def _resumen(grupos):
    por_color = {c: {'grupos': 0, 'bytes': 0, 'archivos': 0} for c in COLORES}
    for g in grupos:
        fila = por_color[g['color']]
        fila['grupos'] += 1
        fila['bytes'] += g['bytes']
        fila['archivos'] += g['archivos']
    return {
        'porColor': por_color,
        'recuperable': {
            'seguro': por_color['verde']['bytes'],
            'conCopia': por_color['amarillo']['bytes'],
            'conRevision': por_color['rojo']['bytes'],
            'total': sum(por_color[c]['bytes'] for c in ('verde', 'amarillo', 'rojo')),
        },
        'nota': 'Verde: regenerable por herramienta. Amarillo: copiar y luego retirar. Rojo: copiar, pero retirar solo tras revisar la dependencia. '
                'Las clasificaciones son heurísticas por nombre y atributos, no por contenido ni por quién referencia cada archivo.',
    }


def _limpiar_expirados():
    ahora = time.time()
    for k in list(PLANES):
        if PLANES[k]['expira'] < ahora:
            PLANES.pop(k, None)
    for k in list(OPERACIONES):
        op = OPERACIONES[k]
        if op['expira'] < ahora and op['estado'] in ('preparado', 'fallido', 'cancelado'):
            OPERACIONES.pop(k, None)


# --------------------------------------------------------------------- 1. vista previa

def previsualizar(base, body):
    if not isinstance(body, dict):
        raise ValueError('Solicitud no válida.')
    origenes_raw = body.get('origenes')
    if isinstance(origenes_raw, str):
        origenes_raw = [origenes_raw]
    if not isinstance(origenes_raw, list) or not 1 <= len(origenes_raw) <= 12:
        raise ValueError('Indica entre 1 y 12 carpetas de origen.')
    min_bytes = body.get('minBytes', MIN_BYTES_DEFECTO)
    if isinstance(min_bytes, bool) or not isinstance(min_bytes, int) or not 0 <= min_bytes <= 10 ** 13:
        raise ValueError('minBytes debe ser un entero de bytes.')
    incluir_ocultos = body.get('incluirOcultos', False) is True
    origenes = []
    for valor in origenes_raw:
        p = _ruta(valor, base)
        if not p.is_dir():
            raise ValueError('El origen debe ser una carpeta: %s' % p)
        if any(p == o or p.is_relative_to(o) or o.is_relative_to(p) for o in origenes):
            raise ValueError('Los orígenes se solapan: %s' % p)
        origenes.append(p)
    limite = time.monotonic() + MAX_SEGUNDOS_RECORRIDO
    contador = [0]
    grupos = []
    parcial = False
    for o in origenes:
        g, pa = _recorrer(o, min_bytes, incluir_ocultos, limite, contador)
        grupos.extend(g)
        parcial = parcial or pa
    grupos.sort(key=lambda g: (COLORES.index(g['color']), -g['bytes']))
    key = _id()
    with LOCK:
        _limpiar_expirados()
        PLANES[key] = {'id': key, 'origenes': [str(o) for o in origenes], 'grupos': grupos, 'minBytes': min_bytes,
                       'creado': _ahora(), 'expira': time.time() + EXPIRA_PLAN}
    return {
        'id': key, 'modo': 'vista previa', 'origenes': [str(o) for o in origenes], 'minBytes': min_bytes,
        'grupos': grupos, 'parcial': parcial, 'entradasRecorridas': contador[0], 'expiraEn': EXPIRA_PLAN,
        'resumen': _resumen(grupos),
        'limites': 'No se copió, movió ni borró nada. Archivos menores a minBytes fuera de carpetas regenerables no se listan. '
                   '.git nunca se exporta. Enlaces y uniones no se recorren.',
    }


# --------------------------------------------------------------------- 2. preparar

def _manifiesto_grupo(g):
    """Lista real de archivos (ruta, bytes, mtime_ns) del grupo, en el momento de preparar."""
    raiz = Path(g['path'])
    filas = []
    if g['tipo'] == 'archivo':
        st = raiz.lstat()
        filas.append({'origen': str(raiz), 'relativo': raiz.name, 'bytes': st.st_size, 'mtime': st.st_mtime_ns})
        return filas
    for actual, dirs, archivos in os.walk(raiz, followlinks=False):
        dirs[:] = [d for d in dirs if not _es_reparse(Path(actual) / d) and d not in NUNCA_EXPORTAR]
        for nombre in archivos:
            f = Path(actual) / nombre
            if f.is_symlink() or _es_reparse(f):
                continue
            try:
                st = f.lstat()
            except OSError:
                raise ValueError('No se pudo leer %s. Prepara otra vez o excluye el grupo.' % f) from None
            filas.append({'origen': str(f), 'relativo': str(f.relative_to(raiz)), 'bytes': st.st_size, 'mtime': st.st_mtime_ns})
    return filas


def preparar(base, body):
    if not isinstance(body, dict):
        raise ValueError('Solicitud no válida.')
    plan_id = body.get('plan')
    seleccion = body.get('seleccion')
    if not isinstance(plan_id, str) or not isinstance(seleccion, list) or not seleccion:
        raise ValueError('Falta la vista previa o la selección de grupos.')
    if not all(isinstance(s, str) for s in seleccion):
        raise ValueError('La selección debe ser una lista de identificadores.')
    with LOCK:
        _limpiar_expirados()
        plan = PLANES.get(plan_id)
        if not plan or plan['expira'] < time.time():
            raise ValueError('La vista previa venció o no existe. Vuelve a previsualizar.')
        grupos = {g['id']: g for g in plan['grupos']}
        origenes = [Path(o) for o in plan['origenes']]
    destino = _ruta(body.get('destino'), base, escritura=True)
    if not destino.is_dir():
        raise ValueError('El destino debe ser una carpeta existente.')
    for o in origenes:
        if destino == o or destino.is_relative_to(o) or o.is_relative_to(destino):
            raise ValueError('El destino no puede estar dentro del origen ni contenerlo: %s' % destino)
    elegidos = []
    for s in seleccion:
        g = grupos.get(s)
        if not g:
            raise ValueError('Un grupo seleccionado ya no está en la vista previa.')
        if not g['exportable']:
            raise ValueError('«%s» no es exportable (%s).' % (g['nombre'], g['categoria']))
        elegidos.append(g)
    archivos = []
    usados = set()
    for g in elegidos:
        # Archivos sueltos van a una carpeta con el nombre de su carpeta origen; las
        # carpetas regenerables, a una propia. Nombres repetidos reciben sufijo.
        if g['tipo'] == 'archivo':
            c = 'archivos__' + _nombre_seguro(Path(g['path']).parent)
        else:
            carpeta = _nombre_seguro(Path(g['path']))
            n, c = 2, carpeta
            while c in usados:
                c = '%s-%d' % (carpeta, n)
                n += 1
            usados.add(c)
        for fila in _manifiesto_grupo(g):
            archivos.append({**fila, 'grupo': g['id'], 'destino': str(destino / c / fila['relativo'])})
    total = sum(a['bytes'] for a in archivos)
    libre = shutil.disk_usage(destino).free
    margen = int(total * 1.02) + 64 * 1024 * 1024
    if libre < margen:
        raise ValueError('No hay espacio suficiente en el destino: libre %d bytes, se necesitan ~%d.' % (libre, margen))
    for a in archivos:
        if Path(a['destino']).exists():
            raise ValueError('Ya existe en el destino y no se sobrescribe: %s' % a['destino'])
    key = _id()
    op = {
        'id': key, 'plan': plan_id, 'destino': str(destino), 'origenes': [str(o) for o in origenes],
        'grupos': [{k: g[k] for k in ('id', 'tipo', 'path', 'nombre', 'bytes', 'archivos', 'color', 'categoria', 'riesgos')} for g in elegidos],
        'archivos': archivos, 'bytes': total, 'estado': 'preparado', 'creado': _ahora(), 'expira': time.time() + EXPIRA_OPERACION,
        'progreso': {'archivos': 0, 'bytes': 0, 'fallidos': 0}, 'cancelar': threading.Event(), 'hilo': None, 'verificado': False, 'error': None,
    }
    with LOCK:
        OPERACIONES[key] = op
    return {'ok': True, **_vista_operacion(op), 'espacioLibreDestino': libre,
            'nota': 'Nada se ha copiado todavía. Los originales no se tocan en ningún paso sin tu autorización expresa.'}


def _vista_operacion(op):
    return {
        'operacion': op['id'], 'estado': op['estado'], 'destino': op['destino'], 'origenes': op['origenes'],
        'grupos': op['grupos'], 'totalArchivos': len(op['archivos']), 'bytes': op['bytes'],
        'progreso': dict(op['progreso']), 'verificado': op['verificado'], 'error': op['error'],
        'rojos': [g['id'] for g in op['grupos'] if g['color'] == 'rojo'],
        'recibo': op.get('reciboPath'),
    }


# --------------------------------------------------------------------- 3. copiar + verificar

def _hash_archivo(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for bloque in iter(lambda: f.read(CHUNK), b''):
            h.update(bloque)
    return h.hexdigest()


def _copiar_uno(fila):
    origen = Path(fila['origen'])
    destino = Path(fila['destino'])
    st = origen.lstat()
    if st.st_size != fila['bytes'] or st.st_mtime_ns != fila['mtime']:
        raise ValueError('cambió desde la preparación')
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + '.superexport.tmp')
    h = hashlib.sha256()
    with open(origen, 'rb') as src, open(temporal, 'wb') as dst:
        for bloque in iter(lambda: src.read(CHUNK), b''):
            h.update(bloque)
            dst.write(bloque)
        dst.flush()
        os.fsync(dst.fileno())
    sha_origen = h.hexdigest()
    try:
        shutil.copystat(origen, temporal, follow_symlinks=False)
    except OSError:
        pass
    os.replace(temporal, destino)
    sha_destino = _hash_archivo(destino)
    despues = origen.lstat()
    if despues.st_size != st.st_size or despues.st_mtime_ns != st.st_mtime_ns:
        raise ValueError('cambió durante la copia')
    return sha_origen, sha_destino


def _escribir_recibo(base, op):
    carpeta = Path(base) / RECIBOS_DIR
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / (op['id'] + '.json')
    datos = {
        'version': 1, 'id': op['id'], 'estado': op['estado'], 'creado': op['creado'], 'actualizado': _ahora(),
        'destino': op['destino'], 'origenes': op['origenes'], 'grupos': op['grupos'], 'bytes': op['bytes'],
        'verificado': op['verificado'], 'error': op['error'], 'retiro': op.get('retiro'),
        'archivos': [{k: a.get(k) for k in ('origen', 'destino', 'bytes', 'mtime', 'grupo', 'shaOrigen', 'shaDestino', 'estado', 'detalle', 'retirado')} for a in op['archivos']],
    }
    temporal = destino.with_suffix('.tmp')
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporal, destino)
    op['reciboPath'] = str(destino)
    return str(destino)


def _trabajo_copia(base, op):
    try:
        for fila in op['archivos']:
            if op['cancelar'].is_set():
                fila['estado'] = 'cancelado'
                continue
            try:
                sha_o, sha_d = _copiar_uno(fila)
                fila['shaOrigen'] = sha_o
                fila['shaDestino'] = sha_d
                fila['estado'] = 'verificado' if sha_o == sha_d else 'hash-distinto'
                if sha_o != sha_d:
                    op['progreso']['fallidos'] += 1
                    fila['detalle'] = 'El SHA-256 del destino releído no coincide con el del origen.'
            except (OSError, ValueError) as exc:
                fila['estado'] = 'fallido'
                fila['detalle'] = str(exc)
                op['progreso']['fallidos'] += 1
            op['progreso']['archivos'] += 1
            op['progreso']['bytes'] += fila['bytes']
        if op['cancelar'].is_set():
            op['estado'] = 'cancelado'
            op['error'] = 'Cancelado por la persona. Lo ya copiado se conserva en el destino; los originales no se tocaron.'
        elif op['progreso']['fallidos']:
            op['estado'] = 'fallido'
            op['error'] = '%d archivo(s) no se pudieron copiar o verificar. Los originales no se tocaron.' % op['progreso']['fallidos']
        else:
            op['estado'] = 'copiado'
            op['verificado'] = True
    except Exception as exc:  # pragma: no cover - fallo inesperado del hilo
        op['estado'] = 'fallido'
        op['error'] = 'Error inesperado: %s' % exc
    finally:
        with LOCK:
            _escribir_recibo(base, op)


def copiar(base, body, sincrono=False):
    if not isinstance(body, dict):
        raise ValueError('Solicitud no válida.')
    key = body.get('operacion')
    with LOCK:
        _limpiar_expirados()
        op = OPERACIONES.get(key) if isinstance(key, str) else None
        if not op:
            raise ValueError('La operación venció o no existe. Prepara otra vez.')
        if op['estado'] != 'preparado':
            raise ValueError('Esta operación ya está en estado «%s».' % op['estado'])
        if body.get('confirmarCopia') is not True:
            raise ValueError('Confirma la copia desde la página (confirmarCopia).')
        op['estado'] = 'copiando'
        op['expira'] = time.time() + 24 * 3600
        hilo = threading.Thread(target=_trabajo_copia, args=(base, op), name='superexport-' + op['id'], daemon=True)
        op['hilo'] = hilo
    hilo.start()
    if sincrono:
        hilo.join()
    return {'ok': True, **_vista_operacion(op)}


def cancelar(base, body):
    if not isinstance(body, dict):
        raise ValueError('Solicitud no válida.')
    key = body.get('operacion')
    with LOCK:
        op = OPERACIONES.get(key) if isinstance(key, str) else None
        if not op:
            raise ValueError('Esa operación no existe.')
        if op['estado'] != 'copiando':
            raise ValueError('Solo se cancela una copia en curso.')
        op['cancelar'].set()
    return {'ok': True, **_vista_operacion(op)}


def estado(base, key):
    with LOCK:
        op = OPERACIONES.get(key) if isinstance(key, str) else None
    if not op:
        return {**_recibo_de_disco(base, key), 'enMemoria': False}
    return {**_vista_operacion(op), 'enMemoria': True}


def esperar(base, key, timeout=600):
    """Para pruebas y herramientas: bloquea hasta que termine la copia."""
    with LOCK:
        op = OPERACIONES.get(key)
    if op and op['hilo'] is not None:
        op['hilo'].join(timeout)
    return estado(base, key)


# --------------------------------------------------------------------- recibos

def _recibo_de_disco(base, key):
    if not isinstance(key, str) or not key or any(c not in '0123456789abcdef' for c in key) or len(key) != 16:
        raise ValueError('Identificador de operación no válido.')
    p = Path(base) / RECIBOS_DIR / (key + '.json')
    if not p.exists():
        raise ValueError('No hay recibo para esa operación.')
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ValueError('El recibo existe pero no se pudo leer.') from None


def recibo(base, key):
    return _recibo_de_disco(base, key)


def recibos(base):
    carpeta = Path(base) / RECIBOS_DIR
    filas = []
    if carpeta.is_dir():
        for p in carpeta.glob('*.json'):
            try:
                r = json.loads(p.read_text(encoding='utf-8'))
                filas.append({k: r.get(k) for k in ('id', 'estado', 'creado', 'actualizado', 'destino', 'origenes', 'bytes', 'verificado', 'retiro')})
            except (OSError, ValueError):
                filas.append({'id': p.stem, 'estado': 'ilegible'})
    filas.sort(key=lambda r: r.get('actualizado') or '', reverse=True)
    return filas[:200]


def status(base):
    with LOCK:
        _limpiar_expirados()
        activas = [_vista_operacion(op) for op in OPERACIONES.values()]
    return {
        'operaciones': activas, 'recibos': recibos(base),
        'limites': {'minBytesDefecto': MIN_BYTES_DEFECTO, 'maxGrupos': MAX_GRUPOS, 'expiraPlan': EXPIRA_PLAN,
                    'fraseRetirar': FRASE_RETIRAR, 'fraseBorrar': FRASE_BORRAR, 'carpetaCuarentena': CARPETA_CUARENTENA},
        'storage': 'Recibos en %s/ junto a la biblioteca. Vistas previas y operaciones viven en memoria y expiran.' % RECIBOS_DIR,
        'note': 'Vista previa por defecto. Copiar solo con confirmación. Retirar originales solo con frase exacta, recibo verificado y reverificación en el momento. No se promete que retirar no rompa dependencias desconocidas.',
    }


# --------------------------------------------------------------------- 4. retirar (candado)

def _reverificar(op, fila):
    origen = Path(fila['origen'])
    destino = Path(fila['destino'])
    if fila.get('estado') != 'verificado':
        return 'no quedó verificado en la copia'
    try:
        st = origen.lstat()
    except OSError:
        return 'el origen ya no está'
    if st.st_size != fila['bytes'] or st.st_mtime_ns != fila['mtime']:
        return 'el origen cambió después de la copia'
    if not destino.is_file():
        return 'la copia ya no está en el destino'
    if destino.lstat().st_size != fila['bytes']:
        return 'la copia cambió de tamaño'
    if _hash_archivo(destino) != fila['shaOrigen']:
        return 'la copia ya no coincide con el SHA-256 registrado'
    return None


def retirar(base, body):
    if not isinstance(body, dict):
        raise ValueError('Solicitud no válida.')
    key = body.get('operacion')
    modo = body.get('modo', 'cuarentena')
    if modo not in ('cuarentena', 'borrar'):
        raise ValueError('El modo debe ser cuarentena o borrar.')
    if body.get('confirmar') is not True:
        raise ValueError('Retirar originales requiere confirmación explícita (confirmar).')
    frase = FRASE_BORRAR if modo == 'borrar' else FRASE_RETIRAR
    if body.get('frase') != frase:
        raise ValueError('Escribe exactamente la frase «%s» para continuar.' % frase)
    aceptados = body.get('aceptarRiesgos', [])
    if not isinstance(aceptados, list) or not all(isinstance(x, str) for x in aceptados):
        raise ValueError('aceptarRiesgos debe ser una lista de identificadores de grupo.')
    with LOCK:
        op = OPERACIONES.get(key) if isinstance(key, str) else None
        if not op:
            raise ValueError('La operación no está en memoria. Solo se retira en la misma sesión de la copia, con su recibo.')
        if op['estado'] != 'copiado' or not op['verificado']:
            raise ValueError('Solo se retiran originales de una copia terminada y verificada (estado actual: %s).' % op['estado'])
        if not op.get('reciboPath') or not Path(op['reciboPath']).exists():
            raise ValueError('Falta el recibo de la copia. No se retira nada sin comprobante.')
        rojos = [g for g in op['grupos'] if g['color'] == 'rojo' and g['id'] not in aceptados]
        if rojos:
            raise ValueError('Hay %d grupo(s) en rojo sin aceptar su riesgo: %s. Acéptalos uno por uno o exclúyelos.' % (len(rojos), ', '.join(g['nombre'] for g in rojos[:5])))
        problemas = []
        for fila in op['archivos']:
            motivo = _reverificar(op, fila)
            if motivo:
                problemas.append({'origen': fila['origen'], 'motivo': motivo})
        if problemas:
            op['retiro'] = {'modo': modo, 'estado': 'rechazado', 'cuando': _ahora(), 'problemas': problemas[:50]}
            _escribir_recibo(base, op)
            raise ValueError('La reverificación falló en %d archivo(s); no se retiró nada. Primer caso: %s (%s).' % (len(problemas), problemas[0]['origen'], problemas[0]['motivo']))
        op['estado'] = 'retirando'
        retirados = 0
        fallidos = []
        cuarentenas = {}
        for fila in op['archivos']:
            origen = Path(fila['origen'])
            try:
                if modo == 'cuarentena':
                    raiz = Path(origen.anchor) if os.name == 'nt' else _raiz_origen(op, origen)
                    cuarentena = raiz / CARPETA_CUARENTENA / op['id']
                    cuarentenas[str(raiz)] = str(cuarentena)
                    rel = origen.relative_to(Path(origen.anchor)) if os.name == 'nt' else origen.relative_to(raiz)
                    destino_q = cuarentena / rel
                    destino_q.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(origen, destino_q)
                    fila['retirado'] = {'modo': modo, 'a': str(destino_q)}
                else:
                    os.remove(origen)
                    fila['retirado'] = {'modo': modo}
                retirados += 1
            except OSError as exc:
                fallidos.append({'origen': str(origen), 'detalle': str(exc)})
                fila['retirado'] = {'modo': modo, 'error': str(exc)}
        vacias = _retirar_carpetas_vacias(op) if not fallidos else 0
        op['estado'] = 'retirado' if not fallidos else 'retiro-parcial'
        op['retiro'] = {'modo': modo, 'estado': op['estado'], 'cuando': _ahora(), 'archivos': retirados, 'fallidos': fallidos[:50],
                        'carpetasVacias': vacias, 'cuarentena': cuarentenas, 'bytesLiberados': op['bytes'] if modo == 'borrar' and not fallidos else 0}
        ruta_recibo = _escribir_recibo(base, op)
    return {'ok': True, **_vista_operacion(op), 'retiro': op['retiro'], 'recibo': ruta_recibo,
            'nota': ('Los originales están en cuarentena en el mismo disco; eso no libera espacio hasta que borres esa carpeta.' if modo == 'cuarentena'
                     else 'Originales borrados. Lo que quedó fue copiado y verificado por SHA-256; dependencias desconocidas no se garantizan.')}


def _raiz_origen(op, archivo):
    for o in op['origenes']:
        if archivo.is_relative_to(Path(o)):
            return Path(o)
    return archivo.parent


def _retirar_carpetas_vacias(op):
    """Tras retirar, quita las carpetas regenerables que quedaron vacías (solo las del grupo, de abajo hacia arriba)."""
    cuenta = 0
    for g in op['grupos']:
        if g['tipo'] != 'carpeta':
            continue
        raiz = Path(g['path'])
        if not raiz.exists():
            continue
        for actual, dirs, archivos in os.walk(raiz, topdown=False):
            try:
                if not os.listdir(actual):
                    os.rmdir(actual)
                    cuenta += 1
            except OSError:
                continue
    return cuenta
