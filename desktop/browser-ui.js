'use strict';
const $=id=>document.getElementById(id);
const action=(name,value)=>window.BeeBrowser.action(name,value).catch(()=>{$('status').textContent='No se pudo completar la navegación.';});
$('navigation').onsubmit=e=>{e.preventDefault();action('go',$('address').value.trim());};
for(const name of ['back','forward','reload'])$(name).onclick=()=>action(name);
window.BeeBrowser.subscribe(state=>{if(document.activeElement!==$('address'))$('address').value=state.url;$('back').disabled=!state.back;$('forward').disabled=!state.forward;$('status').textContent=state.error||state.title||'Bee-Muse · Navegación HTTPS';});
action('state');
