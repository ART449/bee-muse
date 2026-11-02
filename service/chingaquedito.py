"""Chingaquedito: acompañante local de continuidad.

Guarda únicamente lo que la persona escribe en su página. No vigila otras
ventanas, no envía nada a la red, no manda recordatorios y no crea ningún
archivo hasta que se activa de forma explícita. No es tratamiento ni
diagnóstico. Los datos viven en `chingaquedito.json`, separados del catálogo
(catalog.json), de las colecciones (organizacion.json) y de las credenciales
(.credentials).

Lectura estricta: si el archivo tiene una estructura que esta versión no
entiende, o una entrada inválida, se informa un error recuperable y ninguna
operación lo sobrescribe. Preferimos negarnos a guardar antes que perder algo
que la persona escribió.
"""
import datetime as dt
import contextlib
import hashlib
import json
import os
import tempfile
import threading
import time
import uuid
from pathlib import Path

try:  # Candado entre procesos distintos (Windows).
    import msvcrt
except ImportError:  # pragma: no cover - solo Windows
    msvcrt = None
try:  # Equivalente POSIX, por si esto se ejecuta fuera de Windows.
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

LOCK = threading.Lock()
BLOQUEO_MAX = 20.0
BLOQUEO_ESPERA = 0.01
FILE_NAME = 'chingaquedito.json'
ESTADOS = ('activo', 'aparcado', 'terminado')
ORDEN = {'activo': 0, 'aparcado': 1, 'terminado': 2}
LIMITS = {'titulo': 140, 'objetivo': 1200, 'siguiente': 700, 'texto': 1200}
MAX_FRENTES = 300
MAX_IDEAS = 600
# Mismos marcadores que connections.py: la libreta no es lugar para credenciales.
SECRET_MARKERS = ('sk-', 'ghp_', 'github_pat_', 'BEGIN PRIVATE KEY', 'AIza', 'xoxb-')
RECOVERY = ('No se borró nada y no voy a sobrescribir el archivo. Revisa chingaquedito.json '
            'o muévelo a otra carpeta si prefieres empezar de cero.')


def _path(base):
    return base / FILE_NAME


def _ruta_candado(base):
    """Candado por carpeta de datos, fuera de la carpeta del usuario.

    threading.Lock solo protege hilos del mismo proceso; dos procesos distintos
    podían leer, modificar y reescribir a la vez y se perdían entradas. Este
    archivo de candado es compartido por todo proceso que use la misma carpeta.
    """
    clave = hashlib.sha256(os.path.normcase(str(Path(base).resolve())).encode('utf-8')).hexdigest()[:32]
    return Path(tempfile.gettempdir()) / ('bee-muse-chingaquedito-%s.lock' % clave)


@contextlib.contextmanager
def _candado_proceso(base):
    if msvcrt is None and fcntl is None:
        yield
        return
    with open(_ruta_candado(base), 'a+b') as handle:
        if msvcrt is not None:
            limite = time.monotonic() + BLOQUEO_MAX
            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() > limite:
                        raise ValueError('Otro proceso está guardando en la libreta. Espera un momento y vuelve a intentarlo.') from None
                    time.sleep(BLOQUEO_ESPERA)
            try:
                yield
            finally:
                handle.seek(0)
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
        else:  # pragma: no cover - POSIX
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def _guard(base):
    """Hilos del mismo proceso + procesos distintos, siempre en ese orden."""
    with LOCK:
        with _candado_proceso(base):
            yield


def _now():
    # Microsegundos: con segundos, dos frentes tocados en el mismo segundo
    # quedaban empatados y el orden de la lista cambiaba solo.
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='microseconds')


def _empty():
    return {'version': 1, 'activo': False, 'frentes': [], 'ideas': []}


def _bloqueado(motivo):
    return {**_empty(),
            'error': 'No pude leer completa tu libreta guardada (%s).' % motivo,
            'recovery': RECOVERY}


def _texto(value, campo, obligatorio=False):
    if value is None:
        value = ''
    if not isinstance(value, str):
        raise ValueError('Escribe este campo como texto.')
    value = value.replace('\r\n', '\n').strip()
    if any(ord(c) < 32 and c not in '\n\t' for c in value):
        raise ValueError('El texto contiene caracteres que no se pueden guardar.')
    if len(value) > LIMITS[campo]:
        raise ValueError('Este campo admite hasta %d caracteres.' % LIMITS[campo])
    if obligatorio and not value:
        raise ValueError('Falta el título del frente.')
    if any(marker in value for marker in SECRET_MARKERS):
        raise ValueError('No guardes claves ni tokens aquí. Chingaquedito es una libreta, no una bóveda.')
    return value


