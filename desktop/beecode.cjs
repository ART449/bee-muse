'use strict';
const {spawn,spawnSync}=require('node:child_process');

const DEFAULTS={distro:'Debian',bin:'/home/vasart/.local/bin/bee-code',port:4096};
const OUTPUT_LIMIT=4000;
const TAIL_LIMIT=600;

const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const text=value=>value===undefined||value===null?'':String(value);
const clean=value=>String(value).replace(/\u0000/g,'');

function busyError(port){
  const error=Error(`El puerto ${port} ya lo ocupa otro programa. Define BEECODE_PORT con otro puerto para arrancar BeeCode.`);
  error.code='BEECODE_PORT_BUSY';
  return error;
}
function validDistro(value){return typeof value==='string'&&/^[\w.-]{1,64}$/.test(value);}
function validBin(value){
  if(typeof value!=='string'||!value.startsWith('/')||/\s/.test(value))return false;
  if(/['"`]/.test(value)||/[\u0000-\u001f\u007f]/.test(value))return false;
  return !value.split('/').includes('..');
}
function validPort(value){return Number.isInteger(value)&&value>=1024&&value<=65535;}

function readConfig(env=process.env){
  const source=env||{};
  const distro=text(source.BEECODE_WSL_DISTRO)||DEFAULTS.distro;
  const bin=text(source.BEECODE_WSL_BIN)||DEFAULTS.bin;
  const rawPort=text(source.BEECODE_PORT);
  if(!validDistro(distro))throw Error(`BEECODE_WSL_DISTRO inválido: "${distro}". Sólo admite letras, números, punto, guion y guion bajo (máximo 64 caracteres).`);
  if(!validBin(bin))throw Error(`BEECODE_WSL_BIN inválido: "${bin}". Debe ser una ruta POSIX absoluta (empieza por "/") sin espacios, comillas ni segmentos "..".`);
  const port=rawPort===''?DEFAULTS.port:(/^\d+$/.test(rawPort)?Number(rawPort):NaN);
  if(!validPort(port))throw Error(`BEECODE_PORT inválido: "${rawPort}". Debe ser un entero entre 1024 y 65535.`);
  return {distro,bin,port};
}

function wslPath(winPath){
  if(typeof winPath!=='string'||!winPath.length)throw Error('Ruta de trabajo inválida: se esperaba una ruta de Windows no vacía.');
  return winPath.split('\\').join('/');
}

function buildCommand(config,cwd){
  return {file:'wsl.exe',args:['-d',config.distro,'--cd',wslPath(cwd),'--exec',config.bin,'serve','--port',String(config.port),'--hostname','127.0.0.1']};
}

function baseURL(port){return 'http://127.0.0.1:'+port;}

async function probe(port,{fetchImpl=fetch,timeoutMs=3000}={}){
  let response;
  try{response=await fetchImpl(baseURL(port)+'/path',{signal:AbortSignal.timeout(timeoutMs)});}
  catch{return 'down';}
  if(!response||response.status!==200)return 'other';
  let data;
  try{data=await response.json();}
  catch{return 'other';}
  if(!data||typeof data!=='object')return 'other';
  if(typeof data.home!=='string'||typeof data.directory!=='string')return 'other';
  return 'beecode';
}

async function waitForServer(port,{fetchImpl=fetch,timeoutMs=30000,intervalMs=500,isDead=()=>false}={}){
  const deadline=Date.now()+timeoutMs;
  const seconds=Math.max(1,Math.ceil(timeoutMs/1000));
  for(;;){
    if(isDead())throw Error('BeeCode se cerró antes de abrir el puerto.');
    const remaining=Math.max(1,deadline-Date.now());
    const state=await probe(port,{fetchImpl,timeoutMs:Math.min(3000,remaining)});
    if(state==='beecode')return true;
    if(state==='other')throw busyError(port);
    if(Date.now()>=deadline)throw Error(`BeeCode no respondió en ${seconds} segundos.`);
    await delay(Math.max(0,Math.min(intervalMs,deadline-Date.now())));
  }
}

function defaultKill(child){
  if(process.platform==='win32'){
    spawnSync('taskkill.exe',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,timeout:8000});
    return;
  }
  if(child&&typeof child.kill==='function')child.kill();
}

function createManager({spawnImpl=spawn,killImpl,fetchImpl=fetch,env=process.env,timeoutMs=30000,intervalMs=500}={}){
  const kill=killImpl||defaultKill;
  let child=null,dead=false,pending=null;
  function owned(){return !!child&&!dead;}
  function stop(){
    const proc=child,alive=!!child&&!dead;
    child=null;dead=false;
    if(alive)kill(proc);
  }
  function failure(error,output,spawnError){
    if(error&&error.code==='BEECODE_PORT_BUSY')return error;
    if(spawnError&&spawnError.code==='ENOENT')
      return Error('No se encontró wsl.exe: WSL no está instalado en este equipo. Instálalo y revisa BEECODE_WSL_DISTRO / BEECODE_WSL_BIN.');
    const reason=error&&error.message?error.message:'BeeCode no arrancó.';
    const tail=output.slice(-TAIL_LIMIT);
    return Error(`${reason} Revisa BEECODE_WSL_DISTRO / BEECODE_WSL_BIN. Salida del proceso: ${tail||'(sin salida)'}`);
  }
  async function launch(cwd){
    const config=readConfig(env);
    const url=baseURL(config.port);
    const state=await probe(config.port,{fetchImpl});
    if(state==='beecode')return url;
    if(state==='other')throw busyError(config.port);
    if(child){if(!dead){try{kill(child);}catch{}}child=null;dead=false;}
    const {file,args}=buildCommand(config,cwd);
    let output='',spawnError=null;
    // WSL_UTF8=1: wsl.exe escribe sus propios mensajes en UTF-8 en vez de UTF-16.
    const proc=spawnImpl(file,args,{windowsHide:true,stdio:['ignore','pipe','pipe'],env:{...process.env,WSL_UTF8:'1'}});
    child=proc;dead=false;
    const capture=stream=>{
      if(!stream||typeof stream.on!=='function')return;
      stream.on('data',chunk=>{output=(output+clean(chunk)).slice(-OUTPUT_LIMIT);});
    };
    capture(proc.stdout);capture(proc.stderr);
    if(typeof proc.on==='function'){
      proc.on('exit',()=>{dead=true;});
      proc.on('error',error=>{dead=true;spawnError=error;});
    }
    try{
      await waitForServer(config.port,{fetchImpl,timeoutMs,intervalMs,isDead:()=>dead});
    }catch(error){
      if(proc&&!dead){try{kill(proc);}catch{}}
      if(child===proc){child=null;dead=false;}
      throw failure(error,output,spawnError);
    }
    return url;
  }
  function ensure(cwd){
    if(!pending)pending=launch(cwd).finally(()=>{pending=null;});
    return pending;
  }
  return {ensure,stop,owned};
}

module.exports={DEFAULTS,readConfig,wslPath,buildCommand,baseURL,probe,waitForServer,createManager};
