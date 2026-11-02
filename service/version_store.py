"""Versionado reversible de HTML: bytes, manifiesto, recursos y restauración.

Reglas que no se rompen:
- El archivo original del usuario nunca se escribe. Guardar versión solo lee.
- Cada versión tiene un identificador estable derivado del SHA-256 de sus
  bytes. Dos guardados del mismo contenido dan el mismo `versionId`.
- El manifiesto declara qué recursos (CSS/JS/imágenes) referencia el HTML y
  si cada uno existe de verdad en disco, con su propia huella.
- Si el HTML vive dentro de un repositorio Git se anota el commit; si no hay
  repositorio se dice explícitamente "sin repositorio". No se inventa nada.
- Restaurar devuelve los bytes idénticos (SHA-256 comprobado) y puede escribir
  la copia en un destino distinto. Nunca toca el original ni la versión.
"""
import datetime as dt
import hashlib
import html as html_module
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

CARPETA = 'versiones'
CHUNK = 1024 * 1024
MAX_RECURSOS = 200
GIT_TIMEOUT = 5
SKIP_PREFIX = ('http://', 'https://', '//', 'data:', 'mailto:', 'javascript:', '#', 'about:', 'blob:')
TAG_RE = re.compile(r'(?is)<(link|script|img)\b([^>]*)>')
HREF_RE = re.compile(r'(?is)\bhref\s*=\s*(["\'])(.*?)\1')
SRC_RE = re.compile(r'(?is)\bsrc\s*=\s*(["\'])(.*?)\1')
SCOPE = ('Archivo HTML y manifiesto de recursos referenciados. No copia CSS, imágenes, '
         'JavaScript ni backend: solo registra si existen y su huella.')


def _ahora():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='microseconds')


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(CHUNK), b''):
            digest.update(block)
    return digest.hexdigest()


def version_dir(base, record_id):
    return Path(base) / CARPETA / str(record_id)


def version_id(digest):
    return 'v-' + digest[:16]


def _escribir_atomico(destino, data):
    destino = Path(destino)
    temporal = destino.with_name('.%s.%d.%s.tmp' % (destino.name, os.getpid(), uuid.uuid4().hex[:8]))
    temporal.write_bytes(data)
    for intento in range(4):
        try:
            os.replace(temporal, destino)
            return destino
        except OSError:
            if intento == 3:
                temporal.unlink(missing_ok=True)
                raise
            import time
            time.sleep(0.05 * (intento + 1))


def extraer_referencias(texto):
    """Devuelve las referencias locales declaradas por el HTML, sin repetir."""
    vistas = set()
    salida = []
    for etiqueta, atributos in TAG_RE.findall(texto):
        etiqueta = etiqueta.lower()
        patron = HREF_RE if etiqueta == 'link' else SRC_RE
        coincidencia = patron.search(atributos)
        if not coincidencia:
            continue
        valor = html_module.unescape(coincidencia.group(2)).strip()
        if not valor or valor.lower().startswith(SKIP_PREFIX):
            continue
        tipo = {'link': 'css', 'script': 'js', 'img': 'imagen'}[etiqueta]
        clave = (tipo, valor)
        if clave in vistas:
            continue
        vistas.add(clave)
        salida.append({'tipo': tipo, 'referencia': valor})
        if len(salida) >= MAX_RECURSOS:
            break
    return salida


def _recurso_en_disco(referencia, raiz):
    limpio = referencia.split('?', 1)[0].split('#', 1)[0]
    limpio = limpio.replace('/', os.sep)
    candidato = (raiz / limpio).resolve()
    try:
        dentro = candidato.is_relative_to(raiz.resolve())
    except (OSError, ValueError):
        dentro = False
    if not dentro:
        return {'presente': False, 'motivo': 'ruta fuera de la carpeta del HTML'}
    if not candidato.is_file():
        return {'presente': False, 'motivo': 'no existe en disco'}
    try:
        return {'presente': True, 'bytes': candidato.stat().st_size, 'sha256': sha256_file(candidato)}
    except OSError as exc:
        return {'presente': False, 'motivo': 'no se pudo leer (%s)' % exc.__class__.__name__}


