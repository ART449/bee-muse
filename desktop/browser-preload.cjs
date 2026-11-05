'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('BeeBrowser',{
  action:(action,value)=>ipcRenderer.invoke('bee-browser-action',action,value),
  openTool:tool=>ipcRenderer.invoke('bee-browser-tool',tool),
  subscribe:callback=>{ipcRenderer.on('bee-browser-state',(event,state)=>callback(state));}
});
