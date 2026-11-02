import base64
import contextlib
import http.client
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'service'))
import server
import library_chat
import muse_agent
import account_identity
from tools_mcp import LibraryTools


class IndexedToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.base=Path(self.temp.name)
        self.html=self.base/'Nexus.html'
        self.html.write_text('<title>Nexus</title><p>Hola</p>',encoding='utf-8')
        self.ident='a'*20
        (self.base/'catalog.json').write_text(json.dumps({'files':[{'id':self.ident,'name':self.html.name,'title':'Nexus','path':str(self.html)}]}),encoding='utf-8')
        self.tools=LibraryTools(self.base)
    def tearDown(self):self.temp.cleanup()
    def test_search_title_and_read_only_selected_file(self):
        found=self.tools.search('nexus',html_only=True)
        self.assertEqual(found['matches'],1)
        self.assertEqual(self.tools.read_text(found['files'][0]['id'])['text'],'<title>Nexus</title><p>Hola</p>')
        with self.assertRaises(ValueError):self.tools.read_text('../../outside')
        with self.assertRaises(ValueError):self.tools.record('html:'+'b'*20)
    def test_all_file_types_use_existing_database(self):
        with contextlib.closing(sqlite3.connect(self.base/'indice-carpetas.sqlite')) as conn:
            conn.execute('CREATE TABLE files(path TEXT,bytes INTEGER,modified REAL)')
            conn.executemany('INSERT INTO files VALUES(?,?,?)',[(str(self.base/'abeja.png'),12,1),(str(self.base/'.env'),20,1),(str(self.html),30,1)])
            conn.commit()
        result=self.tools.search(extension='png')
        self.assertEqual([r['name'] for r in result['files']],['abeja.png'])
        self.assertNotIn('.env',[r['name'] for r in self.tools.search()['files']])
        self.assertFalse(self.tools.search()['partial'])
    def test_limits_and_types(self):
        for limit in (0,101,True):
            with self.assertRaises(ValueError):self.tools.search(limit=limit)
        with self.assertRaises(ValueError):self.tools.search(extension='../')
    def test_symlink_does_not_allow_index_escape(self):
        link=self.base/'link.html'
        try:link.symlink_to(self.html)
        except OSError:self.skipTest('Symlink creation unavailable')
        (self.base/'catalog.json').write_text(json.dumps({'files':[{'id':'b'*20,'path':str(link)}]}),encoding='utf-8')
        with self.assertRaises(ValueError):LibraryTools(self.base).read_text('html:'+'b'*20)


class ConversationTests(unittest.TestCase):
    def test_general_conversation_is_not_gated_by_catalog(self):
        response={'message':'Aquí estoy','files':[],'proposal':None,'mode':'conversation'}
        with patch.object(muse_agent,'converse',return_value=response) as talk:
            self.assertEqual(library_chat.propose({'files':[]},'Hola, ¿cómo estás?',[]),response)
            talk.assert_called_once()
    def test_no_matches_still_reaches_muse(self):
        with patch.object(muse_agent,'converse',return_value={'message':'Sin inventar archivos'}) as talk:
            library_chat.propose({'files':[]},'Busca Nexus',[])
            talk.assert_called_once()
    def test_workspace_cannot_be_missing_or_relative(self):
        for value in ('missing-folder','',42):
            with self.assertRaises(ValueError):muse_agent.workspace(value)


class IdentityTests(unittest.TestCase):
    def token(self,provider):
        claims={'aud':'test-project','iss':'https://securetoken.google.com/test-project','sub':'test-user',
                'exp':time.time()+1800,'firebase':{'sign_in_provider':provider}}
        body=base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip('=')
        return 'header.'+body+'.signature'
    def test_facebook_lookup_is_required_and_email_is_optional(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return json.dumps({'users':[{'localId':'test-user','displayName':'Test','providerUserInfo':[{'providerId':'facebook.com'}]}]}).encode()
        with patch.object(account_identity,'config',return_value={'apiKey':'test','authDomain':'test','projectId':'test-project','appId':'test'}),patch.object(account_identity.urllib.request,'urlopen',return_value=Response()):
            _,data=account_identity.verify(Path('.'),self.token('facebook.com'))
            self.assertEqual(data['user']['provider'],'facebook.com')
    def test_unknown_provider_rejected_before_network(self):
        with patch.object(account_identity,'config',return_value={'apiKey':'test','authDomain':'test','projectId':'test-project','appId':'test'}),patch.object(account_identity.urllib.request,'urlopen') as request:
            with self.assertRaises(ValueError):account_identity.verify(Path('.'),self.token('password'))
            request.assert_not_called()


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.base=Path(cls.temp.name)
        import shutil
        for path in (ROOT/'service').iterdir():
            if path.suffix in ('.html','.js','.css'):shutil.copy2(path,cls.base/path.name)
        shutil.copytree(ROOT/'service'/'mascotas',cls.base/'mascotas')
        cls.previous=server.BASE
        server.BASE=cls.base
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
        cls.port=cls.http.server_port
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();server.BASE=cls.previous;cls.temp.cleanup()
    def request(self,path,body=None,authorized=True,origin=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=8)
        headers={}
        if authorized:headers['X-Library-Token']=server.SESSION_TOKEN
        if body is not None:
            headers['Origin']=origin or 'http://127.0.0.1:'+str(self.port)
            headers['Content-Type']='application/json'
        conn.request('POST' if body is not None else 'GET',path,None if body is None else json.dumps(body),headers)
        result=conn.getresponse();status=result.status;data=result.read();conn.close();return status,data
    def test_new_ui_and_nine_animations_are_served(self):
        status,body=self.request('/muse')
        self.assertEqual(status,200);self.assertIn(b'agentForm',body)
        for state in ('idle','waving','waiting','running','review','jumping','failed','running-left','running-right'):
            status,data=self.request('/mascotas/cyberbee-octohype/'+state+'.gif')
            self.assertEqual(status,200);self.assertTrue(data.startswith(b'GIF'))
    def test_workspace_routes_keep_local_token_and_origin_gate(self):
        self.assertEqual(self.request('/api/muse/workspace',authorized=False)[0],403)
        self.assertEqual(self.request('/api/muse/workspace',{'path':str(self.base)},origin='https://untrusted.example')[0],403)
        self.assertEqual(self.request('/api/muse/workspace',{'path':str(self.base)})[0],200)
    def test_voice_rejects_invalid_audio_without_invoking_muse(self):
        with patch.object(server.voice_bridge.subprocess,'run') as command:
            self.assertEqual(self.request('/api/muse/transcribe',{'audio':'not-a-wav'})[0],400)
            command.assert_not_called()
    def test_async_conversation_returns_real_completion_state(self):
        with patch.object(muse_agent,'converse',return_value={'message':'Hola','files':[],'mode':'conversation'}):
            status,data=self.request('/api/muse/start',{'message':'Hola'})
            self.assertEqual(status,202)
            key=json.loads(data)['id']
            for _ in range(30):
                status,data=self.request('/api/muse/job?id='+key)
                row=json.loads(data)
                if row['state']!='running':break
                time.sleep(.02)
            self.assertEqual(row['state'],'completed');self.assertEqual(row['result']['message'],'Hola')


if __name__=='__main__':unittest.main()