def manifiesto_recursos(texto, origen):
    raiz = Path(origen).resolve().parent
    declarados = []
    for referencia in extraer_referencias(texto):
        fila = dict(referencia)
        fila.update(_recurso_en_disco(referencia['referencia'], raiz))
        declarados.append(fila)
    presentes = sum(1 for fila in declarados if fila.get('presente'))
    return {
        'escaneado': True,
        'carpeta': str(raiz),
        'declarados': declarados,
        'resumen': {
            'referenciados': len(declarados),
            'presentes': presentes,
            'ausentes': len(declarados) - presentes,
        },
        'nota': 'Externos (http, https, data) no se inspeccionan ni se descargan; no aparecen en esta lista.',
    }


def _git(args, cwd):
    try:
        proceso = subprocess.run(['git'] + args, cwd=str(cwd), capture_output=True,
                                 text=True, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    if proceso.returncode != 0:
        return None
    return proceso.stdout.strip()


def relacion_repositorio(origen):
    """Lee (solo lectura) el repositorio Git que contiene el archivo, si hay."""
    origen = Path(origen).resolve()
    for candidato in [origen.parent, *origen.parent.parents]:
        if not (candidato / '.git').exists():
            continue
        commit = _git(['rev-parse', '--verify', 'HEAD'], candidato)
        if not commit:
            return {'tipo': 'git', 'raiz': str(candidato), 'commit': None,
                    'mensaje': 'repositorio sin commit inicial'}
        rama = _git(['rev-parse', '--abbrev-ref', 'HEAD'], candidato) or ''
        try:
            relativo = origen.relative_to(candidato).as_posix()
        except ValueError:
            relativo = origen.name
        rastreado = _git(['ls-files', '--error-unmatch', '--', relativo], candidato)
        cambios = _git(['status', '--porcelain', '--', relativo], candidato)
        return {
            'tipo': 'git',
            'raiz': str(candidato),
            'commit': commit,
            'rama': rama,
            'archivo': relativo,
            'rastreado': bool(rastreado),
            'estadoLocal': 'con cambios' if cambios else 'sin cambios',
            'mensaje': 'commit leído en solo lectura',
        }
    return {'tipo': 'ninguno', 'commit': None, 'mensaje': 'sin repositorio'}


def construir_manifiesto(origen, raw, digest, texto):
    return {
        'versionId': version_id(digest),
        'sha256': digest,
        'fingerprint': 'sha256:' + digest,
        'bytes': len(raw),
        'source': str(origen),
        'savedAt': _ahora(),
        'archivoVersion': digest + '.html',
        'scope': SCOPE,
        'recursos': manifiesto_recursos(texto, origen),
        'repositorio': relacion_repositorio(origen),
        'restauracion': {
            'metodo': 'version_store.restore_version',
            'verificadaPor': 'sha256 de bytes',
        },
    }


def save_version(base, record, raw=None):
    """Guarda (o reutiliza) una versión del HTML. Nunca escribe el original."""
    origen = Path(record['path'])
    record_id = str(record['id'])
    if raw is None:
        raw = origen.read_bytes()
    digest = sha256_bytes(raw)
    carpeta = version_dir(base, record_id)
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / (digest + '.html')
    manifiesto_path = carpeta / (digest + '.json')
    ya_existia = archivo.exists() and manifiesto_path.exists()
    if not ya_existia:
        texto = raw.decode('utf-8', errors='replace')
        manifiesto = construir_manifiesto(origen, raw, digest, texto)
        _escribir_atomico(archivo, raw)
        _escribir_atomico(manifiesto_path, json.dumps(manifiesto, ensure_ascii=False, indent=2).encode('utf-8'))
    else:
        manifiesto = leer_manifiesto(manifiesto_path)
    return {
        'ok': True,
        'alreadyExists': ya_existia,
        'versionId': manifiesto.get('versionId') or version_id(digest),
        'sha256': digest,
        'bytes': len(raw),
        'manifiesto': manifiesto,
    }


def leer_manifiesto(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _localizar(carpeta, identificador):
    identificador = str(identificador or '').strip()
    if not identificador:
        raise ValueError('Falta la versión que quieres restaurar.')
    if identificador.startswith('v-'):
        prefijo = identificador[2:]
        if not re.fullmatch(r'[0-9a-f]{8,64}', prefijo):
            raise ValueError('El identificador de versión no es válido.')
        candidatos = [p for p in carpeta.glob('*.html') if p.stem.startswith(prefijo)]
    else:
        if not re.fullmatch(r'[0-9a-f]{64}', identificador):
            raise ValueError('La huella de la versión no es válida.')
        candidatos = [carpeta / (identificador + '.html')] if (carpeta / (identificador + '.html')).exists() else []
    if not candidatos:
        raise ValueError('Esa versión no está guardada en este equipo.')
    if len(candidatos) > 1:
        raise ValueError('Hay más de una versión con ese prefijo; usa la huella completa.')
    return candidatos[0]


def restore_version(base, record_id, identificador, destino=None):
    """Devuelve los bytes exactos de la versión y, si se pide, los copia aparte.

    Nunca escribe sobre el archivo original ni sobre la versión guardada.
    """
    carpeta = version_dir(base, record_id)
    archivo = _localizar(carpeta, identificador)
    data = archivo.read_bytes()
    digest = sha256_bytes(data)
    if digest != archivo.stem:
        raise ValueError('La versión guardada no coincide con su propia huella; no la restauro.')
    manifiesto_path = carpeta / (archivo.stem + '.json')
    esperado = None
    if manifiesto_path.exists():
        try:
            esperado = leer_manifiesto(manifiesto_path).get('sha256')
        except (OSError, ValueError):
            esperado = None
    if esperado and esperado != digest:
        raise ValueError('El manifiesto no coincide con los bytes guardados; no restauro.')
    resultado = {
        'ok': True,
        'versionId': version_id(digest),
        'sha256': digest,
        'bytes': len(data),
        'verificado': True,
        'destino': None,
    }
    if destino is not None:
        destino = Path(destino)
        origen_original = None
        if manifiesto_path.exists():
            try:
                origen_original = leer_manifiesto(manifiesto_path).get('source')
            except (OSError, ValueError):
                origen_original = None
        if origen_original and os.path.normcase(str(destino.resolve())) == os.path.normcase(str(Path(origen_original).resolve())):
            raise ValueError('Restaurar no sobrescribe el original. Elige otro destino.')
        if os.path.normcase(str(destino.resolve())) == os.path.normcase(str(archivo.resolve())):
            raise ValueError('Restaurar no sobrescribe la versión guardada. Elige otro destino.')
        destino.parent.mkdir(parents=True, exist_ok=True)
        _escribir_atomico(destino, data)
        resultado['destino'] = str(destino)
        resultado['destinoSha256'] = sha256_file(destino)
    return data, resultado


def history(base, record_id):
    """Historial con identificadores estables y huella, ordenado por guardado."""
    carpeta = version_dir(base, record_id)
    filas = []
    if carpeta.exists():
        for path in carpeta.glob('*.json'):
            try:
                fila = leer_manifiesto(path)
            except (OSError, ValueError):
                continue
            digest = fila.get('sha256') or path.stem
            filas.append({
                'versionId': fila.get('versionId') or version_id(digest),
                'sha256': digest,
                'fingerprint': fila.get('fingerprint') or 'sha256:' + digest,
                'bytes': fila.get('bytes'),
                'savedAt': fila.get('savedAt'),
                'recursos': (fila.get('recursos') or {}).get('resumen'),
                'repositorio': fila.get('repositorio'),
                'scope': fila.get('scope'),
            })
    filas.sort(key=lambda f: (f.get('savedAt') or '', f['versionId']))
    return filas
