"""Authenticated HTTPS gateway for the owner's mobile Bee-Muse client."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
import http.client
import json
import secrets
import ssl
import threading
import time
from urllib.parse import urlsplit


class Gateway(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,backend):
        super().__init__(address,Handler)
        target=urlsplit(backend)
        if target.scheme!='http' or target.hostname not in ('127.0.0.1','localhost') or not target.port:
            raise ValueError('El backend debe ser HTTP en loopback con puerto explícito.')
        self.backend=target
        self.lock=threading.Lock()
        self.pair_code=secrets.token_urlsafe(24)
        self.pair_expires=time.monotonic()+300
        self.sessions={}
        conn=http.client.HTTPConnection(target.hostname,target.port,timeout=10)
        conn.request('GET','/api/session');response=conn.getresponse()
        if response.status!=200:raise ValueError('El servicio local no responde.')
        self.local_token=json.loads(response.read())['token'];conn.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send_json(self,data,status=200,cookie=None):
        raw=json.dumps(data).encode()
        self.send_response(status);self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(raw)
    def authorized(self):
        try:
            jar=SimpleCookie();jar.load(self.headers.get('Cookie',''))
            key=jar['bee_remote'].value
        except (KeyError,ValueError):return False
        with self.server.lock:
            expiry=self.server.sessions.get(key,0)
            if expiry<time.monotonic():
                self.server.sessions.pop(key,None);return False
            return True
    def do_POST(self):
        if self.path=='/pair':
            # No browser cross-origin pairing and no codes in URLs or access logs.
            if self.headers.get('Origin'):
                return self.send_json({'error':'Empareja desde la aplicación.'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 1<=size<=1024:raise ValueError()
                body=json.loads(self.rfile.read(size))
                value=body.get('code')
                if not isinstance(value,str):raise ValueError()
                with self.server.lock:
                    valid=(time.monotonic()<self.server.pair_expires and
                           bool(self.server.pair_code) and secrets.compare_digest(value,self.server.pair_code))
                    if not valid:return self.send_json({'error':'Código inválido o vencido.'},401)
                    self.server.pair_code=None
                    session=secrets.token_urlsafe(32)
                    self.server.sessions[session]=time.monotonic()+8*3600
                return self.send_json({'paired':True},cookie='bee_remote='+session+'; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=28800')
            except (ValueError,TypeError):return self.send_json({'error':'Solicitud inválida.'},400)
        self.proxy()
    def do_GET(self):self.proxy()
    def proxy(self):
        if not self.authorized():return self.send_json({'error':'Empareja este dispositivo.'},401)
        if not self.path.startswith('/') or self.path.startswith('//') or '\\' in self.path:
            return self.send_json({'error':'Ruta inválida.'},400)
        # Keep remote tools out of server-level account configuration.
        if self.path.startswith('/api/jules/key') or self.path.startswith('/api/account/'):
            return self.send_json({'error':'Configura las cuentas desde el equipo principal.'},403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<=size<=4000000:raise ValueError()
            body=self.rfile.read(size) if size else None
            target=self.server.backend
            origin='http://127.0.0.1:'+str(target.port)
            headers={'Origin':origin,'X-Library-Token':self.server.local_token,
                     'Content-Type':self.headers.get('Content-Type','application/json')}
            conn=http.client.HTTPConnection('127.0.0.1',target.port,timeout=270)
            conn.request(self.command,self.path,body,headers)
            upstream=conn.getresponse();data=upstream.read(8*1024*1024+1)
            if len(data)>8*1024*1024:raise ValueError()
            self.send_response(upstream.status)
            self.send_header('Content-Type',upstream.getheader('Content-Type','application/json'))
            self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers();self.wfile.write(data);conn.close()
        except (OSError,ValueError,http.client.HTTPException):
            self.send_json({'error':'El servicio local no completó la solicitud.'},502)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Bee-Muse: acceso móvil HTTPS con emparejamiento de un solo uso.')
    parser.add_argument('--backend',default='http://127.0.0.1:8767')
    parser.add_argument('--bind',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=9443)
    parser.add_argument('--cert',required=True)
    parser.add_argument('--key',required=True)
    args=parser.parse_args()
    server=Gateway((args.bind,args.port),args.backend)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(args.cert,args.key)
    server.socket=context.wrap_socket(server.socket,server_side=True)
    print('Código de emparejamiento (un uso, 5 minutos): '+server.pair_code,flush=True)
    server.serve_forever()
