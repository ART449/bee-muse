/* Superexportaciones: vista previa por defecto; copiar solo con confirmación; retirar
   originales solo con frase exacta, recibo verificado y riesgos rojos aceptados uno por
   uno. Todo lo que se pinta viene del servidor; esta página no decide nada sola. */
const $ = (id) => document.getElementById(id);
let token = null;
let vista = null;          // última vista previa
let operacion = null;      // última operación preparada / copiada
let seleccion = new Set();
let sondeo = null;

function setStatus(text) { $('status').textContent = text; }

async function session() {
  if (!token) {
    const r = await fetch('/api/session');
    token = (await r.json()).token;
  }
  return token;
}

async function send(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  if (body) headers['X-Library-Token'] = await session();
  const r = await fetch(path, body ? { method: 'POST', headers, body: JSON.stringify(body) } : { headers: {} });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || 'No se pudo completar. Intenta otra vez.');
  return data;
}

function bytes(n) {
  if (!n) return '0 B';
  const u = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0; let v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return (i ? v.toFixed(v >= 100 ? 0 : 1) : v) + ' ' + u[i];
}

function el(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined && text !== null) n.textContent = text;
  if (cls) n.className = cls;
  return n;
}

async function actuar(fn, boton) {
  if (boton) boton.disabled = true;
  try { await fn(); }
  catch (e) { setStatus('⚠ ' + e.message); }
  finally { if (boton) boton.disabled = false; }
}

/* ---------------------------------------------------------------- 1. vista previa */

function pintarTotales(resumen) {
  const t = $('totales');
  t.replaceChildren();
  const r = resumen.recuperable;
  const pc = resumen.porColor;
  const items = [
    ['Verde · regenerable', bytes(r.seguro), pc.verde.grupos + ' grupos · ' + pc.verde.archivos + ' archivos', 'verde'],
    ['Amarillo · copiar y retirar', bytes(r.conCopia), pc.amarillo.grupos + ' grupos', 'amarillo'],
    ['Rojo · revisar dependencia', bytes(r.conRevision), pc.rojo.grupos + ' grupos', 'rojo'],
    ['Total candidato', bytes(r.total), 'suma de los tres colores', ''],
  ];
  items.forEach(([titulo, valor, pie, cls]) => {
    const m = el('div', null, 'metric ' + cls);
    const s = el('span'); s.append(el('span', null, 'sem'), document.createTextNode(titulo));
    m.append(s, el('strong', valor), el('span', pie));
    t.append(m);
  });
}

function actualizarSeleccion() {
  let total = 0;
  vista.grupos.forEach((g) => { if (seleccion.has(g.id)) total += g.bytes; });
  $('seleccionTexto').textContent = seleccion.size + ' grupos · ' + bytes(total);
  $('destinoPanel').hidden = seleccion.size === 0;
}

function fila(g) {
  const tr = el('tr', null, g.color);
  tr.dataset.id = g.id;
  const tdSel = el('td');
  const cb = document.createElement('input');
  cb.type = 'checkbox'; cb.style.width = 'auto'; cb.style.margin = '0';
  cb.disabled = !g.exportable;
  cb.checked = seleccion.has(g.id);
  cb.setAttribute('aria-label', 'Seleccionar ' + g.nombre);
  cb.addEventListener('change', () => { if (cb.checked) seleccion.add(g.id); else seleccion.delete(g.id); actualizarSeleccion(); });
  tdSel.append(cb);
  const tdColor = el('td'); tdColor.append(el('span', null, 'sem'), document.createTextNode(g.color));
  const tdQue = el('td');
  tdQue.append(el('div', g.nombre), el('span', g.categoria + (g.regenerar ? ' · ' + g.regenerar : ''), 'badge'));
  if (g.parcial) tdQue.append(el('div', 'recorrido parcial', 'small'));
  const tdRuta = el('td', g.path, 'ruta');
  const tdRiesgos = el('td');
  if (g.riesgos && g.riesgos.length) {
    const ul = el('ul', null, 'riesgos');
    g.riesgos.forEach((r) => ul.append(el('li', r.tipo + ': ' + r.detalle)));
    tdRiesgos.append(ul);
  } else tdRiesgos.append(el('span', '—', 'small'));
  tr.append(tdSel, tdColor, tdQue, tdRuta, tdRiesgos, el('td', g.archivos, 'num'), el('td', bytes(g.bytes), 'num'));
  return tr;
}

