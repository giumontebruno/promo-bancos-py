import { mergeOfficialFavorites } from './favorite-import.mjs';
import { createClient } from '@supabase/supabase-js';

let client, service, current = null, ready = false, initError = '', busy = false;
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const dialog = document.createElement('dialog');
dialog.className = 'beta-dialog';
document.body.append(dialog);
const authGate = document.getElementById('authGate');
const authStatus = document.getElementById('authStatus');
let gateMessage = '', authPhase = 'checking', authAttempt = 0;
clearTimeout(window.paybackAuthWatchdog);
function deadline(promise, ms = 12000) {
  let timer;
  return Promise.race([promise, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('La comprobación tardó demasiado. Reintentá para continuar.')), ms); })]).finally(() => clearTimeout(timer));
}
function updateGate() {
  const locked = !current || authPhase === 'checking';
  document.body.classList.toggle('auth-required', locked);
  authGate.hidden = !locked;
  document.querySelector('.app-shell').inert = locked;
  document.getElementById('bottomNav').inert = locked;
  if (!locked) return;
  const phase = authPhase === 'authenticated' ? 'anonymous' : authPhase;
  authGate.dataset.state = phase;
  authGate.setAttribute('aria-busy', String(phase === 'checking' || busy));
  authStatus.textContent = initError || (phase === 'checking' ? 'Comprobando tu sesión…' : busy ? 'Abriendo Google…' : gateMessage);
  authGate.querySelectorAll('[data-auth-login]').forEach(button => { button.disabled = !client || busy || phase !== 'anonymous'; });
  authGate.querySelector('[data-auth-retry]').hidden = phase !== 'error';

}
function message(text) { const node = dialog.querySelector('[role=status]'); if (node) node.textContent = text; }
async function accessToken() {
  if (!client) return null;
  const result = await deadline(client.auth.getSession());
  if (result.error) throw result.error;
  return result.data.session?.access_token || null;
}
async function api(path, method = 'GET', body) {
  if (method !== 'GET' || path !== 'me') throw new Error('Esta beta no modifica datos del servicio principal.');
  const token = await accessToken();
  if (!token) throw new Error('Ingresá con Google.');
  const response = await fetch(service + '/api/beta/' + path, {
    method, headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000),
  });
  const data = await response.json();
  if (!response.ok) { const error = new Error(data.error || 'No pudimos guardar los cambios.'); error.status = response.status; throw error; }
  return data;
}
function changed() { updateGate(); window.dispatchEvent(new CustomEvent('beta-account', { detail: current })); }
async function refresh(isCurrent = () => true) {
  const attempt = authAttempt;
  const before = await deadline(client.auth.getSession());
  if (before.error) throw before.error;
  const account = await api('me');
  const { data, error } = await deadline(client.auth.getSession());
  if (error) throw error;
  if (!isCurrent() || attempt !== authAttempt) return;
  if (before.data.session?.user?.id !== data.session?.user?.id) return;
  if (data.session && String(account.email).toLowerCase() !== String(data.session.user.email).toLowerCase()) throw new Error('La cuenta cambió. Reintentá el acceso.');
  if (!data.session) { current = null; authPhase = 'anonymous'; changed(); return; }
  const metadata = data.session?.user?.user_metadata || {};
  let avatarUrl = '';
  try {
    const avatar = new URL(metadata.avatar_url || metadata.picture || '');
    if (avatar.protocol === 'https:' && (avatar.hostname === 'googleusercontent.com' || avatar.hostname.endsWith('.googleusercontent.com'))) avatarUrl = avatar.href;
  } catch { /* An account without a Google photo uses the profile fallback. */ }
  current = { ...account, ...importOfficialAccount(data.session.user.id, account.favorites), admin: false, consent: false, givenName: String(metadata.given_name || '').trim(), name: String(metadata.full_name || metadata.name || '').trim(), avatarUrl };
  changed();
}

function importOfficialAccount(id, favorites) {
  const local=localAccount(id), merged=mergeOfficialFavorites(local, favorites);
  const key='paybackPyBeta.account.'+id;
  if(!localStorage.getItem(key+'.beforeImport')) localStorage.setItem(key+'.beforeImport', JSON.stringify(local));
  localStorage.setItem(key,JSON.stringify(merged));
  return merged;
}
function localAccount(id) {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem('paybackPyBeta.account.' + id)) || {}; } catch {}
  return { importedOfficial: Array.isArray(saved.importedOfficial) ? saved.importedOfficial : [], localId: id, favorites: Array.isArray(saved.favorites) ? saved.favorites.filter(x => typeof x === 'string') : [], uenoLevel: Math.max(1, Math.min(5, Number(saved.uenoLevel) || 5)) };
}
function saveLocalAccount(favorites, uenoLevel) {
  if (!current) throw new Error('Ingresá con Google.');
  localStorage.setItem('paybackPyBeta.account.' + current.localId, JSON.stringify({ ...localAccount(current.localId), favorites, uenoLevel }));
  current = { ...current, favorites, uenoLevel }; changed();
}

