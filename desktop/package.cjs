'use strict';
const fs=require('node:fs'),path=require('node:path');
const {packager}=require('@electron/packager');
const stage=path.join(__dirname,'build','runtime');fs.mkdirSync(stage,{recursive:true});
for(const file of ['main.cjs','preload.cjs'])fs.copyFileSync(path.join(__dirname,file),path.join(stage,file));
const metadata=require('./package.json');delete metadata.devDependencies;delete metadata.scripts;
fs.writeFileSync(path.join(stage,'package.json'),JSON.stringify(metadata,null,2));
packager({dir:stage,name:'Bee-Muse',platform:process.platform,arch:process.arch,
  out:path.join(__dirname,'ready'),asar:true,
  extraResource:[path.join(__dirname,'backend'),path.join(__dirname,'library-template')],
  appBundleId:'com.iartlabs.beemuse',appCopyright:'IArtLabs',
  win32metadata:{CompanyName:'IArtLabs',FileDescription:'Bee-Muse · IArtLabs',ProductName:'Bee-Muse'}})
  .then(paths=>console.log(paths.join('\n'))).catch(error=>{console.error(error);process.exitCode=1;});
