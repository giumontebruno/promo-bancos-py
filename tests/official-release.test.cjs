const {test}=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
const read=(path)=>fs.readFileSync(path,'utf8');
const app=()=>read('app-web/index.html');
const manifest=(target)=>JSON.parse(read(`${target}/manifest.webmanifest`));
const official='https://giumontebruno.github.io/promo-bancos-py/app-web/';

test('official uses beta artwork but retains existing manifest identity and guest entry and Google sign-in',()=>{
 const m=manifest('app-web');
 assert.equal(m.start_url,'./index.html');assert.equal(m.scope,'./');assert.equal(m.id,undefined);
 assert.deepEqual(m.icons,manifest('beta-web').icons);
 for(const icon of m.icons) assert.ok(fs.existsSync('app-web/'+icon.src.split('?')[0]));
 assert.match(app(),/class="auth-required"/);assert.ok(app().indexOf('data-auth-guest>Entrar como invitado') < app().indexOf('data-auth-login disabled'));assert.match(app(),/data-auth-guest>Entrar como invitado/);assert.doesNotMatch(app(),/Explorá sin registro|paybackPyBeta/);
 assert.equal(m.background_color,'#0e1512');assert.equal(m.theme_color,m.background_color);assert.ok(m.icons.every(icon=>icon.src.includes('?v=20261126-dark')));
 assert.match(app(),/wordmark-light\.svg\?v=20261126-dark/);
 assert.match(read('app-web/beta-client.js'),/flowType: 'pkce'/);
 assert.match(read('app-web/beta-client.js'),/await api\('favorite', selected \? 'PUT' : 'DELETE'/);
});
test('old root routes share and notification links to official without forwarding arbitrary auth parameters',()=>{
 const source=read('scripts/build.mjs').split("await writeFile('dist/client/index.html',")[1].match(/<script>([\s\S]+?)<\/script>/)[1];
 let redirect;const location={href:official.replace('app-web/','')+'?promo=abc&view=favorites&variant=card&code=secret#token',replace:x=>redirect=x};
 vm.runInNewContext(source,{URL,location});
 assert.equal(redirect,official+'?view=favorites&promo=abc&variant=card');
});
test('OAuth callback preserves its code and restores only fresh official deep-link fields',()=>{
 const source=[...app().matchAll(/<script>([\s\S]+?)<\/script>/g)].map(x=>x[1]).find(x=>x.includes('paybackPy.oauthReturn'));
 let changed,removed=false;
 const c={URL,URLSearchParams,Date:{now:()=>1000000},location:{href:official+'?code=fixture'},history:{replaceState:(...a)=>changed=String(a[2])},sessionStorage:{getItem:()=>JSON.stringify({at:999000,query:'promo=abc&code=bad&view=favorites&variant=card'}),removeItem:()=>removed=true}};
 vm.runInNewContext(source,c);assert.equal(changed,official+'?code=fixture&view=favorites&promo=abc&variant=card');assert.equal(removed,true);
 changed=undefined;c.sessionStorage.getItem=()=>JSON.stringify({at:0,query:'promo=stale'});vm.runInNewContext(source,c);assert.equal(changed,undefined);
});
test('official worker replaces old scope without clearing caches; push retains the official favorites route',()=>{
 const source=read('app-web/sw.js');
 assert.doesNotMatch(source,/caches\.(delete|keys)|unregister/);
 assert.match(source,/self\.skipWaiting\(\)/);assert.match(source,/self\.clients\.claim\(\)/);
 assert.match(source,/new URL\('\.\/\?view=favorites', self.registration.scope\)/);
 assert.match(source,/assets\/logos\/pase\/icon-192.png/);
});

test('official and beta keep dark mode from launch through the app',()=>{
 for(const folder of ['app-web','beta-web']){
  const html=read(folder+'/index.html'), m=manifest(folder);
  assert.match(html,/<html lang="es" data-theme="dark">/);
  assert.match(html,/name="color-scheme" content="dark"/);
  assert.match(html,new RegExp('name="theme-color" content="'+m.background_color+'"'));
  assert.equal(m.background_color,'#0e1512'); assert.equal(m.theme_color,m.background_color);
  assert.doesNotMatch(html+read(folder+'/app.js'),/themeToggle|localStorage\.getItem\('paybackPy(?:Beta)?\.theme'/);
  assert.match(read(folder+'/payback-launch.css'),/--launch-cta:#54e5a3/);
 }
 assert.match(read('scripts/build.mjs'),/html\{background:#0e1512;color-scheme:dark\}/);
});
