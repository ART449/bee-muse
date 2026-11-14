"""Hilos de conversación con Muse: historial persistente por hilo, local y sin red.

Capa aparte del historial corto que muse.js guarda en el navegador (últimas 12 líneas):
aquí viven todos los hilos con título, para retomar cualquiera. No contiene credenciales:
un mensaje que parezca llevar una clave no se guarda.
"""
import datetime as dt
import json
import os
import threading
import time
import uuid

FILE_NAME = 'hilos.json'
LOCK = threading.Lock()
LIMITES = {'titulo': 120, 'content': 12000, 'mensajes': 400, 'hilos': 200}
SECRET_MARKERS = ('sk-', 'ghp_', 'github_pat_', 'BEGIN PRIVATE KEY', 'AIza', 'xoxb-', 'xi-api-key')
TITULO_NUEVO = 'Nuevo hilo'


def _path(base):
    return base / FILE_NAME


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def _empty():
    return {'version': 1, 'activo': None, 'hilos': []}


def _load(base):
    p = _path(base)
    if not p.exists():
        return _empty()
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ValueError('No se pudo leer hilos.json. No se sobrescribe; revisa el archivo o muévelo a otra carpeta.')
    if not isinstance(data, dict) or not isinstance(data.get('hilos'), list):
        raise ValueError('hilos.json tiene un formato inesperado. No se sobrescribe.')
    return data


def _save(base, state):
    dest = _path(base)
    temp = dest.with_name('.%s.%d.%s.tmp' % (FILE_NAME, os.getpid(), uuid.uuid4().hex[:8]))
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')
    try:
        os.chmod(temp, 0o600)
    except (OSError, NotImplementedError):
        pass
    for intento in range(6):
        try:
            os.replace(temp, dest)
            return
        except PermissionError:
            if intento == 5:
                temp.unlink(missing_ok=True)
                raise
            time.sleep(0.02 * (intento + 1))


def _texto(value, campo, maximo, obligatorio=True):
    if value is None and not obligatorio:
        return ''
    if not isinstance(value, str):
        raise ValueError('El campo %s no es válido.' % campo)
    value = value.strip()
    if obligatorio and not value:
        raise ValueError('Escribe %s.' % campo)
    if len(value) > maximo:
        raise ValueError('%s supera %d caracteres.' % (campo.capitalize(), maximo))
    if any(ord(c) < 32 and c not in '\n\t' for c in value):
        raise ValueError('El campo %s tiene caracteres no permitidos.' % campo)
    return value


def _id(value):
    if not isinstance(value, str) or not value.isalnum() or not 6 <= len(value) <= 32:
        raise ValueError('Ese hilo no existe.')
    return value


def _find(state, ident):
    for hilo in state['hilos']:
        if hilo['id'] == ident:
            return hilo
    raise ValueError('Ese hilo no existe.')


def _resumen(hilo):
    ultimo = ''
    for fila in reversed(hilo['mensajes']):
        if fila['role'] == 'assistant':
            ultimo = fila['content'][:160]
            break
    return {'id': hilo['id'], 'titulo': hilo['titulo'], 'creado': hilo['creado'], 'actualizado': hilo['actualizado'],
            'mensajes': len(hilo['mensajes']), 'ultimo': ultimo}


def _nuevo(state, titulo):
    if len(state['hilos']) >= LIMITES['hilos']:
        raise ValueError('Ya hay %d hilos. Borra alguno para crear otro.' % LIMITES['hilos'])
    ahora = _now()
    hilo = {'id': uuid.uuid4().hex[:12], 'titulo': titulo or TITULO_NUEVO, 'creado': ahora, 'actualizado': ahora, 'mensajes': []}
    state['hilos'].append(hilo)
    state['activo'] = hilo['id']
    return hilo


def listar(base):
    with LOCK:
        state = _load(base)
        hilos = sorted(state['hilos'], key=lambda h: h['actualizado'], reverse=True)
        return {'activo': state['activo'], 'hilos': [_resumen(h) for h in hilos]}


def obtener(base, ident):
    with LOCK:
        hilo = _find(_load(base), _id(ident))
        return {'id': hilo['id'], 'titulo': hilo['titulo'], 'mensajes': hilo['mensajes']}


def crear(base, data):
    titulo = _texto((data or {}).get('titulo'), 'el título', LIMITES['titulo'], obligatorio=False)
    with LOCK:
        state = _load(base)
        hilo = _nuevo(state, titulo)
        _save(base, state)
        return {'ok': True, 'activo': hilo['id'], 'hilo': _resumen(hilo)}


def activar(base, data):
    ident = _id((data or {}).get('id'))
    with LOCK:
        state = _load(base)
        hilo = _find(state, ident)
        state['activo'] = ident
        _save(base, state)
        return {'ok': True, 'activo': ident, 'id': hilo['id'], 'titulo': hilo['titulo'], 'mensajes': hilo['mensajes']}


def mensaje(base, data):
    data = data or {}
    role = data.get('role')
    if role not in ('user', 'assistant'):
        raise ValueError('El mensaje debe ser de la persona o de Muse.')
    content = _texto(data.get('content'), 'el mensaje', LIMITES['content'])
    if any(marker in content for marker in SECRET_MARKERS):
        raise ValueError('Este mensaje no se guardó en el hilo: parece contener una clave o token.')
    with LOCK:
        state = _load(base)
        ident = data.get('hilo') or state['activo']
        hilo = _find(state, _id(ident)) if ident else _nuevo(state, '')
        hilo['mensajes'].append({'role': role, 'content': content, 'cuando': _now()})
        hilo['mensajes'] = hilo['mensajes'][-LIMITES['mensajes']:]
        if role == 'user' and hilo['titulo'] == TITULO_NUEVO:
            hilo['titulo'] = (content.splitlines()[0][:60]).rstrip(' .,;:') or TITULO_NUEVO
        hilo['actualizado'] = _now()
        state['activo'] = hilo['id']
        _save(base, state)
        return {'ok': True, 'activo': hilo['id'], 'hilo': _resumen(hilo)}


def renombrar(base, data):
    data = data or {}
    ident = _id(data.get('id'))
    titulo = _texto(data.get('titulo'), 'el título', LIMITES['titulo'])
    with LOCK:
        state = _load(base)
        hilo = _find(state, ident)
        hilo['titulo'] = titulo
        hilo['actualizado'] = _now()
        _save(base, state)
        return {'ok': True, 'hilo': _resumen(hilo)}


def borrar(base, data):
    ident = _id((data or {}).get('id'))
    with LOCK:
        state = _load(base)
        _find(state, ident)
        state['hilos'] = [h for h in state['hilos'] if h['id'] != ident]
        if state['activo'] == ident:
            state['activo'] = None
        _save(base, state)
        return {'ok': True, 'activo': state['activo'], 'total': len(state['hilos'])}
