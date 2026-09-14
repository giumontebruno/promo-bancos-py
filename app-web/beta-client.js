import { createClient } from '@supabase/supabase-js';

let client, service, current = null, ready = false, initError = '', busy = false;
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const dialog = document.createElement('dialog');
dialog.className = 'beta-dialog';
document.body.append(dialog);
function message(text) { const node = dialog.querySelector('[role=status]'); if (node) node.textContent = text; }
async function accessToken() { return client ? (await client.auth.getSession()).data.session?.access_token : null; }
async function api(path, method = 'GET', body) {
  const token = await accessToken();
  if (!token) throw new Error('Ingresá con tu correo invitado.');
  const response = await fetch(service + '/api/beta/' + path, {
    method, headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'No pudimos guardar los cambios.');
  return data;
}
function changed() { window.dispatchEvent(new CustomEvent('beta-account', { detail: current })); }
async function refresh() {
  const account = await api('me');
  const { data } = await client.auth.getSession();
  const metadata = data.session?.user?.user_metadata || {};
  current = { ...account, name: String(metadata.full_name || metadata.name || '').trim() };
  changed();
}
function googleButton() {
  return '<img src="./assets/logos/google-g-official.png" width="20" height="20" alt="">Continuar con Google';
}
async function login() {
  if (!client) { show(); return; }
  const { error } = await client.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: new URL('./', location.href).href, scopes: 'openid email profile', queryParams: { prompt: 'select_account' } } });
  if (error) throw new Error('No pudimos iniciar el acceso con Google. Intentá nuevamente.');
}
function shell(content) {
  dialog.innerHTML = `<article class="dialog-card"><button type="button" class="close-button" data-beta-close aria-label="Cerrar">×</button>${content}<p role="status" aria-live="polite"></p></article>`;
  if (!dialog.open) dialog.showModal();
}
function show() {
  if (!ready) return shell(`<h2>Beta Payback PY</h2><p>${escape(initError || 'Preparando el acceso…')}</p><button data-beta-retry>Reintentar</button>`);
  if (!client) return shell('<h2>Beta por invitación</h2><p>El registro está en preparación. Tus favoritos locales siguen disponibles.</p>');
  if (!current) return shell(`<h2>Ingresar a la beta</h2><form id="betaLogin"><button type="submit" class="google-signin">${googleButton()}</button></form><p>Usá la cuenta de Google cuyo correo fue invitado. Solo solicitamos identidad básica y correo, sin acceso a Gmail, contactos ni Drive.</p>`);
  shell(`<h2>Tu cuenta beta</h2><p>${escape(current.email)}</p>
    <p>Favoritos sincronizados: ${current.favorites.length}. Los avisos se activan por separado en cada dispositivo.</p>
    <form id="betaPreferences"><label class="check-row"><input name="consent" type="checkbox" ${current.consent ? 'checked' : ''}>Compartir mi actividad de prueba</label>
    <p>El administrador podrá ver tu correo y contadores diarios de sesiones, consultas, filtros, promociones abiertas, favoritos agregados y clics en Maps. No guardamos el texto de las búsquedas ni coordenadas. Los contadores se conservan 30 días; al desactivar esta opción se borran.</p>
    <label>Nivel UENO<select name="level">${[1,2,3,4,5].map(n => `<option value="${n}" ${current.uenoLevel === n ? 'selected' : ''}>Nivel ${n}</option>`).join('')}</select></label><button>Guardar preferencias</button></form>
    <div class="beta-actions"><button data-beta-report>Enviar comentario</button>${current.admin ? '<button data-beta-admin>Panel de pruebas</button>' : ''}<button data-beta-logout>Cerrar sesión</button><button data-beta-erase>Borrar mis datos de beta</button></div>`);
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
async function favorite(promoId, selected) {
  await api('favorite', selected ? 'PUT' : 'DELETE', { promoId });
  await refresh();
  if (selected) event('favorite_add');
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
    if (target.hasAttribute('data-beta-admin')) await admin();
    if (target.hasAttribute('data-beta-retry')) { await init(); show(); }
    if (target.hasAttribute('data-beta-logout')) {
      if (window.PaybackPush?.enabled()) await window.PaybackPush.disable();
      const { error } = await client.auth.signOut(); if (error) throw error;
      current = null; lastEvent.clear(); changed(); show();
    }
    if (target.hasAttribute('data-beta-erase')) {
      if (!confirm('¿Borrar favoritos, reportes, actividad y avisos de tu cuenta beta? Tu acceso por correo se conserva.')) return;
      if (window.PaybackPush?.enabled()) await window.PaybackPush.disable();
      await api('me', 'DELETE'); await client.auth.signOut(); current = null; changed(); show();
    }
  } catch (error) { message(error.message); }
});
document.addEventListener('click', async e => {
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
  try {
    const config = await fetch('./notifications-config.json', { cache: 'no-store' }).then(r => r.json());
    service = new URL(config.serviceUrl).origin;
    if (!service.startsWith('https://')) throw new Error('Servicio no disponible');
    const response = await fetch(service + '/api/beta/config', { signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error('El registro de beta todavía no está habilitado.');
    const auth = await response.json(); ready = true;
    if (!auth.enabled) return;
    if (!client) {
      client = createClient(auth.url, auth.key, { auth: { flowType: 'pkce' } });
      client.auth.onAuthStateChange(() => setTimeout(async () => {
        try {
          if (await accessToken()) { await refresh(); event('session'); }
          else { current = null; changed(); }
          if (dialog.open) show();
        } catch (error) { current = null; changed(); show(); message(error.message); }
      }, 0));
    }
  } catch (error) { initError = error.message; }
}
window.PaybackBeta = { accessToken, favorite, level, event, get current() { return current; } };
init();
