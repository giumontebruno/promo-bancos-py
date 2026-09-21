import { createClient } from '@supabase/supabase-js';

const $ = id => document.getElementById(id);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let client, service;
async function load() {
  $('refresh').disabled = true;
  $('content').hidden = true;
  $('signin').hidden = true;
  $('status').textContent = 'Verificando acceso...';
  try {
    if (!client) {
      const config = await fetch('./notifications-config.json', {cache:'no-store'}).then(r => r.json());
      service = new URL(config.serviceUrl).origin;
      const auth = await fetch(service + '/api/beta/config').then(r => r.json());
      if (!auth.enabled) throw new Error('Servicio no disponible.');
      client = createClient(auth.url, auth.key, {auth:{flowType:'pkce'}});
    }
    const {data:{session}} = await client.auth.getSession();
    if (!session) { $('signin').hidden = false; throw new Error('Inicia sesion para continuar.'); }
    const response = await fetch(service + '/api/beta/admin', {
      headers:{Authorization:'Bearer ' + session.access_token}, cache:'no-store', signal:AbortSignal.timeout(15000),
    });
    if (response.status === 403) throw new Error('Esta cuenta no tiene permisos de administracion.');
    if (!response.ok) throw new Error('No pudimos verificar el acceso. Vuelve a ingresar e intenta nuevamente.');
    const data = await response.json();
    const people = new Map();
    for (const row of data.participants) {
      const p = people.get(row.email) || {email:row.email,created:row.created_at,consent:row.consent,last:'',counts:{}};
      p.last = [p.last,row.day || ''].sort().at(-1);
      if (row.kind) p.counts[row.kind] = (p.counts[row.kind] || 0) + row.count;
      people.set(row.email,p);
    }
    $('peopleRows').innerHTML = [...people.values()].map(p => `<tr><td>${escape(p.email)}${p.consent ? '' : '<br><small>Sin seguimiento</small>'}</td><td>${escape(p.created?.slice(0,10))}</td><td>${escape(p.last || '-')}</td>${['session','search','promo_open'].map(k=>`<td>${p.consent ? p.counts[k] || 0 : '-'}</td>`).join('')}</tr>`).join('');
    $('reportRows').innerHTML = data.reports.map(r => `<article><strong>${escape(r.email)}</strong><p>${escape(r.message)}</p><small>${escape(r.kind)} | ${escape(r.created_at)}${r.promo_id ? ' | ' + escape(r.promo_id) : ''}</small></article>`).join('') || '<p>No hay comentarios.</p>';
    $('deliveryRows').innerHTML = (data.deliveries || []).map(r => `<tr><td>${escape(r.created_at)}</td><td>${escape(r.status)}</td></tr>`).join('') || '<tr><td colspan="2">Sin envios registrados.</td></tr>';
    $('content').hidden = false;
    $('errorRows').innerHTML = (data.errors || []).map(r=>`<tr><td>${escape(r.created_at)}</td><td>${escape(r.area)}</td><td>${escape(r.code)}</td></tr>`).join('') || '<tr><td colspan="3">Sin errores registrados.</td></tr>';
    $('status').textContent = `Acceso privado: ${session.user.email}`;
  } catch(error) { $('status').textContent = error.message; }
  finally { $('refresh').disabled = false; }
}
$('refresh').addEventListener('click',load);
document.querySelector('nav').addEventListener('click', e => {
  const button = e.target.closest('[data-tab]');
  if (!button) return;
  for (const tab of document.querySelectorAll('[data-tab]')) {
    const selected = tab === button;
    tab.setAttribute('aria-selected',String(selected));
    $(tab.dataset.tab).hidden = !selected;
  }
});
load();
