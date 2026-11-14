"""Voz de respuesta para Muse: la del equipo (navegador) o ElevenLabs.

La clave de ElevenLabs se guarda cifrada para este usuario de Windows (DPAPI, igual que Jules)
o se toma de ELEVENLABS_API_KEY. Nunca se escribe en el repositorio, en logs ni en respuestas.
"""
import json
import os
import threading
import urllib.error
import urllib.request
import uuid

import jules_connector

FILE_NAME = 'voz.json'
API = 'https://api.elevenlabs.io/v1'
MODELO = 'eleven_multilingual_v2'
LOCK = threading.Lock()
MAX_TEXTO = 2000
PROVEEDORES = ('sistema', 'elevenlabs')


def key_path(base):
    return base / '.credentials' / 'elevenlabs.dpapi'


def valid_key(value):
    return isinstance(value, str) and 16 <= len(value) <= 256 and all(33 <= ord(c) <= 126 for c in value)


def read_key(base):
    value = os.environ.get('ELEVENLABS_API_KEY', '').strip()
    if value:
        if not valid_key(value):
            raise ValueError('La variable ELEVENLABS_API_KEY no tiene un formato válido. No se envió la clave.')
        return value, 'environment'
    p = key_path(base)
    if p.exists():
        try:
            value = jules_connector.crypt(p.read_bytes(), True).decode('utf-8')
        except (OSError, UnicodeError, ValueError):
            raise ValueError('No se pudo abrir la clave cifrada de ElevenLabs. Vuelve a guardarla para este usuario de Windows.') from None
        if not valid_key(value):
            raise ValueError('La clave guardada no tiene un formato válido. Vuelve a añadirla.')
        return value, 'windows'
    return None, None


def _config(base):
    p = base / FILE_NAME
    data = {'proveedor': 'sistema', 'voz': None, 'vozNombre': None}
    if p.exists():
        try:
            leido = json.loads(p.read_text(encoding='utf-8'))
            if isinstance(leido, dict):
                data.update({k: leido.get(k) for k in data if k in leido})
        except (OSError, ValueError):
            pass
    if data['proveedor'] not in PROVEEDORES:
        data['proveedor'] = 'sistema'
    return data


def _save_config(base, data):
    dest = base / FILE_NAME
    temp = dest.with_name('.%s.%d.%s.tmp' % (FILE_NAME, os.getpid(), uuid.uuid4().hex[:8]))
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(temp, dest)


def status(base):
    configurado = bool(os.environ.get('ELEVENLABS_API_KEY', '').strip()) or key_path(base).exists()
    data = _config(base)
    return {**data, 'configurado': configurado, 'modelo': MODELO,
            'almacen': 'Variable de entorno' if os.environ.get('ELEVENLABS_API_KEY', '').strip() else ('Windows DPAPI · usuario actual' if os.name == 'nt' else 'Variable de entorno'),
            'nota': 'La clave solo sale de este equipo hacia ElevenLabs cuando pides leer una respuesta. Sin clave, se usa la voz del equipo.'}


def guardar_clave(base, value):
    if not valid_key(value):
        raise ValueError('Pega únicamente la clave API de ElevenLabs, sin espacios ni instrucciones.')
    encrypted = jules_connector.crypt(value.encode('utf-8'))
    with LOCK:
        p = key_path(base)
        p.parent.mkdir(exist_ok=True)
        temp = p.with_suffix('.tmp')
        temp.write_bytes(encrypted)
        os.replace(temp, p)
    return {'ok': True, **status(base)}


def olvidar_clave(base):
    with LOCK:
        key_path(base).unlink(missing_ok=True)
        data = _config(base)
        if data['proveedor'] == 'elevenlabs':
            data['proveedor'] = 'sistema'
            _save_config(base, data)
    return {'ok': True, **status(base)}


def guardar_config(base, data):
    data = data or {}
    proveedor = data.get('proveedor')
    if proveedor not in PROVEEDORES:
        raise ValueError('Elige la voz del equipo o ElevenLabs.')
    voz = data.get('voz')
    if voz is not None and (not isinstance(voz, str) or not voz.isalnum() or len(voz) > 64):
        raise ValueError('Elige una voz de la lista.')
    nombre = data.get('vozNombre')
    if nombre is not None and (not isinstance(nombre, str) or len(nombre) > 80 or any(ord(c) < 32 for c in nombre)):
        nombre = None
    if proveedor == 'elevenlabs':
        if read_key(base)[0] is None:
            raise ValueError('Guarda primero tu clave de ElevenLabs.')
        if not voz:
            raise ValueError('Elige una voz de ElevenLabs.')
    with LOCK:
        _save_config(base, {'proveedor': proveedor, 'voz': voz, 'vozNombre': nombre})
    return {'ok': True, **status(base)}


def _peticion(base, ruta, cuerpo=None, aceptar='application/json', timeout=40):
    key, _ = read_key(base)
    if not key:
        raise ValueError('Guarda primero tu clave de ElevenLabs.')
    datos = json.dumps(cuerpo).encode('utf-8') if cuerpo is not None else None
    req = urllib.request.Request(API + ruta, data=datos, method='POST' if datos is not None else 'GET',
                                 headers={'xi-api-key': key, 'Accept': aceptar, **({'Content-Type': 'application/json'} if datos is not None else {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as respuesta:
            return respuesta.read()
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise ValueError('ElevenLabs rechazó la clave. Revísala o guarda otra.') from None
        if error.code == 429:
            raise ValueError('ElevenLabs está limitando las solicitudes. Inténtalo en un momento.') from None
        raise ValueError('ElevenLabs respondió con un error (%d).' % error.code) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError('No se pudo contactar a ElevenLabs. Revisa tu conexión.') from None


def voces(base):
    raw = _peticion(base, '/voices', timeout=30)
    try:
        data = json.loads(raw)
    except ValueError:
        raise ValueError('ElevenLabs devolvió una lista que no se pudo leer.') from None
    lista = []
    for voz in data.get('voices') or []:
        ident = voz.get('voice_id')
        if isinstance(ident, str) and ident.isalnum():
            etiquetas = voz.get('labels') or {}
            lista.append({'id': ident, 'nombre': str(voz.get('name') or ident)[:80],
                          'detalle': ', '.join(str(v)[:30] for v in (etiquetas.get('language'), etiquetas.get('gender'), etiquetas.get('accent')) if v)})
    return {'voces': lista[:80], 'total': len(lista)}


def hablar(base, data):
    texto = (data or {}).get('text')
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError('No hay texto que leer.')
    texto = texto.strip()[:MAX_TEXTO]
    config = _config(base)
    if config['proveedor'] != 'elevenlabs' or not config['voz']:
        raise ValueError('ElevenLabs no está elegido como voz. Configúralo en Conexiones.')
    audio = _peticion(base, '/text-to-speech/%s?output_format=mp3_44100_64' % config['voz'],
                      {'text': texto, 'model_id': MODELO}, aceptar='audio/mpeg')
    if not audio or len(audio) < 100:
        raise ValueError('ElevenLabs no devolvió audio.')
    return audio
