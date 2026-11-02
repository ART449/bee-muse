/* Chingaquedito: libreta local. Solo pinta lo que la persona escribió; nunca
   interpreta estados ni manda recordatorios por su cuenta. Editar y borrar
   siempre los pide la persona: nada se borra sin confirmación explícita. */
const $ = (id) => document.getElementById(id);
let token = null;
let busy = false;
let ultimos = null;

const GRUPOS = [
  { estado: 'activo', titulo: 'Ahora', vacio: 'No hay ningún frente activo. También está bien.' },
  { estado: 'aparcado', titulo: 'En pausa', vacio: 'Nada aparcado. Aparcar no es abandonar.' },
  { estado: 'terminado', titulo: 'Terminados', vacio: 'Todavía no has cerrado ninguno.' }
];

function setStatus(text) {
  $('status').textContent = text;
}

async function session() {
  if (!token) {
    const response = await fetch('/api/session');
    const data = await response.json();
    token = data.token;
  }
  return token;
}

async function send(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  if (body) headers['X-Library-Token'] = await session();
  const response = await fetch(path, body
    ? { method: 'POST', headers, body: JSON.stringify(body) }
    : { headers: {} });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'No se pudo completar. Intenta otra vez.');
  return data;
}

function texto(tag, value, className) {
  const node = document.createElement(tag);
  node.textContent = value;
  if (className) node.className = className;
  return node;
}

function boton(etiqueta, accion, primario) {
  const node = document.createElement('button');
  node.type = 'button';
  node.textContent = etiqueta;
  if (primario) node.className = 'primary';
  node.addEventListener('click', accion);
  return node;
}

function confirmarBorradoFrente(frente) {
  return window.confirm(
    '¿Borrar el frente «' + frente.titulo + '»?\n\n' +
    'Se quita de tu libreta. Las ideas que lo mencionan se conservan, solo quedan sin frente. ' +
    'Esto no se puede deshacer.'
  );
}

function confirmarBorradoIdea(idea) {
  const resumen = idea.texto.length > 140 ? idea.texto.slice(0, 140) + '…' : idea.texto;
  return window.confirm(
    '¿Borrar esta idea?\n\n' + resumen + '\n\nEsto no se puede deshacer. Tus frentes no se tocan.'
  );
}

function editor(frente) {
  const form = document.createElement('form');
  form.className = 'editor';
  form.noValidate = false;
  const campos = [
    { key: 'titulo', etiqueta: 'Título', tag: 'input', max: 140, obligatorio: true },
    { key: 'objetivo', etiqueta: 'Objetivo', tag: 'textarea', max: 1200 },
    { key: 'siguiente', etiqueta: 'Siguiente paso', tag: 'textarea', max: 700 }
  ];
  const entradas = {};
  campos.forEach((campo) => {
    const id = 'editar-' + frente.id + '-' + campo.key;
    const label = document.createElement('label');
    label.htmlFor = id;
    label.textContent = campo.etiqueta;
    const entrada = document.createElement(campo.tag);
    entrada.id = id;
    entrada.name = campo.key;
    entrada.maxLength = campo.max;
    entrada.value = frente[campo.key] || '';
    if (campo.obligatorio) entrada.required = true;
    entradas[campo.key] = entrada;
    form.append(label, entrada);
  });

  const acciones = document.createElement('div');
  acciones.className = 'actions';
  const guardar = document.createElement('button');
  guardar.type = 'submit';
  guardar.className = 'primary';
  guardar.textContent = 'Guardar cambios';
  const cancelar = boton('Cancelar', () => { if (ultimos) pintar(ultimos); });
  acciones.append(guardar, cancelar);
  form.append(acciones);

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    actuar(() => send('/api/chingaquedito/editar', {
      id: frente.id,
      titulo: entradas.titulo.value,
      objetivo: entradas.objetivo.value,
      siguiente: entradas.siguiente.value
    }));
  });
  return form;
}

function tarjeta(frente) {
  const card = document.createElement('article');
  card.className = 'card';
  card.dataset.id = frente.id;

  const top = document.createElement('div');
  top.className = 'card-top';
  top.append(texto('h3', frente.titulo));
  const etiqueta = { activo: 'Activo', aparcado: 'Aparcado', terminado: 'Terminado' }[frente.estado] || frente.estado;
  top.append(texto('span', etiqueta, 'badge'));
  card.append(top);

  if (frente.objetivo) {
    const bloque = document.createElement('div');
    bloque.className = 'next';
    bloque.append(texto('strong', 'Objetivo'), texto('p', frente.objetivo));
    card.append(bloque);
  }
  if (frente.siguiente) {
    const bloque = document.createElement('div');
    bloque.className = 'next';
    bloque.append(texto('strong', 'Siguiente paso'), texto('p', frente.siguiente));
    card.append(bloque);
  }
  if (!frente.objetivo && !frente.siguiente) {
    card.append(texto('p', 'Puedes completar el objetivo y el siguiente paso con Editar.', 'small'));
  }

  const acciones = document.createElement('div');
  acciones.className = 'actions';
  const mover = async (estado) => {
    await actuar(() => send('/api/chingaquedito/estado', { id: frente.id, estado }));
  };
  if (frente.estado !== 'activo') acciones.append(boton('Volver aquí', () => actuar(() => send('/api/chingaquedito/volver', { id: frente.id })), true));
  if (frente.estado !== 'aparcado') acciones.append(boton('Aparcar', () => mover('aparcado')));
  if (frente.estado !== 'terminado') acciones.append(boton('Terminar', () => mover('terminado')));
  if (frente.estado === 'terminado') acciones.append(boton('Reabrir', () => mover('activo')));
  acciones.append(boton('Editar', () => {
    if (card.querySelector('.editor')) return;
    card.append(editor(frente));
  }));
  acciones.append(boton('Borrar', () => {
    if (!confirmarBorradoFrente(frente)) return;
    actuar(() => send('/api/chingaquedito/borrar-frente', { id: frente.id, confirmar: true }));
  }));
  card.append(acciones);
  return card;
}

