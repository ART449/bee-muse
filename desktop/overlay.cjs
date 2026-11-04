'use strict';
const fs = require('node:fs');
const path = require('node:path');

const COLLAPSED = {width: 180, height: 198};
const EXPANDED = {width: 460, height: 700};

function finite(value, fallback) { return Number.isFinite(value) ? Math.round(value) : fallback; }
function fitBounds(bounds, displays) {
  const areas = displays.map(display => display.workArea).filter(area => area && area.width > 0 && area.height > 0);
  if (!areas.length) throw Error('No hay una pantalla disponible para el chat flotante.');
  const x = finite(bounds?.x, areas[0].x + areas[0].width - COLLAPSED.width - 24);
  const y = finite(bounds?.y, areas[0].y + areas[0].height - COLLAPSED.height - 24);
  const width = Math.max(1, finite(bounds?.width, COLLAPSED.width));
  const height = Math.max(1, finite(bounds?.height, COLLAPSED.height));
  const overlap = area => Math.max(0, Math.min(x + width, area.x + area.width) - Math.max(x, area.x)) * Math.max(0, Math.min(y + height, area.y + area.height) - Math.max(y, area.y));
  const area = areas.reduce((best, current) => overlap(current) > overlap(best) ? current : best, areas[0]);
  const w = Math.min(width, area.width), h = Math.min(height, area.height);
  return {x: Math.min(Math.max(x, area.x), area.x + area.width - w),
    y: Math.min(Math.max(y, area.y), area.y + area.height - h), width: w, height: h};
}

function createOverlay({app, BrowserWindow, screen, origin, preload, safeWindow}) {
  const file = path.join(app.getPath('userData'), 'overlay-window.json');
  let saved = {};
  try { saved = JSON.parse(fs.readFileSync(file, 'utf8')); } catch {}
  let expanded = saved.expanded === true, visible = saved.visible !== false;
  let expandedSize = {width: Math.max(340, finite(saved.expandedSize?.width, EXPANDED.width)), height: Math.max(420, finite(saved.expandedSize?.height, EXPANDED.height))};
  let saveTimer, disposing = false;
  const size = expanded ? expandedSize : COLLAPSED;
  const initial = fitBounds({...saved.bounds, ...size}, screen.getAllDisplays());
  const window = new BrowserWindow({...initial, title: 'Bee-Muse · Chat flotante',
    frame: false, transparent: true, backgroundColor: '#00000000', hasShadow: expanded,
    show: false, alwaysOnTop: true, skipTaskbar: true, resizable: expanded,
    minimizable: false, maximizable: false, fullscreenable: false,
    webPreferences: {preload, nodeIntegration: false, contextIsolation: true, sandbox: true,
      webSecurity: true, partition: 'persist:bee-muse-desktop'}});
  window.setMenuBarVisibility(false);
  safeWindow(window);
  const state = () => ({expanded, visible: visible && window.isVisible()});
  const notify = () => { if (!window.isDestroyed()) window.webContents.send('bee-overlay-state', state()); };
  const save = () => {
    if (window.isDestroyed()) return;
    const body = {version: 1, bounds: window.getBounds(), expanded, expandedSize, visible};
    try { fs.writeFileSync(file + '.tmp', JSON.stringify(body)); fs.renameSync(file + '.tmp', file); } catch {}
  };
  const saveSoon = () => { clearTimeout(saveTimer); saveTimer = setTimeout(save, 250); };
  function setExpanded(value) {
    if (typeof value !== 'boolean') throw Error('Estado del chat flotante no válido.');
    if (window.isDestroyed()) return;
    const bounds = window.getBounds();
    if (expanded) expandedSize = {width: bounds.width, height: bounds.height};
    expanded = value;
    const nextSize = expanded ? expandedSize : COLLAPSED;
    const next = fitBounds({x: bounds.x + bounds.width - nextSize.width, y: bounds.y + bounds.height - nextSize.height, ...nextSize}, screen.getAllDisplays());
    window.setMinimumSize(1, 1);
    window.setResizable(expanded);
    window.setBounds(next);
    if (expanded) window.setMinimumSize(Math.min(340, next.width), Math.min(420, next.height));
    saveSoon(); notify();
  }
  function show() { if (!window.isDestroyed()) { visible = true; window.show(); window.focus(); saveSoon(); notify(); } }
  function hide() { if (!window.isDestroyed()) { visible = false; window.hide(); saveSoon(); notify(); } }
  function recoverDisplay() {
    if (!window.isDestroyed()) { window.setBounds(fitBounds(window.getBounds(), screen.getAllDisplays())); saveSoon(); }
  }
  window.on('move', saveSoon);
  window.on('resize', saveSoon);
  window.on('close', event => { if (!disposing) { event.preventDefault(); hide(); } });
  window.webContents.on('did-finish-load', notify);
  window.once('ready-to-show', () => { if (visible) window.showInactive(); notify(); });
  screen.on('display-removed', recoverDisplay);
  screen.on('display-metrics-changed', recoverDisplay);
  window.on('closed', () => {
    clearTimeout(saveTimer);
    screen.removeListener('display-removed', recoverDisplay);
    screen.removeListener('display-metrics-changed', recoverDisplay);
  });
  const loaded = window.loadURL(origin + '/muse?overlay=1').catch(error => {
    disposing = true;
    if (!window.isDestroyed()) window.destroy();
    throw error;
  });
  return {window, loaded, state, setExpanded, show, hide,
    dispose() { clearTimeout(saveTimer); save(); disposing = true; if (!window.isDestroyed()) window.destroy(); }};
}

module.exports = {COLLAPSED, EXPANDED, fitBounds, createOverlay};