function googleButton() {
  return '<img src="./assets/logos/google-g-official.png" width="20" height="20" alt="">Continuar con Google';
}
async function login() {
  if (!client) throw new Error('El acceso no está disponible en este momento.');
  const { error } = await client.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: new URL('./', location.href).href, scopes: 'openid email profile', queryParams: { prompt: 'select_account' } } });
  if (error) throw new Error('No pudimos iniciar el acceso con Google. Intentá nuevamente.');
}
function shell(content) {
  dialog.innerHTML = `<article class="dialog-card"><button type="button" class="close-button" data-beta-close aria-label="Cerrar">×</button>${content}<p role="status" aria-live="polite"></p></article>`;
  if (!dialog.open) dialog.showModal();
}
function show() {
  if (!ready || !client) return shell(`<h2>paybackpy beta</h2><p>${escape(initError || 'Preparando el acceso.')}</p><button data-beta-retry>Reintentar</button>`);
  if (!current) return shell(`<h2>paybackpy beta</h2><form id="betaLogin"><button type="submit" class="google-signin">${googleButton()}</button></form><p>Ingresá con Google. Esta versión usa el mismo acceso de Payback y guarda favoritos y nivel por separado en este navegador.</p><a href="./privacy.html">Privacidad</a>`);
  shell(`<span class="filter-label">TU CUENTA</span><h2>Tus preferencias</h2><p>${escape(current.email)}</p><p>Favoritos en esta beta: ${current.favorites.length}. Importamos los guardados de tu cuenta oficial. Los cambios acá quedan en este navegador; no modifican la app oficial.</p><form id="betaPreferences"><label>Nivel UENO<select name="level" aria-label="Nivel UENO">${[1,2,3,4,5].map(n => `<option value="${n}" ${current.uenoLevel === n ? 'selected' : ''}>Nivel ${n}</option>`).join('')}</select></label><button type="submit" class="account-save">Guardar preferencias</button></form><div class="beta-actions"><button class="account-danger" data-beta-logout>Cerrar sesión de esta beta</button></div>`);
}
function report() {
  shell('<h2>Comentarios de esta beta</h2><p>Compartí tus observaciones en la conversación donde recibiste el enlace. Esta prueba no envía reportes al servicio principal.</p>');
}

const lastEvent = new Map();
async function event() { /* No production analytics from this isolated preview. */ }
async function favorite(promoId, selected, relatedIds = []) {
  if (!current) throw new Error('Ingresá con Google.');
  const ids = new Set([promoId, ...relatedIds]);
  const remaining = current.favorites.filter(id => !ids.has(id));
  saveLocalAccount(selected ? [...remaining, promoId] : remaining, current.uenoLevel);
}
async function level(value) {
  saveLocalAccount(current.favorites, Math.max(1, Math.min(5, Number(value) || 5)));
}

