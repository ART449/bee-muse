'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {EventEmitter}=require('node:events');
const {DEFAULTS,readConfig,wslPath,buildCommand,baseURL,probe,waitForServer,createManager}=require('./beecode.cjs');

function ok(body){return {status:200,json:async()=>body};}
function status(code){return {status:code,json:async()=>({home:'/h',directory:'/d'})};}
function broken(){return {status:200,json:async()=>{throw Error('no json');}};}
function down(){throw Error('ECONNREFUSED');}

function fakeSpawn(){
  const calls=[];
  const spawnImpl=(file,args,options)=>{
    const child=new EventEmitter();
    child.pid=4242;
    child.stdout=new EventEmitter();
    child.stderr=new EventEmitter();
    child.kill=()=>{child.killed=true;return true;};
    calls.push({file,args,options,child});
    return child;
  };
  return {spawnImpl,calls};
}
function fetchSequence(states){
  let index=0;
  return ()=>{
    const state=states[Math.min(index,states.length-1)];
    index++;
    if(state==='beecode')return ok({home:'/home/vasart',directory:'/home/vasart/proyecto'});
    if(state==='other')return status(500);
    return down();
  };
}

test('readConfig usa los valores por defecto cuando el entorno está vacío',()=>{
  assert.deepEqual(readConfig({}),{distro:DEFAULTS.distro,bin:DEFAULTS.bin,port:DEFAULTS.port});
  assert.deepEqual(readConfig({BEECODE_WSL_DISTRO:'',BEECODE_WSL_BIN:'',BEECODE_PORT:''}),{distro:DEFAULTS.distro,bin:DEFAULTS.bin,port:DEFAULTS.port});
});

test('readConfig respeta las variables de entorno',()=>{
  const config=readConfig({BEECODE_WSL_DISTRO:'Ubuntu-24.04',BEECODE_WSL_BIN:'/usr/local/bin/bee-code',BEECODE_PORT:'5123'});
  assert.deepEqual(config,{distro:'Ubuntu-24.04',bin:'/usr/local/bin/bee-code',port:5123});
});

test('readConfig rechaza un distro inválido',()=>{
  assert.throws(()=>readConfig({BEECODE_WSL_DISTRO:'Debian; rm -rf /'}),/BEECODE_WSL_DISTRO/);
  assert.throws(()=>readConfig({BEECODE_WSL_DISTRO:'Debian GNU/Linux'}),/BEECODE_WSL_DISTRO/);
  assert.throws(()=>readConfig({BEECODE_WSL_DISTRO:'a'.repeat(65)}),/BEECODE_WSL_DISTRO/);
});

test('readConfig rechaza un binario que no es ruta POSIX absoluta',()=>{
  assert.throws(()=>readConfig({BEECODE_WSL_BIN:'bee-code'}),/BEECODE_WSL_BIN/);
  assert.throws(()=>readConfig({BEECODE_WSL_BIN:'C:\\bin\\bee-code.exe'}),/BEECODE_WSL_BIN/);
  assert.throws(()=>readConfig({BEECODE_WSL_BIN:'/home/vasart/my bin/bee-code'}),/BEECODE_WSL_BIN/);
  assert.throws(()=>readConfig({BEECODE_WSL_BIN:'/home/vasart/"bee-code"'}),/BEECODE_WSL_BIN/);
  assert.throws(()=>readConfig({BEECODE_WSL_BIN:'/home/vasart/../etc/bee-code'}),/BEECODE_WSL_BIN/);
  assert.throws(()=>readConfig({BEECODE_WSL_BIN:'/home/vasart/\u0001bee-code'}),/BEECODE_WSL_BIN/);
});

test('readConfig rechaza un puerto inválido',()=>{
  assert.throws(()=>readConfig({BEECODE_PORT:'80'}),/BEECODE_PORT/);
  assert.throws(()=>readConfig({BEECODE_PORT:'70000'}),/BEECODE_PORT/);
  assert.throws(()=>readConfig({BEECODE_PORT:'abc'}),/BEECODE_PORT/);
  assert.throws(()=>readConfig({BEECODE_PORT:'4096.5'}),/BEECODE_PORT/);
});