function pintarVista(v) {
  vista = v;
  seleccion = new Set();
  operacion = null;
  $('preparado').hidden = true;
  $('retiroPanel').hidden = true;
  $('resultado').hidden = false;
  pintarTotales(v.resumen);
  $('resumenTexto').textContent = v.grupos.length + ' grupos en ' + v.origenes.join(' · ') +
    (v.parcial ? ' · RECORRIDO PARCIAL (tiempo o cantidad): los totales son cota inferior.' : '') +
    ' · ' + v.limites;
  const tbody = $('filas');
  tbody.replaceChildren();
  v.grupos.forEach((g) => tbody.append(fila(g)));
  actualizarSeleccion();
  setStatus('Vista previa lista. Nada se copió ni movió. Selecciona grupos y elige destino. La vista vence en ' + Math.round(v.expiraEn / 60) + ' min.');
}

$('formPrevia').addEventListener('submit', (ev) => {
  ev.preventDefault();
  const origenes = $('origenes').value.split('\n').map((s) => s.trim()).filter(Boolean);
  const minMB = Number($('minMB').value || 0);
  actuar(async () => {
    setStatus('Recorriendo… sin tocar nada.');
    pintarVista(await send('/api/superexports/previsualizar', {
      origenes, minBytes: Math.max(0, Math.round(minMB * 1024 * 1024)), incluirOcultos: $('ocultos').value === 'si'
    }));
  }, $('btnPrevia'));
});

function seleccionar(colores, acumular) {
  if (!vista) return;
  if (!acumular) seleccion = new Set();
  vista.grupos.forEach((g) => { if (g.exportable && colores.includes(g.color)) seleccion.add(g.id); });
  document.querySelectorAll('#filas input[type=checkbox]').forEach((cb) => { cb.checked = seleccion.has(cb.closest('tr').dataset.id); });
  actualizarSeleccion();
}
$('selVerde').addEventListener('click', () => seleccionar(['verde'], false));
$('selAmarillo').addEventListener('click', () => seleccionar(['amarillo'], true));
$('selNada').addEventListener('click', () => seleccionar([], false));

/* ---------------------------------------------------------------- 2. preparar */

$('btnPreparar').addEventListener('click', () => actuar(async () => {
  if (!vista || !seleccion.size) throw new Error('Selecciona al menos un grupo.');
  const r = await send('/api/superexports/preparar', { plan: vista.id, destino: $('destino').value.trim(), seleccion: [...seleccion] });
  operacion = r;
  $('preparado').hidden = false;
  $('retiroPanel').hidden = true;
  $('barra').style.width = '0%';
  $('progresoTexto').textContent = '';
  $('btnCopiar').disabled = false;
  $('preparadoTexto').textContent = 'Preparado: ' + r.totalArchivos + ' archivos · ' + bytes(r.bytes) + ' → ' + r.destino +
    ' · libre en destino ' + bytes(r.espacioLibreDestino) + '. ' + r.nota;
  setStatus('Operación preparada. Todavía no se copió nada.');
}, $('btnPreparar')));

/* ---------------------------------------------------------------- 3. copiar + sondeo */

function pintarProgreso(est) {
  const pct = est.bytes ? Math.round(100 * est.progreso.bytes / est.bytes) : 0;
  $('barra').style.width = pct + '%';
  $('progresoTexto').textContent = est.estado + ' · ' + est.progreso.archivos + '/' + est.totalArchivos + ' archivos · ' +
    bytes(est.progreso.bytes) + ' de ' + bytes(est.bytes) + (est.progreso.fallidos ? ' · ' + est.progreso.fallidos + ' fallidos' : '') +
    (est.error ? ' · ' + est.error : '');
}

function terminoCopia(est) {
  clearInterval(sondeo); sondeo = null;
  $('btnCancelar').hidden = true;
  operacion = est;
  pintarProgreso(est);
  cargarRecibos();
  if (est.estado === 'copiado' && est.verificado) {
    setStatus('Copia terminada y verificada por SHA-256. Originales intactos. Recibo: ' + est.recibo + '\nPuedes retirar originales abajo, o dejarlos.');
    prepararRetiro(est);
  } else {
    setStatus('La copia terminó en estado «' + est.estado + '». ' + (est.error || '') + ' Los originales no se tocaron; no se habilita el retiro.');
  }
}

$('btnCopiar').addEventListener('click', () => actuar(async () => {
  if (!operacion) throw new Error('Primero prepara la copia.');
  if (!window.confirm('¿Copiar ' + operacion.totalArchivos + ' archivos (' + bytes(operacion.bytes) + ') a\n' + operacion.destino + '?\n\nLos originales NO se tocan en este paso.')) return;
  const r = await send('/api/superexports/copiar', { operacion: operacion.operacion, confirmarCopia: true });
  $('btnCopiar').disabled = true;
  $('btnCancelar').hidden = false;
  setStatus('Copiando y calculando SHA-256…');
  pintarProgreso(r);
  sondeo = setInterval(async () => {
    try {
      const est = await send('/api/superexports/estado?id=' + encodeURIComponent(operacion.operacion));
      pintarProgreso(est);
      if (est.estado !== 'copiando') terminoCopia(est);
    } catch (e) { clearInterval(sondeo); sondeo = null; setStatus('⚠ ' + e.message); }
  }, 1000);
}, $('btnCopiar')));

