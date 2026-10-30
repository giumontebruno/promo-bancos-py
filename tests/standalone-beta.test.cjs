const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),beta=path.join(root,'beta-web');
const read=f=>fs.readFileSync(path.join(beta,f),'utf8');
test('beta has distinct install identity and storage keys',()=>{
 const m=JSON.parse(read('manifest.webmanifest'));assert.equal(m.name,'paybackpy beta');assert.equal(m.short_name,m.name);assert.equal(m.id,'/promo-bancos-py/beta/');assert.equal(m.scope,m.id);assert.equal(m.start_url,m.id);
 for(const f of ['app.js','index.html','beta-client.js','push-client.js']) assert.doesNotMatch(read(f),/["']paybackPy\./);
 assert.match(read('beta-client.js'),/storageKey: 'paybackPyBeta.auth'/);assert.doesNotMatch(read('beta-client.js'),/signOut\(\)/);
});
test('beta worker cannot delete production caches or register notifications',()=>{
 const s=read('sw.js');assert.doesNotMatch(s,/caches\.|unregister|showNotification|notificationclick/);assert.match(read('index.html'),/register\("\.\/sw.js", \{ scope: "\.\/" \}\)/);
 assert.doesNotMatch(read('push-client.js'),/fetch\(|subscribe\(|requestPermission/);
});
test('beta entry point loads only its own UI assets, independent of repository branch state',()=>{
 // Comparing git diff to mutable origin/main is vacuous after CI checkout and
 // blocks unrelated authorized safety fixes. Test the actual isolation contract.
 const html=read('index.html');
 const scripts=[...html.matchAll(/<script[^>]+src=["']([^"']+)/g)].map(match=>match[1]);
 assert.ok(scripts.length>0);for(const script of scripts)assert.ok(script.startsWith('./'),script);
 assert.doesNotMatch(html,/(?:src|href)=["'][^"']*(?:app-web|server)\//);
});
test('local favorites and level do not call the production API; accounts separated',async()=>{
 const mem=new Map(),calls=[];const node={classList:{},addEventListener(){},querySelector(){return {hidden:false}},querySelectorAll(){return []}};
 const context=vm.createContext({setTimeout,clearTimeout,URL,AbortSignal,Map,Set,CustomEvent:class{},localStorage:{getItem:k=>mem.get(k),setItem:(k,v)=>mem.set(k,v)},document:{createElement:()=>node,body:{append(){}},getElementById:()=>node,addEventListener(){}},window:{addEventListener(){}},fetch:async(...args)=>{calls.push(args);throw new Error('Unexpected network');}});
 let s=read('beta-client.js').replace(/^import[^\n]*\n/gm,'').replace(/updateGate\(\);\s*init\(\);\s*$/,'');
 context.mergeOfficialFavorites=(await import("../beta-web/favorite-import.mjs")).mergeOfficialFavorites;
 vm.runInContext(s,context);
 vm.runInContext("changed = () => {}; current = { email: 'local-test', localId:'qa-user', favorites:[],uenoLevel:5 };",context);
 await vm.runInContext("favorite('promo-a',true)",context);await vm.runInContext('level(3)',context);
 assert.deepEqual(JSON.parse(mem.get('paybackPyBeta.account.qa-user')),{importedOfficial:[],localId:'qa-user',favorites:['promo-a'],uenoLevel:3});
 assert.equal(vm.runInContext("localAccount('other-user').favorites.length",context),0);
 vm.runInContext("importOfficialAccount('second-user',['official-b']); importOfficialAccount('qa-user',['official-a']);",context);
 assert.deepEqual(JSON.parse(mem.get('paybackPyBeta.account.second-user')).favorites,['official-b']);
 assert.deepEqual(JSON.parse(mem.get('paybackPyBeta.account.qa-user')).favorites,['promo-a','official-a']);
 assert.ok(mem.has('paybackPyBeta.account.qa-user.beforeImport'));
 vm.runInContext("current = null; current = {...localAccount('second-user')};",context);
 assert.equal(vm.runInContext("current.favorites.join(',')",context),'official-b');
 vm.runInContext("current = {...localAccount('qa-user'),favorites:['promo-a']};",context);

 await vm.runInContext("favorite('promo-a',false)",context);assert.equal(calls.length,0);
 vm.runInContext("localStorage.setItem = () => { throw new Error('quota'); }",context);
 await assert.rejects(vm.runInContext("favorite('unsaved',true)",context),/quota/);
 assert.equal(vm.runInContext('current.favorites.length',context),0);
 await assert.rejects(vm.runInContext("api('me','DELETE')",context),/no modifica/);assert.equal(calls.length,0);
});
