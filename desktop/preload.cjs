'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('BeeDesktop',{chooseFolders:()=>ipcRenderer.invoke('bee-choose-folders'),chooseHtmlFolders:()=>ipcRenderer.invoke('bee-choose-folders'),showIndexedFile:id=>ipcRenderer.invoke('bee-show-indexed-file',id),storage:{
  getItem:key=>ipcRenderer.sendSync('bee-storage','get',key),
  setItem:(key,value)=>{const result=ipcRenderer.sendSync('bee-storage','set',key,value);if(result!==true)throw Error('No se pudo guardar la selección de escritorio.');}
}});