$('btnCancelar').addEventListener('click', () => actuar(async () => {
  await send('/api/superexports/cancelar', { operacion: operacion.operacion });
  setStatus('Cancelación pedida. Termina el archivo en curso y se detiene; lo copiado se conserva.');
}, $('btnCancelar')));

/* ---------------------------------------------------------------- 4. retirar (candado) */

function prepararRetiro(est) {
  $('retiroPanel').hidden = false;
  $('frase').value = '';
  $('confirmar').checked = false;
  $('retiroTexto').textContent = '';
  const rojos = est.grupos.filter((g) => g.color === 'rojo');
  $('rojosAviso').hidden = rojos.length === 0;
  const ul = $('rojosLista');
  ul.replaceChildren();
  rojos.forEach((g) => {
    const li = el('li');
    const lab = el('label');
    const cb = document.createElement('input');
    cb.type = 'checkbox'; cb.style.width = 'auto'; cb.style.marginRight = '8px'; cb.dataset.id = g.id; cb.className = 'rojoAceptar';
    cb.addEventListener('change', validarRetiro);
    lab.append(cb, document.createTextNode(g.nombre + ' — ' + g.path));
    li.append(lab);
    const r = el('ul', null, 'riesgos');
    g.riesgos.forEach((x) => r.append(el('li', x.tipo + ': ' + x.detalle)));
    li.append(r);
    ul.append(li);
  });
  validarRetiro();
}

function fraseEsperada() { return $('modo').value === 'borrar' ? 'BORRAR ORIGINALES' : 'RETIRAR ORIGINALES'; }

function validarRetiro() {
  $('fraseEsperada').textContent = fraseEsperada();
  const rojosOk = [...document.querySelectorAll('.rojoAceptar')].every((cb) => cb.checked);
  const ok = operacion && operacion.estado === 'copiado' && operacion.verificado &&
    $('frase').value === fraseEsperada() && $('confirmar').checked && rojosOk;
  $('btnRetirar').disabled = !ok;
}
$('modo').addEventListener('change', validarRetiro);
$('frase').addEventListener('input', validarRetiro);
$('confirmar').addEventListener('change', validarRetiro);

$('btnRetirar').addEventListener('click', () => actuar(async () => {
  const modo = $('modo').value;
  const msg = modo === 'borrar'
    ? 'Vas a BORRAR los originales de ' + operacion.totalArchivos + ' archivos (' + bytes(operacion.bytes) + ').\nNo es reversible. Antes se reverifica cada copia.\n\n¿Continuar?'
    : 'Vas a mover los originales a una carpeta de cuarentena en el mismo disco (reversible; no libera espacio aún).\nAntes se reverifica cada copia.\n\n¿Continuar?';
  if (!window.confirm(msg)) return;
  const aceptados = [...document.querySelectorAll('.rojoAceptar:checked')].map((cb) => cb.dataset.id);
  const r = await send('/api/superexports/retirar', { operacion: operacion.operacion, modo, frase: $('frase').value, confirmar: true, aceptarRiesgos: aceptados });
  operacion = r;
  $('btnRetirar').disabled = true;
  $('retiroTexto').textContent = r.retiro.estado + ' · ' + r.retiro.archivos + ' archivos · ' + r.nota + ' Recibo: ' + r.recibo;
  setStatus('Retiro ' + r.retiro.estado + '. ' + r.nota);
  cargarRecibos();
}, $('btnRetirar')));

/* ---------------------------------------------------------------- recibos */

async function cargarRecibos() {
  try {
    const s = await send('/api/superexports');
    const ul = $('recibos');
    ul.replaceChildren();
    if (!s.recibos.length) { ul.append(el('li', 'Sin recibos todavía.', 'small')); return; }
    s.recibos.forEach((r) => {
      const li = el('li');
      const retiro = r.retiro ? ' · retiro: ' + r.retiro.modo + ' (' + r.retiro.estado + ')' : ' · originales intactos';
      li.append(el('div', (r.actualizado || r.creado || '') + ' · ' + r.estado + (r.verificado ? ' · verificado' : '') + retiro));
      li.append(el('div', (r.origenes || []).join(', ') + ' → ' + (r.destino || '') + ' · ' + bytes(r.bytes || 0), 'ruta small'));
      const a = el('a', 'ver recibo ' + r.id, 'small');
      a.href = '/api/superexports/recibo?id=' + encodeURIComponent(r.id);
      a.target = '_blank';
      li.append(a);
      ul.append(li);
    });
  } catch (e) { setStatus('⚠ ' + e.message); }
}

cargarRecibos();
