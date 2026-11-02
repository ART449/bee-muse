'use strict';
const fs=require('node:fs'),path=require('node:path');
const {packager}=require('@electron/packager');
const stage=path.join(__dirname,'build','runtime');fs.mkdirSync(stage,{recursive:true});
for(const file of ['main.cjs','preload.cjs','browser.cjs','browser-preload.cjs','browser-ui.js','browser.html'])fs.copyFileSync(path.join(__dirname,file),path.join(stage,file));
const metadata=require('./package.json');delete metadata.devDependencies;delete metadata.scripts;
fs.writeFileSync(path.join(stage,'package.json'),JSON.stringify(metadata,null,2));
packager({dir:stage,name:'Bee-Muse',platform:process.platform,arch:process.arch,
  out:path.join(__dirname,'ready'),asar:true,
  extraResource:[path.join(__dirname,'backend'),path.join(__dirname,'library-template')],
  appBundleId:'com.iartlabs.beemuse',appCopyright:'IArtLabs',
  win32metadata:{CompanyName:'IArtLabs',FileDescription:'Bee-Muse · IArtLabs',ProductName:'Bee-Muse'}})
  .then(paths=>{
    if(process.platform==='win32')for(const folder of paths){
      for(const file of ['install_windows.ps1','uninstall_windows.ps1'])fs.copyFileSync(path.join(__dirname,'..','scripts',file),path.join(folder,file));
      fs.writeFileSync(path.join(folder,'Instalar-Bee-Muse.cmd'),'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" -Package "%~dp0."\r\nif errorlevel 1 pause\r\n');
    }
    console.log(paths.join('\n'));
  }).catch(error=>{console.error(error);process.exitCode=1;});
