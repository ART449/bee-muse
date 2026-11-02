'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('BeeBrowser',{
  action:(action,value)=>ipcRenderer.invoke('bee-browser-action',action,value),
  subscribe:callback=>{ipcRenderer.on('bee-browser-state',(event,state)=>callback(state));}
});