function pintarFrentes(datos) {
  const contenedor = $('frentes');
  contenedor.textContent = '';
  const frentes = Array.isArray(datos.frentes) ? datos.frentes : [];
  GRUPOS.forEach((grupo) => {
    const delGrupo = frentes.filter((f) => f.estado === grupo.estado);
    const bloque = document.createElement('section');
    bloque.append(texto('h3', grupo.titulo + ' (' + delGrupo.length + ')'));
    if (!delGrupo.length) {
      bloque.append(texto('p', grupo.vacio, 'empty small'));
    } else {
      delGrupo.forEach((frente) => bloque.append(tarjeta(frente)));
    }
    contenedor.append(bloque);
  });

  const total = frentes.length;
  $('resumen').textContent = total
    ? total + (total === 1 ? ' frente guardado' : ' frentes guardados') + ': ' +
      GRUPOS.map((g) => datos.counts[g.estado] + ' ' + g.titulo.toLowerCase()).join(' · ')
    : 'Todavía no hay frentes guardados.';

  const select = $('ideaFrente');
  const elegido = select.value;
  select.textContent = '';
  const ninguno = document.createElement('option');
  ninguno.value = '';
  ninguno.textContent = 'Sin frente (solo la idea)';
  select.append(ninguno);
  frentes.forEach((frente) => {
    const opcion = document.createElement('option');
    opcion.value = frente.id;
    opcion.textContent = frente.titulo + ' · ' + frente.estado;
    select.append(opcion);
  });
  if (frentes.some((f) => f.id === elegido)) select.value = elegido;
}

function pintarIdeas(datos) {
  const contenedor = $('ideas');
  contenedor.textContent = '';
  const ideas = Array.isArray(datos.ideas) ? datos.ideas : [];
  if (!ideas.length) {
    contenedor.append(texto('p', 'Aquí aparecerán las ideas que guardes. Sin ordenar y sin deberes.', 'empty small'));
    return;
  }
  const frentes = new Map((datos.frentes || []).map((f) => [f.id, f]));
  ideas.forEach((idea) => {
    const fila = document.createElement('article');
    fila.className = 'idea';
    fila.append(texto('p', idea.texto));
    const frente = idea.frente ? frentes.get(idea.frente) : null;
    fila.append(texto('span', frente ? 'Vino mientras estabas en «' + frente.titulo + '»' : 'Idea suelta, sin frente', 'small'));
    const acciones = document.createElement('div');
    acciones.className = 'actions';
    if (frente) {
      acciones.append(boton('Volver a ese frente', () => actuar(() => send('/api/chingaquedito/volver', { id: frente.id }))));
    }
    acciones.append(boton('Borrar idea', () => {
      if (!confirmarBorradoIdea(idea)) return;
      actuar(() => send('/api/chingaquedito/borrar-idea', { id: idea.id, confirmar: true }));
    }));
    fila.append(acciones);
    contenedor.append(fila);
  });
}

function pintar(datos) {
  ultimos = datos;
  const roto = Boolean(datos.error);
  $('problema').hidden = !roto;
  if (roto) {
    $('problemaTexto').textContent = datos.error;
    $('activacion').hidden = true;
    $('libreta').hidden = true;
    setStatus('Tu libreta no se pudo leer completa. No se borró nada.');
    return;
  }
  const activo = datos.activo === true;
  $('activacion').hidden = activo;
  $('libreta').hidden = !activo;
  if (activo) {
    pintarFrentes(datos);
    pintarIdeas(datos);
  }
  if (!activo) setStatus(datos.configurado
    ? 'Chingaquedito está en pausa. Nada nuevo se guarda hasta que lo reactives.'
    : 'Chingaquedito aún no está activado. Nada se ha guardado.');
}

async function actuar(accion) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('#libreta button, #activar').forEach((b) => { b.disabled = true; });
  try {
    const datos = await accion();
    if (datos && datos.cambio) setStatus(datos.cambio);
    if (datos) pintar(datos);
  } catch (error) {
    setStatus(error.message || 'No se pudo completar. Intenta otra vez.');
  } finally {
    busy = false;
    document.querySelectorAll('#libreta button, #activar').forEach((b) => { b.disabled = false; });
  }
}

$('activar').addEventListener('click', () => actuar(() => send('/api/chingaquedito/activar', { activo: true })));
$('pausar').addEventListener('click', () => actuar(() => send('/api/chingaquedito/activar', { activo: false })));

$('formFrente').addEventListener('submit', (event) => {
  event.preventDefault();
  const cuerpo = {
    titulo: $('titulo').value,
    objetivo: $('objetivo').value,
    siguiente: $('siguiente').value,
    estado: $('estadoNuevo').value
  };
  actuar(async () => {
    const datos = await send('/api/chingaquedito/frente', cuerpo);
    $('formFrente').reset();
    return datos;
  });
});

$('formIdea').addEventListener('submit', (event) => {
  event.preventDefault();
  const cuerpo = { texto: $('texto').value, frente: $('ideaFrente').value || null };
  actuar(async () => {
    const datos = await send('/api/chingaquedito/idea', cuerpo);
    $('texto').value = '';
    return datos;
  });
});

send('/api/chingaquedito').then(pintar).catch(() => {
  setStatus('No se pudo leer tu libreta local. Revisa que el servicio de Bee-Muse siga abierto.');
});