def _estado(value, por_defecto=None):
    if value is None or value == '':
        if por_defecto is None:
            raise ValueError('Indica el estado: activo, aparcado o terminado.')
        return por_defecto
    if not isinstance(value, str) or value not in ESTADOS:
        raise ValueError('El estado debe ser activo, aparcado o terminado.')
    return value


def _id():
    return uuid.uuid4().hex[:16]


def _ident(data, mensaje):
    ident = data.get('id')
    if not isinstance(ident, str) or not ident.strip() or len(ident) > 32:
        raise ValueError(mensaje)
    return ident


def _confirmar(data):
    if data.get('confirmar') is not True:
        raise ValueError('Para borrar hace falta confirmarlo explícitamente desde la página.')


def _fecha(value, donde):
    if value is None or value == '':
        return ''
    if not isinstance(value, str):
        raise ValueError('%s tiene una fecha que no puedo leer' % donde)
    return value[:40]


def _frente_valido(row, posicion):
    donde = 'el frente %d' % posicion
    if not isinstance(row, dict):
        raise ValueError('%s no es una entrada válida' % donde)
    ident = row.get('id')
    if not isinstance(ident, str) or not ident.strip() or len(ident) > 32:
        raise ValueError('%s no tiene identificador' % donde)
    try:
        titulo = _texto(row.get('titulo'), 'titulo', True)
        objetivo = _texto(row.get('objetivo'), 'objetivo')
        siguiente = _texto(row.get('siguiente'), 'siguiente')
    except ValueError as exc:
        raise ValueError('%s: %s' % (donde, exc)) from None
    try:
        estado = _estado(row.get('estado'), 'activo')
    except ValueError as exc:
        raise ValueError('%s: %s' % (donde, exc)) from None
    return {
        'id': ident,
        'titulo': titulo,
        'objetivo': objetivo,
        'siguiente': siguiente,
        'estado': estado,
        'creado': _fecha(row.get('creado'), donde),
        'tocado': _fecha(row.get('tocado'), donde),
        'ultimaVuelta': _fecha(row.get('ultimaVuelta'), donde) or None,
    }


def _idea_valida(row, posicion, ids_frentes):
    donde = 'la idea %d' % posicion
    if not isinstance(row, dict):
        raise ValueError('%s no es una entrada válida' % donde)
    ident = row.get('id')
    if not isinstance(ident, str) or not ident.strip() or len(ident) > 32:
        raise ValueError('%s no tiene identificador' % donde)
    try:
        texto = _texto(row.get('texto'), 'texto', True)
    except ValueError as exc:
        raise ValueError('%s: %s' % (donde, exc)) from None
    frente = row.get('frente')
    if frente is not None and not isinstance(frente, str):
        raise ValueError('%s apunta a un frente que no puedo leer' % donde)
    if frente and frente not in ids_frentes:
        raise ValueError('%s apunta a un frente que ya no está en el archivo' % donde)
    return {
        'id': ident,
        'texto': texto,
        'frente': frente or None,
        'creado': _fecha(row.get('creado'), donde),
    }


def _shape(raw):
    """Valida el archivo completo. Si algo no cuadra, levanta ValueError."""
    if not isinstance(raw, dict):
        raise ValueError('el archivo no contiene un objeto')
    version = raw.get('version', 1)
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise ValueError('la versión del archivo no es la que esta aplicación entiende')
    activo = raw.get('activo', False)
    if not isinstance(activo, bool):
        raise ValueError('el campo "activo" no es verdadero o falso')
    frentes_raw = raw.get('frentes', [])
    ideas_raw = raw.get('ideas', [])
    if not isinstance(frentes_raw, list):
        raise ValueError('la lista de frentes no es una lista')
    if not isinstance(ideas_raw, list):
        raise ValueError('la lista de ideas no es una lista')

    frentes, vistos = [], set()
    for posicion, row in enumerate(frentes_raw, 1):
        frente = _frente_valido(row, posicion)
        if frente['id'] in vistos:
            raise ValueError('el frente %d repite un identificador' % posicion)
        vistos.add(frente['id'])
        frentes.append(frente)

    ideas, vistos_ideas = [], set()
    for posicion, row in enumerate(ideas_raw, 1):
        idea = _idea_valida(row, posicion, vistos)
        if idea['id'] in vistos_ideas:
            raise ValueError('la idea %d repite un identificador' % posicion)
        vistos_ideas.add(idea['id'])
        ideas.append(idea)

    normalized = {'version': 1, 'activo': activo, 'frentes': frentes, 'ideas': ideas}
    if normalized != raw:
        raise ValueError('el archivo tiene campos o valores que esta versión no puede conservar')
    return normalized


