// Optional release staging only. Never invoked by the normal Pages build.
// Keeps the installed app identity and official account implementation intact.
import {cp,readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
export async function prepareOfficialCandidate(root='dist/client') {
 const official=path.join(root,'app-web'), beta=path.join(root,'beta');
 const retain=['beta-bundle.js','beta-client.js','admin.html','admin-client.js','admin-bundle.js','manifest.webmanifest','config.js','notifications-config.json','privacy.html','terms.html','push-client.js'];
 const originalApp=await readFile(path.join(official,'app.js'),'utf8');
 const originalSw=await readFile(path.join(official,'sw.js'),'utf8');
 const alerts=originalApp.slice(originalApp.indexOf('function renderFavoriteAlerts()'),originalApp.indexOf('function syncFavoriteAlerts()'));
 const push=originalSw.slice(originalSw.indexOf("self.addEventListener('push'"));
 if(!alerts.startsWith('function renderFavoriteAlerts()') || !push.startsWith("self.addEventListener('push'")) throw new Error('Official notification contract missing');
 const saved = new Map();
 for (const file of retain) saved.set(file,await readFile(path.join(official,file)));
 const backup=path.join(root,'official-rollback');
 await mkdir(backup,{recursive:true});await cp(official,backup,{recursive:true});
 await cp(beta,official,{recursive:true});
 for (const [file,bytes] of saved) await writeFile(path.join(official,file),bytes);
 let app=await readFile(path.join(official,'app.js'),'utf8');
 app=app.replaceAll('paybackPyBeta.', 'paybackPy.').replaceAll('https://giumontebruno.github.io/promo-bancos-py/beta/','https://giumontebruno.github.io/promo-bancos-py/app-web/');
 app=app.slice(0,app.indexOf('function renderFavoriteAlerts()'))+alerts+app.slice(app.indexOf('function syncFavoriteAlerts()'));
 app=app.replace('Explorá sin cuenta. Los favoritos de esta beta quedan en este navegador.','Ingresá para consultar los favoritos de tu cuenta.');
 await writeFile(path.join(official,'app.js'),app);
 let html=await readFile(path.join(official,'index.html'),'utf8');
 html=html.replaceAll('paybackpy beta','Payback PY').replaceAll('paybackPyBeta.theme','paybackPy.theme')
 .replace('Los cambios de favoritos de esta beta quedan en este navegador, separados de la app principal.','Tus favoritos de la cuenta se conservan y sincronizan con el servicio oficial.')
 .replace('<button type="button" class="auth-retry" data-auth-guest>Seguir sin iniciar sesión</button>','')
 .replace('Explorá sin registro. Ingresá sólo si querés usar tu cuenta.','Ingresá para consultar tus beneficios y favoritos.')
 .replace('beta-bundle.js?v=readable-status-20261030','beta-bundle.js?v=official-candidate-20261112');
 await writeFile(path.join(official,'index.html'),html);
 // No destructive CacheStorage cleanup. Existing installs keep their URL and identity.
 await writeFile(path.join(official,'sw.js'),`self.addEventListener('install',()=>self.skipWaiting());\nself.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));\nself.addEventListener('fetch',e=>{if(e.request.mode!=='navigate')return;e.respondWith(fetch(e.request).catch(()=>new Response('<html lang="es"><meta name="viewport" content="width=device-width"><h1>Estás sin conexión</h1><p>Conectate para consultar promociones actualizadas. Tus favoritos siguen guardados.</p></html>',{status:503,headers:{'Content-Type':'text/html;charset=utf-8'}})));});\n`+push);
 return {official,backup,beta,accountMode:'official service',localBetaFavorites:'preserved at /beta; not automatically merged',pwaIdentity:'unchanged'};
}
if(process.argv[1] && path.resolve(process.argv[1])===path.resolve(new URL(import.meta.url).pathname)) console.log(JSON.stringify(await prepareOfficialCandidate(process.argv[2]||'dist/client'),null,2));
