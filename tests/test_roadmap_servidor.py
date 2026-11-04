import http.client
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'service'))
import server


class RutasRoadmapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name)
        for name in ('muse.html', 'conexiones.html', 'hilos.js', 'hilos.css', 'conexiones-extra.js'):
            (cls.base / name).write_bytes((ROOT / 'service' / name).read_bytes())
        (cls.base / 'catalog.json').write_text(json.dumps({'total': 0, 'files': []}), encoding='utf-8')
        cls.patch = patch.object(server, 'BASE', cls.base)
        cls.patch.start()
        cls.httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.port = cls.httpd.server_port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.patch.stop()
        cls.temp.cleanup()

    def pedir(self, metodo, ruta, cuerpo=None, token=True, origin=True):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        cabeceras = {}
        if token:
            cabeceras['X-Library-Token'] = server.SESSION_TOKEN
        if cuerpo is not None:
            cabeceras['Content-Type'] = 'application/json'
            if origin:
                cabeceras['Origin'] = 'http://127.0.0.1:%d' % self.port
        conn.request(metodo, ruta, body=json.dumps(cuerpo) if cuerpo is not None else None, headers=cabeceras)
        r = conn.getresponse()
        datos = r.read()
        conn.close()
        try:
            return r.status, json.loads(datos), r.headers
        except ValueError:
            return r.status, datos, r.headers

    def test_hilos_por_http_con_token_y_sin_token(self):
        estado, datos, _ = self.pedir('POST', '/api/hilos/crear', {'titulo': 'Prueba HTTP'})
        self.assertEqual(estado, 200, datos)
        ident = datos['activo']
        estado, datos, _ = self.pedir('POST', '/api/hilos/mensaje', {'role': 'user', 'content': 'hola'})
        self.assertEqual(estado, 200, datos)
        estado, datos, _ = self.pedir('GET', '/api/hilos?id=' + ident)
        self.assertEqual(estado, 200)
        self.assertEqual(datos['mensajes'][0]['content'], 'hola')
        estado, datos, _ = self.pedir('GET', '/api/hilos', token=False)
        self.assertEqual(estado, 403)
        estado, datos, _ = self.pedir('POST', '/api/hilos/crear', {}, token=False)
        self.assertEqual(estado, 403)
        estado, datos, _ = self.pedir('POST', '/api/hilos/mensaje', {'role': 'user', 'content': 'token ghp_abc'})
        self.assertEqual(estado, 400)
        self.assertIn('clave', datos['error'])

    def test_mcp_y_voz_por_http(self):
        estado, datos, _ = self.pedir('GET', '/api/mcp', token=False)
        self.assertEqual(estado, 200)
        self.assertEqual(datos['servidores'], [])
        estado, datos, _ = self.pedir('POST', '/api/mcp/guardar', {'name': 'demo', 'command': 'python', 'args': ['-V']})
        self.assertEqual(estado, 200, datos)
        estado, datos, _ = self.pedir('POST', '/api/mcp/guardar', {'name': 'bee-muse', 'command': 'x'})
        self.assertEqual(estado, 400)
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': ''}):
            estado, datos, _ = self.pedir('GET', '/api/voz')
            self.assertEqual(estado, 200)
            self.assertFalse(datos['configurado'])
            estado, datos, _ = self.pedir('POST', '/api/voz/hablar', {'text': 'hola'})
            self.assertEqual(estado, 400)
            self.assertNotIn('xi-api-key', json.dumps(datos))

    def test_paginas_y_estaticos_con_csp_de_audio(self):
        estado, cuerpo, cabeceras = self.pedir('GET', '/muse', token=False)
        self.assertEqual(estado, 200)
        self.assertIn(b'/hilos.js', cuerpo)
        self.assertIn("media-src 'self' blob:", cabeceras.get('Content-Security-Policy', ''))
        for ruta in ('/hilos.js', '/hilos.css', '/conexiones-extra.js'):
            estado, cuerpo, _ = self.pedir('GET', ruta, token=False)
            self.assertEqual(estado, 200, ruta)
        estado, cuerpo, _ = self.pedir('GET', '/conexiones', token=False)
        self.assertIn(b'id="mcpSeccion"', cuerpo)
        self.assertIn(b'id="voz"', cuerpo)


if __name__ == '__main__':
    unittest.main()
