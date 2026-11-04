"""Servidores MCP que la persona conecta a Muse desde Bee-Muse.

Solo servidores por stdio (comando + argumentos), que es lo que el CLI de Muse acepta con
``--config mcpServers.<nombre>=...``. Aquí no se guardan claves: si un servidor necesita una,
va en el entorno de ese servidor, no en este archivo.
"""
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid

FILE_NAME = 'mcp_servers.json'
LOCK = threading.Lock()
NOMBRE = re.compile(r'^[a-z0-9][a-z0-9_-]{0,31}$')
RESERVADOS = {'bee-muse'}
MAX_SERVIDORES = 20
MAX_ARGS = 20
MAX_TEXTO = 400
SECRET_MARKERS = ('sk-', 'ghp_', 'github_pat_', 'BEGIN PRIVATE KEY', 'AIza', 'xoxb-')
NOTA_WORKSPACE = ('Muse carga sus MCP al conversar con la carpeta de trabajo elegida. Esa carpeta debe estar en el disco '
                  'principal (C:): en una unidad USB o exFAT el CLI rechaza su configuración MCP.')


def _path(base):
    return base / FILE_NAME


def _load(base):
    p = _path(base)
    if not p.exists():
        return {'version': 1, 'servidores': []}
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ValueError('No se pudo leer mcp_servers.json. No se sobrescribe.')
    if not isinstance(data, dict) or not isinstance(data.get('servidores'), list):
        raise ValueError('mcp_servers.json tiene un formato inesperado. No se sobrescribe.')
    return data


def _save(base, state):
    dest = _path(base)
    temp = dest.with_name('.%s.%d.%s.tmp' % (FILE_NAME, os.getpid(), uuid.uuid4().hex[:8]))
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')
    try:
        os.chmod(temp, 0o600)
    except (OSError, NotImplementedError):
        pass
    os.replace(temp, dest)


def _texto(value, campo):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Escribe %s.' % campo)
    value = value.strip()
    if len(value) > MAX_TEXTO or any(ord(c) < 32 for c in value):
        raise ValueError('%s no es válido.' % campo.capitalize())
    if any(marker in value for marker in SECRET_MARKERS):
        raise ValueError('No pegues claves ni tokens aquí. Ponlos en el entorno del servidor.')
    return value


def _nombre(value):
    if not isinstance(value, str) or not NOMBRE.match(value):
        raise ValueError('El nombre usa minúsculas, números, guion o guion bajo (hasta 32).')
    if value in RESERVADOS:
        raise ValueError('Ese nombre lo usa Bee-Muse para su propio índice.')
    return value


def _publico(servidor):
    return {'name': servidor['name'], 'command': servidor['command'], 'args': list(servidor['args']), 'enabled': bool(servidor.get('enabled', True))}


def listar(base):
    with LOCK:
        state = _load(base)
        return {'servidores': [_publico(s) for s in state['servidores']], 'nota': NOTA_WORKSPACE, 'maximo': MAX_SERVIDORES}


def guardar(base, data):
    data = data or {}
    name = _nombre(data.get('name'))
    command = _texto(data.get('command'), 'el comando')
    args = data.get('args', [])
    if not isinstance(args, list) or len(args) > MAX_ARGS:
        raise ValueError('Los argumentos son una lista de hasta %d textos.' % MAX_ARGS)
    args = [_texto(a, 'el argumento') for a in args]
    enabled = bool(data.get('enabled', True))
    with LOCK:
        state = _load(base)
        existentes = [s for s in state['servidores'] if s['name'] != name]
        if len(existentes) >= MAX_SERVIDORES:
            raise ValueError('Ya hay %d servidores. Quita alguno para agregar otro.' % MAX_SERVIDORES)
        nuevo = {'name': name, 'command': command, 'args': args, 'enabled': enabled}
        existentes.append(nuevo)
        state['servidores'] = sorted(existentes, key=lambda s: s['name'])
        _save(base, state)
        return {'ok': True, 'servidor': _publico(nuevo), 'total': len(state['servidores'])}


def borrar(base, data):
    name = _nombre((data or {}).get('name'))
    with LOCK:
        state = _load(base)
        antes = len(state['servidores'])
        state['servidores'] = [s for s in state['servidores'] if s['name'] != name]
        if len(state['servidores']) == antes:
            raise ValueError('Ese servidor no está en la lista.')
        _save(base, state)
        return {'ok': True, 'total': len(state['servidores'])}


def habilitados(base):
    """Pares (nombre, {'command','args'}) listos para ``--config mcpServers.<nombre>=``."""
    if base is None:
        return []
    try:
        with LOCK:
            state = _load(base)
    except ValueError:
        return []
    return [(s['name'], {'command': s['command'], 'args': list(s['args'])}) for s in state['servidores'] if s.get('enabled', True)]


def _resolver(command):
    if os.path.isabs(command):
        return command if os.path.isfile(command) else None
    return shutil.which(command)


def _handshake(proc, deadline):
    cola = queue.Queue()

    def leer():
        try:
            for raw in proc.stdout:
                cola.put(raw)
        except (OSError, ValueError):
            pass
        cola.put(None)

    threading.Thread(target=leer, daemon=True).start()

    def enviar(msg):
        proc.stdin.write((json.dumps(msg) + '\n').encode('utf-8'))
        proc.stdin.flush()

    def esperar(ident):
        while True:
            restante = deadline - time.monotonic()
            if restante <= 0:
                raise ValueError('El servidor no respondió a tiempo.')
            try:
                raw = cola.get(timeout=restante)
            except queue.Empty:
                raise ValueError('El servidor no respondió a tiempo.')
            if raw is None:
                raise ValueError('El servidor se cerró antes de responder.')
            if len(raw) > 4 * 1024 * 1024:
                continue
            try:
                obj = json.loads(raw)
            except ValueError:
                continue
            if isinstance(obj, dict) and obj.get('id') == ident:
                if 'error' in obj:
                    detalle = obj['error'].get('message') if isinstance(obj['error'], dict) else ''
                    raise ValueError('El servidor devolvió un error: %s' % (detalle or 'sin detalle'))
                return obj.get('result') or {}

    enviar({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
        'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'bee-muse', 'version': '0.5.0'}}})
    inicio = esperar(1)
    enviar({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    enviar({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
    herramientas = esperar(2).get('tools') or []
    nombres = [t.get('name') for t in herramientas if isinstance(t, dict) and isinstance(t.get('name'), str)]
    servidor = inicio.get('serverInfo') if isinstance(inicio, dict) else None
    return {'servidor': (servidor or {}).get('name') or '', 'version': (servidor or {}).get('version') or '', 'tools': nombres[:50], 'total': len(nombres)}


def probar(base, data, timeout=20):
    name = _nombre((data or {}).get('name'))
    with LOCK:
        state = _load(base)
    servidor = next((s for s in state['servidores'] if s['name'] == name), None)
    if not servidor:
        raise ValueError('Ese servidor no está en la lista.')
    exe = _resolver(servidor['command'])
    if not exe:
        raise ValueError('No se encontró el comando "%s" en este equipo.' % servidor['command'])
    try:
        proc = subprocess.Popen([exe] + list(servidor['args']), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, shell=False,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except OSError as error:
        raise ValueError('No se pudo iniciar el servidor: %s' % error.strerror) from None
    try:
        resultado = _handshake(proc, time.monotonic() + timeout)
    except (OSError, BrokenPipeError):
        raise ValueError('El servidor cerró la conexión al iniciar.') from None
    finally:
        try:
            proc.kill()
        except OSError:
            pass
    return {'ok': True, 'name': name, **resultado}