dialog.addEventListener('submit', async e => {
  e.preventDefault(); if (busy) return; busy = true;
  const form = e.target, data = new FormData(form), submit = form.querySelector('button[type=submit],button:not([type])');
  submit.disabled = true; message('Guardando…');
  try {
    if (form.id === 'betaLogin') {
      await login();
      message('Abriendo Google…');
    } else if (form.id === 'betaPreferences') {
      await level(Number(data.get('level'))); show(); message('Preferencias guardadas.');

    }
  } catch (error) { message(error.message); }
  finally { busy = false; submit.disabled = false; }
});
dialog.addEventListener('click', async e => {
  const target = e.target.closest('button'); if (!target) return;
  try {
    if (target.hasAttribute('data-beta-close')) dialog.close();
    if (target.hasAttribute('data-beta-home')) show();
    if (target.hasAttribute('data-beta-report')) report();
    if (target.hasAttribute('data-beta-retry')) { await init(); show(); }
    if (target.hasAttribute('data-beta-logout')) {
      if (window.PaybackPush?.enabled()) await window.PaybackPush.disable();
      const { error } = await deadline(client.auth.signOut({ scope: 'local' })); if (error) throw error;
      ++authAttempt; current = null; authPhase = 'anonymous'; initError = ''; lastEvent.clear(); changed(); show();
    }

  } catch (error) { message(error.message); }
});
authGate.addEventListener('click', async e => {
  if (e.target.closest('[data-auth-retry]')) { await init(); return; }
  const button = e.target.closest('[data-auth-login]');
  if (!button || busy || authPhase !== 'anonymous') return;
  busy = true;
  gateMessage = 'Abriendo Google…';
  updateGate();
  try { await deadline(login()); }
  catch (error) { gateMessage = error.message; }
  finally { busy = false; updateGate(); }
});
document.addEventListener('click', async e => {
  const logoutButton = e.target.closest('[data-profile-logout]');
  if (logoutButton) {
    if (busy) return;
    busy = true; logoutButton.disabled = true;
    const status = document.querySelector('.profile-session-status');
    if (status) status.textContent = 'Cerrando sesión…';
    try {
      if (window.PaybackPush?.enabled()) await window.PaybackPush.disable();
      const { error } = await deadline(client.auth.signOut({ scope: 'local' }));
      if (error) throw error;
      ++authAttempt; current = null; authPhase = 'anonymous'; initError = ''; lastEvent.clear(); changed();
    } catch {
      if (status) status.textContent = 'No pudimos cerrar la sesión. Intentá nuevamente.';
    } finally { busy = false; logoutButton.disabled = false; }
    return;
  }
  const loginButton = e.target.closest('[data-beta-login]');
  if (loginButton) {
    if (busy) return;
    busy = true; loginButton.disabled = true;
    try { await login(); } catch (error) { show(); message(error.message); }
    finally { busy = false; loginButton.disabled = false; }
    return;
  }
  const button = e.target.closest('[data-beta-open], [data-beta-report-id]');
  if (button?.hasAttribute('data-beta-open')) show();
  if (button?.hasAttribute('data-beta-report-id')) report(button.dataset.betaReportId);
  if (e.target.closest('[data-bank],[data-category],[data-day]')) event('filter');
  if (e.target.closest('[data-view="nearby"]')) event('map_open');
  if (e.target.closest('.place-maps-link')) event('directions');
});
let searchTimer;
document.getElementById('searchInput')?.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => event('search'), 1500); });
async function init() {
  const attempt = ++authAttempt;
  const active = () => attempt === authAttempt;
  authPhase = 'checking'; ready = false; initError = ''; gateMessage = '';
  updateGate();
  try {
    await deadline((async () => {
      const configResponse = await fetch('./notifications-config.json', { cache: 'no-store', signal: AbortSignal.timeout(10000) });
      if (!configResponse.ok) throw new Error('No pudimos preparar el acceso. Reintentá.');
      const config = await configResponse.json();
      if (!active()) return;
      service = new URL(config.serviceUrl).origin;
      if (!service.startsWith('https://')) throw new Error('Servicio no disponible');
      const response = await fetch(service + '/api/beta/config', { signal: AbortSignal.timeout(10000) });
      if (!response.ok) throw new Error('El acceso no está disponible en este momento. Reintentá.');
      const auth = await response.json();
      if (!active()) return;
      if (!auth.enabled) throw new Error('El acceso no está disponible en este momento.');
      if (!client) {
        client = createClient(auth.url, auth.key, { auth: { flowType: 'pkce', storageKey: 'paybackPyBeta.auth' } });
        client.auth.onAuthStateChange((eventName) => {
          if (eventName === 'SIGNED_OUT') {
            ++authAttempt; current = null; authPhase = 'anonymous'; ready = true; initError = ''; gateMessage = ''; lastEvent.clear(); changed();
          } else if (eventName !== 'INITIAL_SESSION') {
            setTimeout(() => { if (authPhase !== 'checking') init(); }, 0);
          }
        });
      }
      const token = await accessToken();
      if (!active()) return;
      // Only the authenticated backend response unlocks the app, never storage alone.
      if (token) await refresh(active);
      else current = null;
      if (!active()) return;
      authPhase = current ? 'authenticated' : 'anonymous'; ready = true; changed();
      if (current) event('session');
    })());
  } catch (error) {
    if (!active()) return;
    ++authAttempt; current = null; ready = true;
    if (error.status === 401) {
      authPhase = 'anonymous'; initError = ''; gateMessage = 'Tu sesión venció. Ingresá nuevamente para continuar.';
    } else {
      authPhase = 'error';
      initError = !navigator.onLine ? 'Estás sin conexión. Conectate y reintentá para comprobar tu sesión.'
        : error instanceof TypeError || error.name === 'TimeoutError' ? 'No pudimos conectar con el acceso. Revisá tu conexión y reintentá.' : error.message;
    }
    changed();
  }
}
window.addEventListener('pageshow', e => { if (e.persisted) init(); });
window.addEventListener('offline', () => { if (!current && authPhase !== 'checking') { authPhase = 'error'; initError = 'Estás sin conexión. Conectate y reintentá.'; updateGate(); } });

window.PaybackBeta = { accessToken, favorite, level, event, get current() { return current; } };
updateGate();
init();

