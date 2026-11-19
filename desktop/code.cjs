'use strict';
// Ventana "Code": levanta BeeCode (bee-code serve dentro de WSL) bajo demanda y muestra su interfaz web.
const {BrowserWindow,shell}=require('electron');
const {createManager}=require('./beecode.cjs');
const manager=createManager();
let window=null;
function escape(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function page(title,detail){
  const html='<!doctype html><meta charset="utf-8"><title>Code · BeeCode</title><style>body{margin:0;height:100vh;display:grid;place-items:center;background:#0a0a0f;color:#e8e6f0;font:15px system-ui,sans-serif}main{max-width:640px;padding:24px}h1{font-size:20px;margin:0 0 12px}pre{white-space:pre-wrap;color:#b9b4c8;font-size:13px}</style><main><h1>'+escape(title)+'</h1><pre>'+escape(detail)+'</pre></main>';
  return 'data:text/html;charset=utf-8,'+encodeURIComponent(html);
}
function external(url){try{const u=new URL(url);if(['https:','http:'].includes(u.protocol)&&!['127.0.0.1','localhost'].includes(u.hostname))shell.openExternal(u.href);}catch{}}
function guard(contents,origin){
  const inside=url=>{try{return new URL(url).origin===origin;}catch{return false;}};
  contents.on('will-navigate',(event,url)=>{if(!inside(url)){event.preventDefault();external(url);}});
  contents.on('will-redirect',(event,url)=>{if(!inside(url)){event.preventDefault();external(url);}});
  contents.setWindowOpenHandler(({url})=>{external(url);return {action:'deny'};});
}
async function openCode(parent,cwd){
  if(window&&!window.isDestroyed()){window.show();window.focus();return window;}
  const win=window=new BrowserWindow({parent,title:'Code · BeeCode',width:1280,height:860,minWidth:680,minHeight:480,backgroundColor:'#0a0a0f',webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true,partition:'persist:bee-code'}});
  win.on('page-title-updated',event=>event.preventDefault());
  const contents=win.webContents,session=contents.session;
  session.setPermissionRequestHandler((w,permission,done)=>done(permission==='clipboard-sanitized-write'));
  contents.on('will-attach-webview',event=>event.preventDefault());
  win.on('closed',()=>{if(window===win)window=null;manager.stop();});
  await contents.loadURL(page('Abriendo BeeCode…','Arrancando el servidor en WSL. La primera vez puede tardar unos segundos.\nCarpeta de trabajo: '+cwd)).catch(()=>{});
  try{
    const url=await manager.ensure(cwd);
    if(win.isDestroyed())return null;
    guard(contents,new URL(url).origin);
    await contents.loadURL(url+'/');
  }catch(error){
    if(!win.isDestroyed())await contents.loadURL(page('No se pudo abrir BeeCode',error.message+'\n\nRequisitos: WSL con la distribución indicada en BEECODE_WSL_DISTRO (Debian por defecto) y bee-code instalado en la ruta de BEECODE_WSL_BIN. Cierra esta ventana y vuelve a abrir Code para reintentar.')).catch(()=>{});
  }
  return win;
}
function stopCode(){manager.stop();}
module.exports={openCode,stopCode};