test('wslPath convierte las barras invertidas de Windows',()=>{
  assert.equal(wslPath('C:\\Users\\x\\proj'),'C:/Users/x/proj');
  assert.equal(wslPath('D:\\a\\b\\'),'D:/a/b/');
  assert.equal(wslPath('/home/vasart'),'/home/vasart');
  assert.throws(()=>wslPath(''),/ruta/i);
  assert.throws(()=>wslPath(null),/ruta/i);
});

test('buildCommand compone el comando de wsl.exe',()=>{
  const config=readConfig({BEECODE_WSL_DISTRO:'Debian',BEECODE_WSL_BIN:'/home/vasart/.local/bin/bee-code',BEECODE_PORT:'4096'});
  const command=buildCommand(config,'C:\\BYFLOW\\bee-muse');
  assert.equal(command.file,'wsl.exe');
  assert.deepEqual(command.args,['-d','Debian','--cd','C:/BYFLOW/bee-muse','--exec','/home/vasart/.local/bin/bee-code','serve','--port','4096','--hostname','127.0.0.1']);
});

test('baseURL apunta al servidor local',()=>{
  assert.equal(baseURL(4096),'http://127.0.0.1:4096');
});

test('probe distingue beecode, other y down',async()=>{
  assert.equal(await probe(4096,{fetchImpl:async()=>ok({home:'/h',directory:'/d'})}),'beecode');
  assert.equal(await probe(4096,{fetchImpl:async()=>status(404)}),'other');
  assert.equal(await probe(4096,{fetchImpl:async()=>broken()}),'other');
  assert.equal(await probe(4096,{fetchImpl:async()=>ok({home:'/h'})}),'other');
  assert.equal(await probe(4096,{fetchImpl:async()=>ok({home:1,directory:2})}),'other');
  assert.equal(await probe(4096,{fetchImpl:async()=>down()}),'down');
});

test('waitForServer resuelve cuando el servidor responde',async()=>{
  const result=await waitForServer(4096,{fetchImpl:async()=>ok({home:'/h',directory:'/d'}),timeoutMs:500,intervalMs:5});
  assert.equal(result,true);
});

test('waitForServer agota el tiempo de espera',async()=>{
  await assert.rejects(()=>waitForServer(4096,{fetchImpl:async()=>down(),timeoutMs:30,intervalMs:5}),/BeeCode no respondió en/);
});

test('waitForServer detecta el proceso muerto',async()=>{
  await assert.rejects(()=>waitForServer(4096,{fetchImpl:async()=>down(),timeoutMs:500,intervalMs:5,isDead:()=>true}),/BeeCode se cerró antes de abrir el puerto\./);
});

test('waitForServer avisa cuando el puerto está ocupado',async()=>{
  await assert.rejects(()=>waitForServer(4096,{fetchImpl:async()=>status(500),timeoutMs:500,intervalMs:5}),/ocupa otro programa/);
  await assert.rejects(()=>waitForServer(4096,{fetchImpl:async()=>status(500),timeoutMs:500,intervalMs:5}),/BEECODE_PORT/);
});

test('el gestor reutiliza un servidor ajeno sin lanzar nada',async()=>{
  const {spawnImpl,calls}=fakeSpawn();
  const manager=createManager({spawnImpl,fetchImpl:async()=>ok({home:'/h',directory:'/d'}),env:{}});
  const url=await manager.ensure('C:\\BYFLOW\\bee-muse');
  assert.equal(url,baseURL(DEFAULTS.port));
  assert.equal(calls.length,0);
  assert.equal(manager.owned(),false);
});

test('el gestor lanza el proceso cuando el puerto está libre',async()=>{
  const {spawnImpl,calls}=fakeSpawn();
  const manager=createManager({spawnImpl,fetchImpl:fetchSequence(['down','beecode']),env:{},timeoutMs:500,intervalMs:5});
  const url=await manager.ensure('C:\\BYFLOW\\bee-muse');
  assert.equal(url,baseURL(DEFAULTS.port));
  assert.equal(calls.length,1);
  assert.equal(calls[0].file,'wsl.exe');
  assert.equal(calls[0].options.windowsHide,true);
  assert.deepEqual(calls[0].options.stdio,['ignore','pipe','pipe']);
  assert.equal(calls[0].options.env.WSL_UTF8,'1');
  assert.equal(manager.owned(),true);
});

