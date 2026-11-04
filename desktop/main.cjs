'use strict';
const {app,BrowserWindow,Menu,dialog,shell,ipcMain,clipboard}=require('electron');
const fs=require('node:fs');
const path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');
const {openBrowser}=require('./browser.cjs');
let mainWindow,backend,origin,ending=false;
const storageKeys=new Set(['html-library-selection','html-library-stages','html-bee-history','muse-agent-history']);
ipcMain.on('bee-storage',(event,action,key,value)=>{
  if(!mainWindow||event.sender!==mainWindow.webContents||!event.senderFrame?.url.startsWith(origin+'/')||!storageKeys.has(key)){event.returnValue=null;return;}
  const file=path.join(app.getPath('userData'),'library-state.json');
  try{let state={};try{state=JSON.parse(fs.readFileSync(file,'utf8'));}catch{}
    if(action==='get')event.returnValue=typeof state[key]==='string'?state[key]:null;
    else if(action==='set'&&typeof value==='string'&&Buffer.byteLength(value)<2*1024*1024){state[key]=value;fs.writeFileSync(file+'.tmp',JSON.stringify(state));fs.renameSync(file+'.tmp',file);event.returnValue=true;}
    else event.returnValue=null;
  }catch{event.returnValue=null;}
});
app.setName('Bee-Muse');
app.setPath('userData',process.env.BEE_MUSE_DATA_DIR&&path.isAbsolute(process.env.BEE_MUSE_DATA_DIR)?process.env.BEE_MUSE_DATA_DIR:path.join(app.getPath('appData'),'Bee-Muse'));
const locked=app.requestSingleInstanceLock();
if(!locked)app.quit();
app.on('second-instance',()=>{if(mainWindow){mainWindow.restore();mainWindow.show();mainWindow.focus();}});
function resources(){return app.isPackaged?process.resourcesPath:__dirname;}
function configFile(){return path.join(app.getPath('userData'),'desktop.json');}
function library(){
  let target=path.join(app.getPath('userData'),'library');
  try{const saved=JSON.parse(fs.readFileSync(configFile(),'utf8'));if(typeof saved.library==='string'&&path.isAbsolute(saved.library)&&fs.existsSync(saved.library))target=saved.library;}catch{}
  fs.mkdirSync(target,{recursive:true});
  const template=path.join(resources(),'library-template');
  for(const name of fs.readdirSync(template)){const source=path.join(template,name),destination=path.join(target,name);if(/\.(html|js|css)$/.test(name)||name==='mascotas')fs.cpSync(source,destination,{recursive:true,force:true});else if(!fs.existsSync(destination))fs.cpSync(source,destination,{recursive:true,force:false,errorOnExist:false});}
  return target;
}
function trustedMain(event){return mainWindow&&event.sender===mainWindow.webContents&&event.senderFrame===mainWindow.webContents.mainFrame&&event.senderFrame.url.startsWith(origin+'/');}
ipcMain.handle('bee-open-browser',event=>{if(!trustedMain(event))throw Error('Solicitud no permitida.');openBrowser(mainWindow);return true;});
ipcMain.handle('bee-open-account',async(event,flow,provider)=>{
  if(!trustedMain(event)||typeof flow!=='string'||!/^[-\w]{32}$/.test(flow)||!['google','facebook'].includes(provider))throw Error('Solicitud de acceso inválida.');
  const url=new URL(origin);url.hostname='localhost';url.pathname='/cuenta';url.search=new URLSearchParams({desktop:'1',flow,provider}).toString();
  await shell.openExternal(url.href);return true;
});
ipcMain.handle('bee-choose-folders',async event=>{
  if(!trustedMain(event))throw Error('Solicitud no permitida.');
  const result=await dialog.showOpenDialog(mainWindow,{title:'Elige las carpetas que quieres indexar',properties:['openDirectory','multiSelections']});
  return result.canceled?[]:result.filePaths.slice(0,12);
});
ipcMain.handle('bee-show-indexed-file',async(event,id)=>{
  if(!trustedMain(event)||typeof id!=='string'||!/^\w{20}$/.test(id))throw Error('Archivo no válido.');
  const response=await fetch(origin+'/api/files/record?id='+encodeURIComponent(id));
  if(!response.ok)throw Error('Archivo fuera del índice.');
  const record=await response.json();
  if(!path.isAbsolute(record.path)||!fs.existsSync(record.path))throw Error('El archivo ya no está disponible.');
  shell.showItemInFolder(record.path);return true;
});
function external(url){try{const u=new URL(url);if(['https:','http:'].includes(u.protocol)&&!['127.0.0.1','localhost'].includes(u.hostname))shell.openExternal(u.href);}catch{}}
function safeWindow(win){
  win.webContents.on('will-navigate',(event,url)=>{if(!url.startsWith(origin+'/')){event.preventDefault();external(url);}});
  win.webContents.setWindowOpenHandler(({url})=>{external(url);return {action:'deny'};});
  win.webContents.session.setPermissionRequestHandler((contents,permission,callback,details)=>{const url=details.requestingUrl||contents.getURL();const audioOnly=Array.isArray(details.mediaTypes)&&details.mediaTypes.length>0&&details.mediaTypes.every(type=>type==='audio');callback(contents===mainWindow.webContents&&url.startsWith(origin+'/')&&permission==='media'&&audioOnly);});
  win.webContents.on('will-attach-webview',event=>event.preventDefault());
}
async function chooseLibrary(){
  const result=await dialog.showOpenDialog(mainWindow,{title:'Abrir una biblioteca de Bee-Muse',properties:['openDirectory']});
  if(result.canceled)return;
  const folder=result.filePaths[0];
  if(!fs.existsSync(path.join(folder,'catalog.json'))){await dialog.showMessageBox(mainWindow,{type:'info',message:'Esa carpeta no contiene una biblioteca de Bee-Muse.',detail:'Elige la carpeta de la biblioteca existente. Tus archivos no se moverán.'});return;}
  fs.writeFileSync(configFile(),JSON.stringify({library:folder},null,2));app.relaunch();app.quit();
}
function menu(){
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {label:'Bee-Muse',submenu:[{label:'Mis archivos · elegir carpetas',click:()=>mainWindow.loadURL(origin+'/')},{label:'Mostrar carpeta de la aplicación',click:()=>shell.openPath(app.getPath('userData'))},{type:'separator'},{role:'quit',label:'Salir'}]},
    {label:'Ir a',submenu:[['Mis archivos','/'],['Biblioteca HTML','/html'],['Carpetas y movimientos','/carpetas'],['Muse','/muse'],['Apuntadora','/apuntadora'],['Conexiones','/conexiones'],['Hackatón','/hackaton']].map(([label,route])=>({label,click:()=>mainWindow.loadURL(origin+route)}))},
    {label:'Editar',submenu:[{role:'undo',label:'Deshacer'},{role:'redo',label:'Rehacer'},{type:'separator'},{role:'cut',label:'Cortar'},{role:'copy',label:'Copiar'},{role:'paste',label:'Pegar'},{role:'selectAll',label:'Seleccionar todo'}]},
    {label:'Navegador',submenu:[{label:'Abrir navegador Bee-Muse',click:()=>openBrowser(mainWindow)}]},
    {label:'Vista',submenu:[{role:'reload',label:'Recargar vista'},{role:'resetZoom',label:'Tamaño original'},{role:'zoomIn',label:'Acercar'},{role:'zoomOut',label:'Alejar'},{role:'togglefullscreen',label:'Pantalla completa'}]},
    {label:'Ayuda',submenu:[{label:'Acerca de Bee-Muse',click:()=>dialog.showMessageBox(mainWindow,{message:'Bee-Muse · IART Labs · La Colmena',detail:'Aplicación de escritorio 0.5.0. Biblioteca local y Muse en nube. Compilación de Windows; distribución pública y firma pendientes.'})}]}
  ]));
}
function contextMenu(contents){
  contents.on('context-menu',(event,params)=>{
    const items=[];
    const text=(params.selectionText||'').trim();
    if(params.linkURL){items.push({label:'Copiar enlace',click:()=>clipboard.writeText(params.linkURL)},{type:'separator'});}
    if(params.isEditable){items.push({role:'undo',label:'Deshacer'},{role:'redo',label:'Rehacer'},{type:'separator'},{role:'cut',label:'Cortar'},{role:'copy',label:'Copiar'},{role:'paste',label:'Pegar'},{role:'selectAll',label:'Seleccionar todo'});}
    else if(text){items.push({role:'copy',label:'Copiar'},{role:'selectAll',label:'Seleccionar todo'});}
    else{items.push({role:'selectAll',label:'Seleccionar todo'});}
    if(params.mediaType==='image'&&params.srcURL){items.push({type:'separator'},{label:'Copiar imagen',click:()=>contents.copyImageAt(params.x,params.y)});}
    if(!app.isPackaged){items.push({type:'separator'},{label:'Inspeccionar',click:()=>contents.inspectElement(params.x,params.y)});}
    event.preventDefault();
    Menu.buildFromTemplate(items).popup({window:BrowserWindow.fromWebContents(contents)||undefined,x:params.x,y:params.y});
  });
}
app.on('web-contents-created',(event,contents)=>contextMenu(contents));
function startBackend(folder){return new Promise((resolve,reject)=>{
  const exe=path.join(resources(),'backend',process.platform==='win32'?'bee-muse-service.exe':'bee-muse-service');
  const logs=path.join(app.getPath('userData'),'service.log');
  backend=spawn(exe,['--port','0'],{cwd:folder,env:{...process.env,BEE_LIBRARY_DIR:folder,PYTHONUTF8:'1'},windowsHide:true,stdio:['ignore','pipe','pipe']});
  let buffer='',ready=false;
  const timer=setTimeout(()=>reject(Error('El servicio no respondió al iniciar. Revisa service.log en la carpeta de la aplicación.')),45000);
  backend.stdout.on('data',data=>{buffer+=data.toString();const match=buffer.match(/http:\/\/127\.0\.0\.1:(\d+)/);if(match&&!ready){ready=true;clearTimeout(timer);resolve('http://127.0.0.1:'+match[1]);}});
  backend.stderr.on('data',data=>fs.appendFileSync(logs,data));
  backend.on('error',error=>{clearTimeout(timer);reject(error);});
  backend.on('exit',code=>{clearTimeout(timer);if(!ready)reject(Error('El servicio se cerró antes de iniciar (código '+code+').'));else if(!ending){dialog.showErrorBox('Bee-Muse se detuvo','El servicio local dejó de responder. Cierra y abre Bee-Muse; tu biblioteca se conserva.');app.quit();}});
});}
if(locked)app.whenReady().then(async()=>{
  try{
    fs.mkdirSync(app.getPath('userData'),{recursive:true});
    origin=await startBackend(library());
    mainWindow=new BrowserWindow({title:'Bee-Muse · IArtLabs · 0.5.0',width:1280,height:860,minWidth:680,minHeight:560,backgroundColor:'#0a0a0f',show:false,webPreferences:{preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true,partition:'persist:bee-muse-desktop'}});
    mainWindow.on('page-title-updated',event=>event.preventDefault());
    safeWindow(mainWindow);menu();
    mainWindow.once('ready-to-show',()=>mainWindow.show());
    await mainWindow.loadURL(origin+'/muse');
  }catch(error){dialog.showErrorBox('No se pudo abrir Bee-Muse',error.message);app.quit();}
});
app.on('window-all-closed',()=>app.quit());
app.on('before-quit',()=>{ending=true;if(backend&&!backend.killed){if(process.platform==='win32')spawnSync('taskkill.exe',['/PID',String(backend.pid),'/T','/F'],{windowsHide:true,timeout:8000});else backend.kill();}});
