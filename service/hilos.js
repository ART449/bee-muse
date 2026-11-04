/* Hilos de conversación con Muse. Capa aparte: no modifica el historial corto de muse.js; lo alimenta.
   Retomar un hilo = escribir sus últimos mensajes en el historial que muse.js ya restaura y recargar. */
(()=>{'use strict';
const chat=document.getElementById('agentChat'),form=document.getElementById('agentForm'),area=document.getElementById('agentMessage');
if(!chat||!form||!area)return;
const CLAVE='muse-agent-history';
let activo=null,hilos=[],pendiente=null,abierta=false;
async function token(){return (await(await fetch('/api/session')).json()).token;}
async function api(ruta,cuerpo){const t=await token();const r=await fetch(ruta,{method:cuerpo===undefined?'GET':'POST',headers:{'X-Library-Token':t,...(cuerpo===undefined?{}:{'Content-Type':'application/json'})},body:cuerpo===undefined?undefined:JSON.stringify(cuerpo)});let d={};try{d=await r.json();}catch{}if(!r.ok)throw Error(d.error||'No se pudo completar.');return d;}
function el(tag,clase,texto){const n=document.createElement(tag);if(clase)n.className=clase;if(texto!=null)n.textContent=texto;return n;}
function boton(texto,fn,clase){const b=el('button',clase,texto);b.type='button';b.onclick=fn;return b;}
function cuando(iso){try{const d=new Date(iso);const dif=(Date.now()-d.getTime())/60000;if(dif<1)return 'ahora';if(dif<60)return 'hace '+Math.round(dif)+' min';if(dif<1440)return 'hace '+Math.round(dif/60)+' h';return d.toLocaleDateString('es-MX',{day:'numeric',month:'short'});}catch{return '';}}
const barra=el('div');barra.id='hilosBarra';barra.setAttribute('aria-label','Hilos de conversación');
const actual=el('div','hilos-actual');const titulo=el('span');const sub=el('small');actual.append(titulo,sub);
const btnLista=boton('Hilos',()=>{abierta=!abierta;lista.hidden=!abierta;btnLista.setAttribute('aria-expanded',String(abierta));});btnLista.setAttribute('aria-expanded','false');btnLista.setAttribute('aria-controls','hilosLista');
const btnNuevo=boton('Nuevo hilo',nuevo,'primary');
const lista=el('ul');lista.id='hilosLista';lista.hidden=true;const aviso=el('p');aviso.id='hilosAviso';aviso.setAttribute('role','status');
barra.append(actual,btnLista,btnNuevo,lista,aviso);
const envoltura=chat.closest('.chatwrap')||chat;envoltura.parentNode.insertBefore(barra,envoltura);
function pintar(){const h=hilos.find(x=>x.id===activo);titulo.textContent=h?h.titulo:'Sin hilo activo';sub.textContent=h?(h.mensajes+' mensajes · '+cuando(h.actualizado)):'El primer mensaje abre un hilo nuevo.';
  lista.replaceChildren();if(!hilos.length){lista.appendChild(el('li',null,'Todavía no hay hilos guardados. Conversa con Muse y aquí aparecerán.'));return;}
  for(const h of hilos){const li=el('li',h.id===activo?'hilo-activo':'');const t=boton('',()=>retomar(h.id),'hilo-titulo');t.append(document.createTextNode(h.titulo),el('small',null,h.mensajes+' mensajes · '+cuando(h.actualizado)+(h.ultimo?' · '+h.ultimo.slice(0,70):'')));t.setAttribute('aria-label','Retomar '+h.titulo);
    const acc=el('div','hilo-acciones');acc.append(boton('Renombrar',()=>renombrar(li,h)),boton('Borrar',()=>borrar(li,h)));li.append(t,acc);lista.appendChild(li);}}
async function cargar(){try{const d=await api('/api/hilos');hilos=d.hilos;activo=d.activo;pintar();}catch(e){aviso.textContent=e.message;}}
function guardarLocal(mensajes){try{const store=window.BeeDesktop?.storage||localStorage;store.setItem(CLAVE,JSON.stringify(mensajes.slice(-12).map(m=>({role:m.role,content:m.content}))));}catch{}}
async function retomar(id){try{aviso.textContent='Retomando el hilo…';const d=await api('/api/hilos/activar',{id});guardarLocal(d.mensajes);location.reload();}catch(e){aviso.textContent=e.message;}}
async function nuevo(){try{await api('/api/hilos/crear',{});guardarLocal([]);location.reload();}catch(e){aviso.textContent=e.message;}}
function renombrar(li,h){const entrada=el('input');entrada.type='text';entrada.value=h.titulo;entrada.maxLength=120;entrada.setAttribute('aria-label','Nuevo título');const ok=boton('Guardar',async()=>{try{await api('/api/hilos/renombrar',{id:h.id,titulo:entrada.value.trim()});await cargar();}catch(e){aviso.textContent=e.message;}},'primary');const no=boton('Cancelar',pintar);li.replaceChildren(entrada,ok,no);entrada.focus();entrada.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();ok.click();}if(e.key==='Escape')pintar();};}
function borrar(li,h){const p=el('span',null,'¿Borrar «'+h.titulo+'»? ');const si=boton('Sí, borrar',async()=>{try{await api('/api/hilos/borrar',{id:h.id});if(h.id===activo)guardarLocal([]);await cargar();}catch(e){aviso.textContent=e.message;}});const no=boton('No',pintar);li.replaceChildren(p,si,no);no.focus();}
form.addEventListener('submit',()=>{const texto=area.value.trim();if(texto)pendiente=texto;},true);
window.addEventListener('bee-agent-response',async event=>{const respuesta=typeof event.detail==='string'?event.detail:'';try{if(pendiente){const r=await api('/api/hilos/mensaje',{role:'user',content:pendiente});activo=r.activo;}if(respuesta)await api('/api/hilos/mensaje',{role:'assistant',content:respuesta});pendiente=null;await cargar();}catch(e){pendiente=null;aviso.textContent=e.message;}});
cargar();
})();
