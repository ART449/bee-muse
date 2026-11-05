/* Guía de primer uso de Bee-Muse. Capa aparte: cursor dibujado en el DOM que nace donde está el mouse real,
   tres pasos (continuar → voz → apuntadora), espera el clic real de la persona y se detiene con Esc,
   con "Saltar guía" o si la persona mueve su mouse mientras el cursor viaja. Nunca mueve el mouse del sistema
   ni hace clics por la persona. Blancos: [data-tour="continuar|voz|apuntadora"]; si uno falta, se salta. */
(()=>{'use strict';
const CLAVE='bee-guia-vista';
const reducido=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
const almacen={
  get(){try{const s=window.BeeDesktop&&window.BeeDesktop.storage;const v=s?s.getItem(CLAVE):null;if(v!=null)return v;}catch{}try{return localStorage.getItem(CLAVE);}catch{return null;}},
  set(v){try{const s=window.BeeDesktop&&window.BeeDesktop.storage;if(s)s.setItem(CLAVE,v);}catch{}try{localStorage.setItem(CLAVE,v);}catch{}}
};
const PASOS=[
  {blanco:'continuar',texto:'Aquí retomas tu hilo: Bee-Muse te dice en qué ibas y qué quedó pendiente. Ahora tú, dale a Continuar.'},
  {blanco:'voz',texto:'Para pedir por voz: pulsa, habla y suelta; el texto queda listo en el cuadro. Ahora tú, dale aquí.',respaldo:()=>Array.from(document.querySelectorAll('button')).find(b=>/Dictar/.test(b.textContent||''))||null},
  {blanco:'apuntadora',texto:'Pide un HTML y la Apuntadora lo señala sin sacarte de la conversación. Ahora tú, dale aquí.',respaldo:()=>document.querySelector('a[href*="/html?locate="],a[href*="/html?point="]')}
];
let ultimo=null,activa=false,estado='',hechos=0,cursor=null,tarjeta=null,blancoActual=null,escuchaClic=null,focoPrevio=null,temporizador=0,origenViaje=null;
document.addEventListener('mousemove',e=>{ultimo={x:e.clientX,y:e.clientY};if(activa&&estado==='viajando'&&origenViaje&&Math.hypot(e.clientX-origenViaje.x,e.clientY-origenViaje.y)>24)detener('mouse');},{passive:true});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&activa){e.preventDefault();detener('esc');}});
function el(tag,clase,texto){const n=document.createElement(tag);if(clase)n.className=clase;if(texto!=null)n.textContent=texto;return n;}
function boton(texto,clase,fn){const b=el('button','guia-btn'+(clase?' '+clase:''),texto);b.type='button';b.addEventListener('click',fn);return b;}
const LECTURA_MS=2500;let mostradoEn=0;
function aviso(texto,ms){const a=el('div','guia-aviso',texto);a.setAttribute('role','status');document.body.appendChild(a);setTimeout(()=>a.remove(),ms||1800);}
function buscar(paso){let n=document.querySelector('[data-tour="'+paso.blanco+'"]');if(!n&&paso.respaldo)n=paso.respaldo();return n&&n.offsetParent!==null?n:null;}
function pedirPermiso(){
  if(document.querySelector('.guia-permiso'))return;
  focoPrevio=document.activeElement;
  const fondo=el('div','guia-permiso');const caja=el('div','guia-caja');caja.setAttribute('role','dialog');caja.setAttribute('aria-modal','true');caja.setAttribute('aria-labelledby','guiaTitulo');
  const h=el('h2',null,'¿Te muestro Bee-Muse en un minuto?');h.id='guiaTitulo';caja.appendChild(h);
  ['Soy Muse, una inteligencia artificial creada por Meta. No me inventó este equipo: ellos me dieron manos dentro de Bee-Muse para ayudarte.',
   'Si aceptas, un cursor guía recorre esta ventana y te muestra cómo retomar tu hilo, pedir por voz y señalar un archivo. No mueve el mouse de tu equipo ni hace clics por ti en cosas delicadas.',
   'Mueve tu mouse o pulsa Esc en cualquier momento y la guía se detiene al instante.'].forEach(t=>caja.appendChild(el('p',null,t)));
  caja.appendChild(el('p','guia-firma','«Yo no inventé a Muse. Lo que hice fue darle unas buenas manos.» — ArT, IArtLabs'));
  const fila=el('div','guia-botones');
  const no=boton('Ahora no',null,()=>{almacen.set('1');cerrarPermiso();});
  const si=boton('Sí, muéstrame','guia-primario',()=>{almacen.set('1');cerrarPermiso();iniciar();});
  fila.appendChild(no);fila.appendChild(si);caja.appendChild(fila);fondo.appendChild(caja);document.body.appendChild(fondo);si.focus();
  fondo.addEventListener('keydown',e=>{if(e.key==='Escape'){e.stopPropagation();almacen.set('1');cerrarPermiso();}});
  function cerrarPermiso(){fondo.remove();if(focoPrevio&&focoPrevio.focus)try{focoPrevio.focus();}catch{}}
}
function iniciar(){
  if(activa)return;activa=true;focoPrevio=document.activeElement;
  hechos=0;cursor=el('div','guia-cursor');cursor.setAttribute('aria-hidden','true');
  const inicio=ultimo||{x:innerWidth/2,y:innerHeight/2};
  cursor.style.transform='translate('+inicio.x+'px,'+inicio.y+'px)';document.body.appendChild(cursor);
  tarjeta=el('div','guia-tarjeta');tarjeta.setAttribute('role','dialog');tarjeta.setAttribute('aria-live','polite');document.body.appendChild(tarjeta);
  addEventListener('resize',reubicar);addEventListener('scroll',reubicar,true);
  paso(0);
}
function paso(i){
  limpiarBlanco();
  while(i<PASOS.length&&!buscar(PASOS[i]))i++;
  if(i>=PASOS.length){return terminar();}
  const p=PASOS[i],n=buscar(p);blancoActual=n;n.classList.add('guia-blanco');
  tarjeta.replaceChildren();tarjeta.appendChild(el('div','guia-paso','Paso '+(i+1)+' de '+PASOS.length));tarjeta.appendChild(el('p',null,p.texto));
  const fila=el('div','guia-botones');fila.appendChild(boton('Saltar guía',null,()=>detener('saltar')));fila.appendChild(boton('Siguiente','guia-primario',()=>{hechos++;paso(i+1);}));tarjeta.appendChild(fila);
  mostradoEn=Date.now();escuchaClic=()=>{if(Date.now()-mostradoEn<LECTURA_MS)return;hechos++;paso(i+1);};n.addEventListener('click',escuchaClic);
  n.scrollIntoView({block:'center',behavior:reducido()?'auto':'smooth'});
  estado='viajando';origenViaje=ultimo?{x:ultimo.x,y:ultimo.y}:null;
  clearTimeout(temporizador);
  setTimeout(()=>{if(!activa||blancoActual!==n)return;colocar(n);temporizador=setTimeout(()=>{if(activa&&blancoActual===n){estado='esperando';tarjeta.querySelector('.guia-primario').focus();}},reducido()?0:1600);},reducido()?0:350);
}
function colocar(n){
  const r=n.getBoundingClientRect();const x=r.left+r.width*0.5,y=r.top+r.height*0.6;
  cursor.style.transform='translate('+x+'px,'+y+'px)';
  const t=tarjeta.getBoundingClientRect();let top=r.bottom+14,left=Math.min(Math.max(16,r.left),innerWidth-t.width-16);
  if(top+t.height>innerHeight-16)top=Math.max(16,r.top-t.height-14);
  tarjeta.style.left=left+'px';tarjeta.style.top=top+'px';
}
function reubicar(){if(activa&&blancoActual)colocar(blancoActual);}
function limpiarBlanco(){if(blancoActual){blancoActual.classList.remove('guia-blanco');if(escuchaClic)blancoActual.removeEventListener('click',escuchaClic);}blancoActual=null;escuchaClic=null;}
function terminar(){
  limpiarBlanco();estado='fin';if(cursor)cursor.remove();cursor=null;
  tarjeta.replaceChildren();tarjeta.appendChild(el('div','guia-paso','Listo'));tarjeta.appendChild(el('p',null,hechos>=PASOS.length?'Ya hiciste las tres acciones. Puedes repetir la guía desde el menú Ayuda cuando quieras.':hechos>0?'Recorrido terminado: esta pantalla tenía '+hechos+' de '+PASOS.length+' pasos. Puedes repetir la guía desde el menú Ayuda.':'Esta pantalla aún no tiene los pasos de la guía. Ábrela desde Muse e inténtalo de nuevo.'));
  const fila=el('div','guia-botones');fila.appendChild(boton('Cerrar','guia-primario',()=>detener('fin')));tarjeta.appendChild(fila);
  const t=tarjeta.getBoundingClientRect();tarjeta.style.left=Math.max(16,(innerWidth-t.width)/2)+'px';tarjeta.style.top=Math.max(16,innerHeight-t.height-32)+'px';
  tarjeta.querySelector('.guia-primario').focus();clearTimeout(temporizador);temporizador=setTimeout(()=>detener('fin'),15000);
}
function detener(motivo){
  if(!activa)return;activa=false;estado='';clearTimeout(temporizador);limpiarBlanco();
  removeEventListener('resize',reubicar);removeEventListener('scroll',reubicar,true);
  if(cursor)cursor.remove();if(tarjeta)tarjeta.remove();cursor=tarjeta=null;
  if(motivo!=='fin')aviso('Guía detenida. Puedes repetirla desde el menú Ayuda.');
  if(focoPrevio&&focoPrevio.focus)try{focoPrevio.focus();}catch{}
}
window.BeeGuia={iniciar,detener,pedirPermiso};
const forzada=new URLSearchParams(location.search).get('guia')==='1';
if(forzada||almacen.get()!=='1')setTimeout(pedirPermiso,forzada?250:900);
})();
