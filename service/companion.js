(() => {
  'use strict';
  const names={idle:'En reposo',waving:'Saludando',waiting:'Escuchando o esperando',running:'Trabajando',review:'Revisando',jumping:'Tarea completada',failed:'La tarea encontró un error','running-left':'Navegando atrás','running-right':'Navegando adelante'};
  const box=document.createElement('aside');box.className='bee-companion';box.setAttribute('aria-label','CyberBee y OctoHype');
  const image=document.createElement('img');image.alt='CyberBee y OctoHype';image.width=112;image.height=112;
  const label=document.createElement('span');label.setAttribute('role','status');
  const button=document.createElement('button');button.type='button';button.textContent='Ocultar animación';button.setAttribute('aria-label','Ocultar animación');
  box.append(image,label,button);document.body.append(box);
  let current='idle',reset=null;
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  function set(state){if(!names[state])return;clearTimeout(reset);current=state;image.src='/mascotas/cyberbee-octohype/'+(reduced.matches?'still.png':state+'.gif');label.textContent=names[state];if(['jumping','failed','waving','running-left','running-right'].includes(state))reset=setTimeout(()=>set('idle'),state==='failed'?8000:3200);}
  window.BeeCompanion={set};window.addEventListener('bee-state',event=>set(event.detail));reduced.addEventListener('change',()=>set(current));
  button.onclick=()=>{box.hidden=true;try{sessionStorage.setItem('bee-companion-hidden','1');}catch{}};
  try{box.hidden=sessionStorage.getItem('bee-companion-hidden')==='1';}catch{}
  let pending=0,sequence=0;const nativeFetch=window.fetch.bind(window);
  window.fetch=async(input,options={})=>{const url=new URL(typeof input==='string'?input:input.url,location.href);const method=(options.method||(typeof input==='object'&&input.method)||'GET').toUpperCase();const active=url.origin===location.origin&&method==='POST'&&url.pathname.startsWith('/api/')&&!url.pathname.startsWith('/api/account/');const ticket=++sequence;if(active){pending++;set(url.pathname.includes('versions')?'review':'running');}try{const result=await nativeFetch(input,options);if(active){if(!result.ok)set('failed');else if(url.pathname!=='/api/muse/start')set('jumping');}return result;}catch(error){if(active)set('failed');throw error;}finally{if(active){pending--;if(pending>0)set('running');}}};
  const chat=document.getElementById('agentChat')||document.getElementById('beeChat');
  if(chat)new MutationObserver(()=>{const busy=document.getElementById('agentSend')?.disabled||document.getElementById('beeSend')?.disabled;if(busy)set('running');}).observe(chat,{childList:true,subtree:true});
  document.addEventListener('focusin',e=>{if(e.target.matches('textarea,input:not([type=hidden])')&&!pending)set('waiting');});
  document.addEventListener('focusout',()=>{if(!pending)set('idle');});
  document.addEventListener('click',e=>{const link=e.target.closest('a[href]');if(link&&new URL(link.href).origin===location.origin)set('running-right');});
  set('waving');
})();