test('dos llamadas concurrentes a ensure comparten un solo proceso',async()=>{
  const {spawnImpl,calls}=fakeSpawn();
  const manager=createManager({spawnImpl,fetchImpl:fetchSequence(['down','beecode']),env:{},timeoutMs:500,intervalMs:5});
  const [first,second]=await Promise.all([manager.ensure('C:\\a'),manager.ensure('C:\\b')]);
  assert.equal(first,baseURL(DEFAULTS.port));
  assert.equal(second,baseURL(DEFAULTS.port));
  assert.equal(calls.length,1);
});

test('stop mata sólo el proceso propio y es idempotente',async()=>{
  const {spawnImpl,calls}=fakeSpawn();
  const killed=[];
  const manager=createManager({spawnImpl,killImpl:child=>{killed.push(child);},fetchImpl:fetchSequence(['down','beecode']),env:{},timeoutMs:500,intervalMs:5});
  await manager.ensure('C:\\BYFLOW\\bee-muse');
  assert.equal(manager.owned(),true);
  manager.stop();
  manager.stop();
  assert.equal(killed.length,1);
  assert.equal(killed[0],calls[0].child);
  assert.equal(manager.owned(),false);
});

test('stop sin proceso propio no mata nada',async()=>{
  const {spawnImpl}=fakeSpawn();
  const killed=[];
  const manager=createManager({spawnImpl,killImpl:child=>{killed.push(child);},fetchImpl:async()=>ok({home:'/h',directory:'/d'}),env:{}});
  manager.stop();
  assert.equal(killed.length,0);
});

test('un fallo ENOENT informa que falta wsl.exe',async()=>{
  const calls=[];
  const spawnImpl=(file,args,options)=>{
    const child=new EventEmitter();
    child.pid=4242;
    child.stdout=new EventEmitter();
    child.stderr=new EventEmitter();
    calls.push(child);
    setTimeout(()=>child.emit('error',Object.assign(Error('spawn wsl.exe ENOENT'),{code:'ENOENT'})),0);
    return child;
  };
  const manager=createManager({spawnImpl,killImpl:()=>{},fetchImpl:async()=>down(),env:{},timeoutMs:500,intervalMs:5});
  await assert.rejects(()=>manager.ensure('C:\\BYFLOW\\bee-muse'),/wsl\.exe/);
  assert.equal(calls.length,1);
  assert.equal(manager.owned(),false);
});

test('un puerto ocupado lanza el error sin lanzar ningún proceso',async()=>{
  const {spawnImpl,calls}=fakeSpawn();
  const manager=createManager({spawnImpl,fetchImpl:async()=>status(500),env:{}});
  await assert.rejects(()=>manager.ensure('C:\\BYFLOW\\bee-muse'),/ocupa otro programa/);
  assert.equal(calls.length,0);
});

test('el fallo del proceso incluye la salida y la pista de configuración',async()=>{
  const spawnImpl=()=>{
    const child=new EventEmitter();
    child.pid=4242;
    child.stdout=new EventEmitter();
    child.stderr=new EventEmitter();
    setTimeout(()=>{child.stdout.emit('data','bee-code: no such command\n');child.emit('exit',1);},0);
    return child;
  };
  const manager=createManager({spawnImpl,killImpl:()=>{},fetchImpl:async()=>down(),env:{},timeoutMs:120,intervalMs:5});
  await assert.rejects(()=>manager.ensure('C:\\BYFLOW\\bee-muse'),error=>{
    assert.match(error.message,/bee-code: no such command/);
    assert.match(error.message,/BEECODE_WSL_DISTRO/);
    assert.match(error.message,/BEECODE_WSL_BIN/);
    return true;
  });
});
