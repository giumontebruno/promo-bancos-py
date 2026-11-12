const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
test('official candidate keeps auth, PWA identity, beta favorites and rollback, without enabling release',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'payback-candidate-'));
 try {
  const retained=['beta-bundle.js','beta-client.js','admin.html','admin-client.js','admin-bundle.js','manifest.webmanifest','config.js','notifications-config.json','privacy.html','terms.html','push-client.js'];
  await fs.mkdir(path.join(root,'app-web'));await fs.mkdir(path.join(root,'beta'));
  for(const f of retained){await fs.writeFile(path.join(root,'app-web',f),'official:'+f);await fs.writeFile(path.join(root,'beta',f),'isolated:'+f);}
  await fs.writeFile(path.join(root,'app-web','index.html'),'old official');
  await fs.writeFile(path.join(root,'app-web','app.js'),'function renderFavoriteAlerts(){return "official alerts";}\nfunction syncFavoriteAlerts(){}');
  await fs.writeFile(path.join(root,'app-web','sw.js'),"self.addEventListener('push',()=>{});");
  await fs.writeFile(path.join(root,'beta','index.html'),'paybackpy beta paybackPyBeta.theme');
  await fs.writeFile(path.join(root,'beta','app.js'),'const key="paybackPyBeta.favorites"; function renderFavoriteAlerts(){} function syncFavoriteAlerts(){}');
  const {prepareOfficialCandidate}=await import('../scripts/prepare-official-candidate.mjs');await prepareOfficialCandidate(root);
  for(const f of retained)assert.equal(await fs.readFile(path.join(root,'app-web',f),'utf8'),'official:'+f);
  assert.match(await fs.readFile(path.join(root,'app-web','app.js'),'utf8'),/paybackPy\.favorites/);
  assert.match(await fs.readFile(path.join(root,'beta','app.js'),'utf8'),/paybackPyBeta\.favorites/);
  assert.equal(await fs.readFile(path.join(root,'official-rollback','index.html'),'utf8'),'old official');
  assert.doesNotMatch(await fs.readFile(path.join(root,'app-web','sw.js'),'utf8'),/caches.delete|localStorage|unregister/);
  assert.doesNotMatch(await fs.readFile('scripts/build.mjs','utf8'),/prepareOfficialCandidate/);
 }finally{await fs.rm(root,{recursive:true,force:true});}
});
