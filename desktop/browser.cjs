'use strict';
const {BrowserWindow,WebContentsView,ipcMain,app}=require('electron');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
let window,view;
const toolbarURL=pathToFileURL(path.join(__dirname,'browser.html')).href;
function httpsURL(value){
  if(typeof value!=='string'||value.length>8192)throw Error('Dirección no válida.');
  const url=new URL(value.includes('://')?value:'https://'+value);
  if(url.protocol!=='https:'||!url.hostname||url.username||url.password)throw Error('Usa una dirección HTTPS sin credenciales.');
  return url.href;
}
function trusted(event){return window&&!window.isDestroyed()&&event.sender===window.webContents&&event.senderFrame===window.webContents.mainFrame&&event.senderFrame.url===toolbarURL;}
function state(error=''){
  if(!window||window.isDestroyed()||!view||view.webContents.isDestroyed())return;
  const w=view.webContents;
  window.webContents.send('bee-browser-state',{url:w.getURL()==='about:blank'?'':w.getURL(),title:w.getTitle().slice(0,200),back:w.navigationHistory.canGoBack(),forward:w.navigationHistory.canGoForward(),error});
}
ipcMain.handle('bee-browser-action',async(event,action,value)=>{
  if(!trusted(event)||!view||view.webContents.isDestroyed())throw Error('Solicitud no permitida.');
  const w=view.webContents;
  try{
    if(action==='go')await w.loadURL(httpsURL(value));
    else if(action==='back'&&w.navigationHistory.canGoBack())w.navigationHistory.goBack();
    else if(action==='forward'&&w.navigationHistory.canGoForward())w.navigationHistory.goForward();
    else if(action==='reload')w.reload();
    else if(action!=='state')throw Error('Acción no admitida.');
    state();return true;
  }catch(error){state(error.message);return false;}
});
function openBrowser(parent,{show=true}={}){
  if(window&&!window.isDestroyed()){window.show();window.focus();return;}
  window=new BrowserWindow({parent,show,title:'Navegador Bee-Muse',width:1150,height:800,minWidth:640,minHeight:400,backgroundColor:'#15121d',webPreferences:{preload:path.join(__dirname,'browser-preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true}});
  view=new WebContentsView({webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true,partition:'persist:bee-browser'}});
  window.contentView.addChildView(view);
  const resize=()=>{if(!window||window.isDestroyed())return;const [width,height]=window.getContentSize();view.setBounds({x:0,y:100,width,height:Math.max(0,height-100)});};
  window.on('resize',resize);resize();
  const contents=view.webContents,session=contents.session;
  session.setPermissionRequestHandler((w,p,done)=>done(false));session.setPermissionCheckHandler(()=>false);
  // Save dialogs are owned by Electron; downloaded files are never executed by Bee-Muse.
  if(!session.beeDownloadConfigured){session.beeDownloadConfigured=true;session.on('will-download',(event,item)=>item.setSaveDialogOptions({title:'Guardar descarga de Bee-Muse',defaultPath:path.join(app.getPath('downloads'),path.basename(item.getFilename()))}));}
  function guard(event,url){try{httpsURL(url);if(!url.startsWith('https://'))throw Error();}catch{event.preventDefault();state('Sólo se admiten páginas HTTPS.');}}
  contents.on('will-navigate',guard);contents.on('will-redirect',guard);
  contents.setWindowOpenHandler(({url})=>{try{contents.loadURL(httpsURL(url)).catch(e=>state(e.message));}catch(e){state(e.message);}return {action:'deny'};});
  contents.on('will-attach-webview',event=>event.preventDefault());
  contents.on('did-navigate',()=>state());contents.on('did-navigate-in-page',()=>state());contents.on('page-title-updated',()=>state());
  contents.on('did-fail-load',(e,code,description)=>{if(code!==-3)state('No se pudo abrir la página: '+description);});
  window.webContents.on('will-navigate',event=>event.preventDefault());window.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  window.on('closed',()=>{if(!contents.isDestroyed())contents.close();window=null;view=null;});
  window.loadFile(path.join(__dirname,'browser.html')).catch(()=>{});
  return window;
}
module.exports={openBrowser,httpsURL};
