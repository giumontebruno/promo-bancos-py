const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{execFileSync}=require('node:child_process');
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
test('production application and backend sources are untouched',()=>{
 const changed=execFileSync('git',['diff','--name-only','origin/main','--','app-web','server','public','data','drizzle'],{cwd:root,encoding:'utf8'}).trim();assert.equal(changed,'');
});
test('local favorites and level do not call the production API; accounts separated',async()=>{
 const mem=new Map(),calls=[];const node={classList:{},addEventListener(){},querySelector(){return {hidden:false}},querySelectorAll(){return []}};
 const context=vm.createContext({setTimeout,clearTimeout,URL,AbortSignal,Map,Set,CustomEvent:class{},localStorage:{getItem:k=>mem.get(k),setItem:(k,v)=>mem.set(k,v)},document:{createElement:()=>node,body:{append(){}},getElementById:()=>node,addEventListener(){}},window:{addEventListener(){}},fetch:async(...args)=>{calls.push(args);throw new Error('Unexpected network');}});
 let s=read('beta-client.js').replace(/^import[^\n]*\n/,'').replace(/updateGate\(\);\s*init\(\);\s*$/,'');
 vm.runInContext(s,context);
 vm.runInContext("changed = () => {}; current = { email: 'local-test', localId:'qa-user', favorites:[],uenoLevel:5 };",context);
 await vm.runInContext("favorite('promo-a',true)",context);await vm.runInContext('level(3)',context);
 assert.deepEqual(JSON.parse(mem.get('paybackPyBeta.account.qa-user')),{favorites:['promo-a'],uenoLevel:3});
 assert.equal(vm.runInContext("localAccount('other-user').favorites.length",context),0);
 await vm.runInContext("favorite('promo-a',false)",context);assert.equal(calls.length,0);
 vm.runInContext("localStorage.setItem = () => { throw new Error('quota'); }",context);
 await assert.rejects(vm.runInContext("favorite('unsaved',true)",context),/quota/);
 assert.equal(vm.runInContext('current.favorites.length',context),0);
 await assert.rejects(vm.runInContext("api('me','DELETE')",context),/no modifica/);assert.equal(calls.length,0);
});