def load(base):
    path = _path(base)
    if not path.exists():
        return _empty()
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except OSError:
        return _bloqueado('no se pudo abrir el archivo')
    except ValueError:
        return _bloqueado('no es un JSON válido')
    try:
        return _shape(raw)
    except ValueError as exc:
        return _bloqueado(str(exc))


def _save(base, state):
    dest = _path(base)
    # Temporal con nombre único por proceso: antes todos usaban el mismo
    # chingaquedito.tmp y dos procesos se lo quitaban entre sí (PermissionError).
    temp = dest.with_name('.%s.%d.%s.tmp' % (FILE_NAME, os.getpid(), uuid.uuid4().hex[:8]))
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
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


def _requiere_lectura(state):
    if state.get('error'):
        raise ValueError(state['error'] + ' ' + RECOVERY)


def _requiere_activacion(state):
    if not state.get('activo'):
        raise ValueError('Chingaquedito todavía no está activado en este equipo. Actívalo primero; no se guarda nada sin tu permiso.')


def status(base):
    state = load(base)
    # Dentro de cada estado, lo último que tocaste aparece primero.
    frentes = sorted(state['frentes'], key=lambda f: f.get('ultimaVuelta') or f.get('tocado') or '', reverse=True)
    frentes.sort(key=lambda f: ORDEN.get(f['estado'], 3))
    counts = {estado: sum(1 for f in state['frentes'] if f['estado'] == estado) for estado in ESTADOS}
    payload = {
        'activo': state['activo'],
        'configurado': _path(base).exists(),
        'frentes': frentes,
        'ideas': list(reversed(state['ideas'])),
        'counts': counts,
        'limites': {'frentes': MAX_FRENTES, 'ideas': MAX_IDEAS},
        'storage': 'Archivo local chingaquedito.json, separado del catálogo y de las credenciales.',
        'note': 'Solo se guarda lo que escribes aquí. Sin cuentas, sin nube, sin notificaciones.',
    }
    if state.get('error'):
        payload['error'] = state['error']
        payload['recovery'] = state.get('recovery') or RECOVERY
    return payload


def activar(base, activo):
    if not isinstance(activo, bool):
        raise ValueError('Indica si quieres activarlo.')
    if not activo and not _path(base).exists():
        raise ValueError('Chingaquedito todavía no está activado.')
    with _guard(base):
        state = load(base)
        _requiere_lectura(state)
        state['activo'] = activo
        _save(base, state)
    return {'ok': True, **status(base)}


def crear_frente(base, data):
    if not isinstance(data, dict):
        raise ValueError('Solicitud no válida.')
    titulo = _texto(data.get('titulo'), 'titulo', True)
    objetivo = _texto(data.get('objetivo'), 'objetivo')
    siguiente = _texto(data.get('siguiente'), 'siguiente')
    estado = _estado(data.get('estado'), 'activo')
    with _guard(base):
        state = load(base)
        _requiere_lectura(state)
        _requiere_activacion(state)
        if len(state['frentes']) >= MAX_FRENTES:
            raise ValueError('La lista llegó a %d frentes. Termina, borra o aparca alguno antes de añadir otro.' % MAX_FRENTES)
        now = _now()
        frente = {'id': _id(), 'titulo': titulo, 'objetivo': objetivo, 'siguiente': siguiente,
                  'estado': estado, 'creado': now, 'tocado': now, 'ultimaVuelta': None}
        state['frentes'].append(frente)
        _save(base, state)
    return {'ok': True, 'cambio': 'Guardé el frente «%s».' % titulo, **status(base)}


def editar_frente(base, data):
    """Cambia título, objetivo o siguiente paso sin tocar el estado ni la fecha de creación."""
    if not isinstance(data, dict):
        raise ValueError('Solicitud no válida.')
    ident = _ident(data, 'Falta el frente que quieres editar.')
    cambios = {}
    for campo in ('titulo', 'objetivo', 'siguiente'):
        if campo in data:
            cambios[campo] = _texto(data.get(campo), campo, campo == 'titulo')
    if not cambios:
        raise ValueError('No hay cambios que guardar. Escribe algo en el título, el objetivo o el siguiente paso.')
    with _guard(base):
        state = load(base)
        _requiere_lectura(state)
        _requiere_activacion(state)
        frente = next((f for f in state['frentes'] if f['id'] == ident), None)
        if frente is None:
            raise ValueError('Ese frente ya no está en la lista.')
        frente.update(cambios)
        frente['tocado'] = _now()
        _save(base, state)
    return {'ok': True, 'cambio': 'Actualicé «%s». Tu frente sigue en %s.' % (frente['titulo'], frente['estado']), **status(base)}


