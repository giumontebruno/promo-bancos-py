const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const read=path=>fs.readFileSync(path,'utf8');
test('consumer beta has no operational diagnostics panel or dropdown',()=>{
 const html=read('beta-web/index.html'),app=read('beta-web/app.js');
 assert.doesNotMatch(html,/id="sourceHealth"|Ver bancos pendientes|Estado de las actualizaciones/);
 assert.doesNotMatch(app,/renderPilotSourceHealth|healthResponse|source_status\.json/);
 assert.doesNotMatch(read('beta-web/glass-ui.css'),/\.source-health/);
});
test('operational source evidence stays available outside the consumer UI',()=>{
 const health=JSON.parse(read('public/source_status.json'));assert.ok(Object.keys(health).length);
 for(const entry of Object.values(health))assert.ok(['fetched','failed','partial'].includes(entry.status));
 assert.ok(read('scripts/publication-snapshot.mjs').includes('source_status.json'));
});
test('per-promotion uncertainty and financial safeguards are not hidden with diagnostics',()=>{
 const app=read('beta-web/app.js');assert.ok(app.includes('renderSupermarketAssessment(promo)'));assert.ok(app.includes('Tope pendiente de aclaración del banco'));assert.ok(app.includes('No es un reintegro confirmado.'));assert.ok(app.includes('Revisá')||app.includes('Falta confirmar'));
});
test('changed beta assets bypass prior release caches without altering the main app',()=>{
 const html=read('beta-web/index.html');for(const file of ['beta-bundle.js','supermarket-eligibility.js','glass-ui.css'])assert.ok(html.includes(`${file}?v=readable-status-20261030`));assert.ok(html.includes('app.js?v=financial-safety-20261030'));
 assert.doesNotMatch(read('app-web/index.html'),/readable-status-20261030/);
});
