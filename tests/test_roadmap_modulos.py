import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'service'))
import hilos
import mcp_servers
import voz_tts


class HilosTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_mensaje_sin_hilo_crea_uno_y_lo_titula_con_el_primer_mensaje(self):
        r = hilos.mensaje(self.base, {'role': 'user', 'content': 'Busca el catálogo sintético.\nY señálalo.'})
        self.assertEqual(r['hilo']['titulo'], 'Busca el catálogo sintético')
        hilos.mensaje(self.base, {'role': 'assistant', 'content': 'Aquí está.'})
        lista = hilos.listar(self.base)
        self.assertEqual(lista['activo'], r['activo'])
        self.assertEqual(lista['hilos'][0]['mensajes'], 2)
        self.assertEqual(lista['hilos'][0]['ultimo'], 'Aquí está.')

    def test_crear_activar_renombrar_borrar(self):
        a = hilos.crear(self.base, {'titulo': 'Uno'})
        b = hilos.crear(self.base, {})
        self.assertEqual(hilos.listar(self.base)['activo'], b['activo'])
        act = hilos.activar(self.base, {'id': a['activo']})
        self.assertEqual(act['titulo'], 'Uno')
        hilos.renombrar(self.base, {'id': a['activo'], 'titulo': 'Uno renombrado'})
        self.assertEqual(hilos.obtener(self.base, a['activo'])['titulo'], 'Uno renombrado')
        r = hilos.borrar(self.base, {'id': a['activo']})
        self.assertIsNone(r['activo'])
        with self.assertRaises(ValueError):
            hilos.obtener(self.base, a['activo'])

    def test_rechaza_claves_y_roles_raros(self):
        with self.assertRaises(ValueError):
            hilos.mensaje(self.base, {'role': 'user', 'content': 'mi clave es sk-abcdef'})
        with self.assertRaises(ValueError):
            hilos.mensaje(self.base, {'role': 'system', 'content': 'hola'})
        with self.assertRaises(ValueError):
            hilos.activar(self.base, {'id': '../x'})
        self.assertFalse((self.base / 'hilos.json').exists())

    def test_archivo_corrupto_no_se_sobrescribe(self):
        (self.base / 'hilos.json').write_text('{no json', encoding='utf-8')
        with self.assertRaises(ValueError):
            hilos.listar(self.base)
        self.assertEqual((self.base / 'hilos.json').read_text(encoding='utf-8'), '{no json')


FAKE_MCP = r'''
import json,sys
for raw in sys.stdin:
    try: m=json.loads(raw)
    except ValueError: continue
    if m.get('method')=='initialize':
        print(json.dumps({'jsonrpc':'2.0','id':m['id'],'result':{'protocolVersion':'2024-11-05','serverInfo':{'name':'falso','version':'1.0'},'capabilities':{}}}),flush=True)
    elif m.get('method')=='tools/list':
        print(json.dumps({'jsonrpc':'2.0','id':m['id'],'result':{'tools':[{'name':'saludar'},{'name':'sumar'}]}}),flush=True)
'''


class McpServersTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.falso = self.base / 'falso_mcp.py'
        self.falso.write_text(FAKE_MCP, encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_guardar_listar_habilitados_borrar(self):
        mcp_servers.guardar(self.base, {'name': 'falso', 'command': sys.executable, 'args': [str(self.falso)]})
        mcp_servers.guardar(self.base, {'name': 'apagado', 'command': 'x', 'args': [], 'enabled': False})
        lista = mcp_servers.listar(self.base)['servidores']
        self.assertEqual([s['name'] for s in lista], ['apagado', 'falso'])
        hab = mcp_servers.habilitados(self.base)
        self.assertEqual(hab, [('falso', {'command': sys.executable, 'args': [str(self.falso)]})])
        mcp_servers.borrar(self.base, {'name': 'apagado'})
        self.assertEqual(len(mcp_servers.listar(self.base)['servidores']), 1)

    def test_validaciones(self):
        for malo in ({'name': 'bee-muse', 'command': 'x'}, {'name': 'Mayús', 'command': 'x'}, {'name': 'ok', 'command': ''},
                     {'name': 'ok', 'command': 'x', 'args': ['sk-secreto']}, {'name': 'ok', 'command': 'x', 'args': 'no-lista'}):
            with self.assertRaises(ValueError):
                mcp_servers.guardar(self.base, malo)
        with self.assertRaises(ValueError):
            mcp_servers.borrar(self.base, {'name': 'nadie'})

    def test_probar_hace_handshake_y_lista_herramientas(self):
        mcp_servers.guardar(self.base, {'name': 'falso', 'command': sys.executable, 'args': [str(self.falso)]})
        r = mcp_servers.probar(self.base, {'name': 'falso'}, timeout=15)
        self.assertEqual(r['servidor'], 'falso')
        self.assertEqual(r['tools'], ['saludar', 'sumar'])

    def test_probar_comando_inexistente(self):
        mcp_servers.guardar(self.base, {'name': 'nada', 'command': 'comando-que-no-existe-bee', 'args': []})
        with self.assertRaises(ValueError):
            mcp_servers.probar(self.base, {'name': 'nada'})


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class VozTtsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_sin_clave_no_hay_elevenlabs(self):
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': ''}):
            s = voz_tts.status(self.base)
            self.assertFalse(s['configurado'])
            self.assertEqual(s['proveedor'], 'sistema')
            with self.assertRaises(ValueError):
                voz_tts.guardar_config(self.base, {'proveedor': 'elevenlabs', 'voz': 'abc123'})
            with self.assertRaises(ValueError):
                voz_tts.hablar(self.base, {'text': 'hola'})

    def test_con_clave_en_entorno_configura_y_habla_sin_filtrar_la_clave(self):
        llamadas = []

        def falso_urlopen(req, timeout=0):
            llamadas.append((req.full_url, req.get_method(), dict(req.header_items())))
            if req.full_url.endswith('/voices'):
                return FakeResponse(json.dumps({'voices': [{'voice_id': 'abc123', 'name': 'Lupita', 'labels': {'language': 'es'}}]}).encode())
            return FakeResponse(b'ID3' + b'\x00' * 200)

        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'clave-de-prueba-123456'}), patch('urllib.request.urlopen', falso_urlopen):
            self.assertTrue(voz_tts.status(self.base)['configurado'])
            voces = voz_tts.voces(self.base)
            self.assertEqual(voces['voces'][0]['nombre'], 'Lupita')
            voz_tts.guardar_config(self.base, {'proveedor': 'elevenlabs', 'voz': 'abc123', 'vozNombre': 'Lupita'})
            audio = voz_tts.hablar(self.base, {'text': '  Hola, soy Muse.  '})
            self.assertTrue(audio.startswith(b'ID3'))
            url, metodo, cabeceras = llamadas[-1]
            self.assertIn('/text-to-speech/abc123', url)
            self.assertEqual(metodo, 'POST')
            self.assertEqual(cabeceras.get('Xi-api-key'), 'clave-de-prueba-123456')
            guardado = json.loads((self.base / 'voz.json').read_text(encoding='utf-8'))
            self.assertNotIn('clave-de-prueba', json.dumps(guardado))
            with self.assertRaises(ValueError):
                voz_tts.guardar_config(self.base, {'proveedor': 'elevenlabs', 'voz': '../x'})

    def test_errores_http_se_traducen_sin_exponer_la_clave(self):
        import urllib.error

        def falla(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 401, 'Unauthorized', {}, None)

        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'clave-de-prueba-123456'}), patch('urllib.request.urlopen', falla):
            with self.assertRaises(ValueError) as ctx:
                voz_tts.voces(self.base)
            self.assertNotIn('clave-de-prueba', str(ctx.exception))
            self.assertIn('rechazó la clave', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