def cambiar_estado(base, data):
    if not isinstance(data, dict):
        raise ValueError('Solicitud no válida.')
    ident = _ident(data, 'Falta el frente.')
    estado = _estado(data.get('estado'))
    with _guard(base):
        state = load(base)
        _requiere_lectura(state)
        _requiere_activacion(state)
        frente = next((f for f in state['frentes'] if f['id'] == ident), None)
        if frente is None:
            raise ValueError('Ese frente ya no está en la lista.')
        frente['estado'] = estado
        frente['tocado'] = _now()
        _save(base, state)
    nombre = {'activo': 'Quedó activo', 'aparcado': 'Quedó aparcado', 'terminado': 'Quedó terminado'}[estado]
    return {'ok': True, 'cambio': '%s «%s». Puedes retomarlo cuando quieras.' % (nombre, frente['titulo']), **status(base)}


def volver(base, data):
    if not isinstance(data, dict):
        raise ValueError('Solicitud no válida.')
    ident = _ident(data, 'Falta el frente al que quieres volver.')
    with _guard(base):
        state = load(base)
        _requiere_lectura(state)
        _requiere_activacion(state)
        frente = next((f for f in state['frentes'] if f['id'] == ident), None)
        if frente is None:
            raise ValueError('Ese frente ya no está en la lista.')
        now = _now()
        frente['ultimaVuelta'] = now
        frente['tocado'] = now
        reactivado = frente['estado'] == 'aparcado'
        if reactivado:
            frente['estado'] = 'activo'
        _save(base, state)
    nota = 'Volviste a «%s».' % frente['titulo']
    if reactivado:
        nota += ' Lo saqué de la pausa porque tú lo pediste.'
    elif frente['estado'] == 'terminado':
        nota += ' Sigue marcado como terminado; cámbialo si lo retomas en serio.'
    return {'ok': True, 'cambio': nota, **status(base)}


def guardar_idea(base, data):
    if not isinstance(data, dict):
        raise ValueError('Solicitud no válida.')
    texto = _texto(data.get('texto'), 'texto', True)
    frente_id = data.get('frente')
    if frente_id is not None and not isinstance(frente_id, str):
        raise ValueError('El frente elegido no es válido.')
    with _guard(base):
        state = load(base)
        _requiere_lectura(state)
        _requiere_activacion(state)
        if len(state['ideas']) >= MAX_IDEAS:
            raise ValueError('La libreta de ideas llegó a %d entradas. Borra o cierra algunas antes de seguir.' % MAX_IDEAS)
        if frente_id and not any(f['id'] == frente_id for f in state['frentes']):
            raise ValueError('El frente elegido ya no está en la lista.')
        state['ideas'].append({'id': _id(), 'texto': texto, 'frente': frente_id or None, 'creado': _now()})
        # Guardar una idea nunca cambia el estado de un frente.
        _save(base, state)
    return {'ok': True, 'cambio': 'Guardé la idea. Tu frente sigue donde estaba.', **status(base)}


def borrar_frente(base, data):
    """Borra el frente y deja vivas sus ideas, solo sin vínculo. Nunca borra ideas."""
    if not isinstance(data, dict):
        raise ValueError('Solicitud no válida.')
    ident = _ident(data, 'Falta el frente que quieres borrar.')
    _confirmar(data)
    with _guard(base):
        state = load(base)
        _requiere_lectura(state)
        _requiere_activacion(state)
        frente = next((f for f in state['frentes'] if f['id'] == ident), None)
        if frente is None:
            raise ValueError('Ese frente ya no está en la lista.')
        state['frentes'] = [f for f in state['frentes'] if f['id'] != ident]
        sueltas = 0
        for idea in state['ideas']:
            if idea['frente'] == ident:
                idea['frente'] = None
                sueltas += 1
        _save(base, state)
    nota = 'Borré «%s» de tu libreta.' % frente['titulo']
    if sueltas == 1:
        nota += ' La idea que lo mencionaba sigue guardada, ahora sin frente.'
    elif sueltas > 1:
        nota += ' Las %d ideas que lo mencionaban siguen guardadas, ahora sin frente.' % sueltas
    return {'ok': True, 'cambio': nota, **status(base)}


def borrar_idea(base, data):
    if not isinstance(data, dict):
        raise ValueError('Solicitud no válida.')
    ident = _ident(data, 'Falta la idea que quieres borrar.')
    _confirmar(data)
    with _guard(base):
        state = load(base)
        _requiere_lectura(state)
        _requiere_activacion(state)
        idea = next((i for i in state['ideas'] if i['id'] == ident), None)
        if idea is None:
            raise ValueError('Esa idea ya no está en la libreta.')
        state['ideas'] = [i for i in state['ideas'] if i['id'] != ident]
        _save(base, state)
    return {'ok': True, 'cambio': 'Borré esa idea. Tus frentes no se tocaron.', **status(base)}
