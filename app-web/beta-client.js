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
  const account = await api('me');
  const { data, error } = await deadline(client.auth.getSession());
  if (error) throw error;
  if (!isCurrent() || attempt !== authAttempt) return;
  if (!data.session) { current = null; authPhase = 'anonymous'; changed(); return; }
  const metadata = data.session?.user?.user_metadata || {};
  let avatarUrl = '';
  try {
    const avatar = new URL(metadata.avatar_url || metadata.picture || '');
    if (avatar.protocol === 'https:' && (avatar.hostname === 'googleusercontent.com' || avatar.hostname.endsWith('.googleusercontent.com'))) avatarUrl = avatar.href;
  } catch { /* An account without a Google photo uses the profile fallback. */ }
  current = { ...account, name: String(metadata.full_name || metadata.name || '').trim(), avatarUrl };
  changed();
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
  if (!ready) return shell(`<h2>Beta Payback PY</h2><p>${escape(initError || 'Preparando el acceso…')}</p><button data-beta-retry>Reintentar</button>`);
  if (!client) return shell('<h2>Beta Payback PY</h2><p>El registro está en preparación. Tus favoritos locales siguen disponibles.</p>');
  if (!current) return shell(`<h2>Ingresar a la beta</h2><form id="betaLogin"><button type="submit" class="google-signin">${googleButton()}</button></form><p>Ingresá con tu cuenta de Google. Solo solicitamos identidad básica y correo, sin acceso a Gmail, contactos ni Drive.</p><p>La beta registra por defecto contadores diarios de uso asociados a tu cuenta. No guarda lo que escribís en búsquedas ni tu ubicación. Podés desactivar esta medición y borrar sus datos en tu cuenta. <a href="./privacy.html">Privacidad</a></p>`);
  shell(`<h2>Tu cuenta beta</h2><p>${escape(current.email)}</p>
    <p>Favoritos sincronizados: ${current.favorites.length}. Los avisos se activan por separado en cada dispositivo.</p>
    <form id="betaPreferences"><label class="check-row"><input name="consent" type="checkbox" ${current.consent ? 'checked' : ''}>Medición básica de la beta</label>
    <p>Activa por defecto en cuentas nuevas. El administrador puede ver tu correo y contadores diarios de sesiones, búsquedas, filtros, promociones abiertas, favoritos agregados y clics en Maps. No guardamos el texto de las búsquedas ni coordenadas. Los contadores se conservan 30 días; si desactivás la medición, se borran.</p>
    <label>Nivel UENO<select name="level">${[1,2,3,4,5].map(n => `<option value="${n}" ${current.uenoLevel === n ? 'selected' : ''}>Nivel ${n}</option>`).join('')}</select></label><button>Guardar preferencias</button></form>
    <div class="beta-actions"><button data-beta-report>Enviar comentario</button><button data-beta-logout>Cerrar sesión</button><button data-beta-erase>Borrar mis datos de beta</button></div>`);
}
function report(promoId = '') {
  if (!current) return show();
  shell(`<h2>Enviar un reporte</h2><form id="betaReport"><input type="hidden" name="promoId" value="${escape(promoId)}"><label>Motivo<select name="kind"><option value="${promoId ? 'incorrect' : 'missing'}">${promoId ? 'Datos incorrectos' : 'Falta una promoción'}</option><option value="suggestion">Sugerencia</option></select></label><label>Comentario<textarea name="message" minlength="10" maxlength="2000" rows="5" required placeholder="Comercio, banco y qué encontraste"></textarea></label><p>El administrador verá tu correo, comentario y la promoción asociada. No incluyas números de tarjeta ni datos personales de otras personas.</p><button>Enviar reporte</button></form>`);
}
async function admin() {
  const data = await api('admin');
  const groups = new Map();
  for (const row of data.participants) {
    const person = groups.get(row.email) || { email: row.email, consent: row.consent, total: 0, last: '', counts: {} };
    person.total += row.count || 0; person.last = [person.last, row.day || ''].sort().at(-1);
    if (row.kind) person.counts[row.kind] = (person.counts[row.kind] || 0) + row.count;
    groups.set(row.email, person);
  }
  shell(`<h2>Pruebas · últimos 30 días</h2><div class="beta-table"><table><thead><tr><th>Participante</th><th>Última actividad UTC</th><th>Sesiones</th><th>Búsquedas</th><th>Promos abiertas</th><th>Maps</th></tr></thead><tbody>${[...groups.values()].sort((a,b) => b.total-a.total).map(p => `<tr><td>${escape(p.email)}${!p.consent ? ' (sin seguimiento)' : ''}</td><td>${escape(p.last || '—')}</td><td>${p.counts.session || 0}</td><td>${p.counts.search || 0}</td><td>${p.counts.promo_open || 0}</td><td>${p.counts.directions || 0}</td></tr>`).join('')}</tbody></table></div><h3>Reportes recientes</h3>${data.reports.map(r => `<div class="beta-report"><strong>${escape(r.email)} · ${escape(r.kind)}</strong><p>${escape(r.message)}</p><small>${escape(r.created_at)}${r.promo_id ? ' · ' + escape(r.promo_id) : ''}</small></div>`).join('') || '<p>No hay reportes.</p>'}<button data-beta-home>Volver</button>`);
}
const lastEvent = new Map();
async function event(kind) {
  if (!current?.consent) return;
  const now = Date.now(), interval = kind === 'session' ? 30 * 60000 : 1500;
  if (now - (lastEvent.get(kind) || 0) < interval) return;
  lastEvent.set(kind, now);
  try { await api('event', 'POST', { kind }); } catch { /* Analytics must never block the app. */ }
}
const favoriteWrites = new Map();
async function favorite(promoId, selected, relatedIds = []) {
  if (!current) throw new Error('Ingresá con Google.');
  const account = current.email;
  const key = `${account}:${promoId}`;
  const equivalent = new Set([promoId, ...relatedIds]);
  const entry = favoriteWrites.get(key) || { promise: Promise.resolve(), confirmedIds: current.favorites.filter(id => equivalent.has(id)), relatedIds: new Set() };
  relatedIds.forEach(id => entry.relatedIds.add(id));
  entry.relatedIds.forEach(id => equivalent.add(id));
  const remaining = current.favorites.filter(id => !equivalent.has(id));
  current.favorites = selected ? [...remaining, promoId] : remaining;
  changed();
  const pending = entry.promise.catch(() => {}).then(async () => {
    if (current?.email !== account) throw new Error('La sesión cambió. Volvé a intentar.');
    await api('favorite', selected ? 'PUT' : 'DELETE', {promoId, relatedIds: [...entry.relatedIds]});
    entry.confirmedIds = selected ? [promoId] : [];
  });
  entry.promise = pending;
  favoriteWrites.set(key, entry);
  try { await pending; if (selected) event('favorite_add'); }
  catch (error) {
    if (current?.email === account && entry.promise === pending) {
      current.favorites = [...current.favorites.filter(id => !equivalent.has(id)), ...entry.confirmedIds];
      changed();
    }
    throw error;
  } finally { if (entry.promise === pending) favoriteWrites.delete(key); }
}
async function level(value) {
  await api('me', 'PUT', { consent: current.consent, uenoLevel: value });
  await refresh();
}
dialog.addEventListener('submit', async e => {
  e.preventDefault(); if (busy) return; busy = true;
  const form = e.target, data = new FormData(form), submit = form.querySelector('button');
  submit.disabled = true; message('Guardando…');
  try {
    if (form.id === 'betaLogin') {
      await login();
      message('Abriendo Google…');
    } else if (form.id === 'betaPreferences') {
      await api('me', 'PUT', { consent: data.has('consent'), uenoLevel: Number(data.get('level')) });
      await refresh(); show(); message('Preferencias guardadas.');
    } else if (form.id === 'betaReport') {
      await api('report', 'POST', Object.fromEntries(data));
      form.reset(); message('Reporte enviado. Gracias por ayudarnos a mejorar.');
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
      const { error } = await deadline(client.auth.signOut()); if (error) throw error;
      ++authAttempt; current = null; authPhase = 'anonymous'; initError = ''; lastEvent.clear(); changed(); show();
    }
    if (target.hasAttribute('data-beta-erase')) {
      if (!confirm('¿Borrar favoritos, reportes, actividad y avisos de tu cuenta beta? Tu acceso por correo se conserva.')) return;
      if (window.PaybackPush?.enabled()) await window.PaybackPush.disable();
      await api('me', 'DELETE'); await deadline(client.auth.signOut()); current = null; changed(); show();
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
      const { error } = await deadline(client.auth.signOut());
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
        client = createClient(auth.url, auth.key, { auth: { flowType: 'pkce' } });
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

