const {test} = require('node:test');
const assert = require('node:assert/strict');
const {DatabaseSync} = require('node:sqlite');
const {readFileSync,readdirSync} = require('node:fs');
const Module = require('node:module');
const esbuild = require('esbuild');
const output=esbuild.buildSync({entryPoints:['server/index.js'],bundle:true,write:false,format:'cjs',platform:'node'});
const loaded=new Module('push-worker');
loaded._compile(output.outputFiles[0].text,'push-worker');
const worker=loaded.exports.default;

test('edge push sends once, does not follow redirects and expires revoked subscriptions',async()=>{
  const sql=new DatabaseSync(':memory:');
  for(const file of readdirSync('drizzle').filter(f=>f.endsWith('.sql')).sort()) sql.exec(readFileSync('drizzle/'+file,'utf8'));
  const db={prepare(query){const stmt=sql.prepare(query);let args=[];return {bind(...values){args=values;return this;},async first(){return stmt.get(...args);},async all(){return {results:stmt.all(...args)};},async run(){return {meta:stmt.run(...args)};}};}};
  const vapid=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']);
  const client=await crypto.subtle.generateKey({name:'ECDH',namedCurve:'P-256'},true,['deriveBits']);
  const raw=async key=>Buffer.from(await crypto.subtle.exportKey('raw',key)).toString('base64url');
  const endpoint='https://fcm.googleapis.com/test-endpoint';
  const subscription={endpoint,keys:{p256dh:await raw(client.publicKey),auth:Buffer.alloc(16,1).toString('base64url')}};
  const env={DB:db,CRON_TOKEN:'test',VAPID_PUBLIC_KEY:await raw(vapid.publicKey),VAPID_PRIVATE_KEY:(await crypto.subtle.exportKey('jwk',vapid.privateKey)).d};
  const insert=id=>sql.prepare('INSERT INTO devices(id,token_hash,subscription,favorites,ueno_level,updated_at) VALUES (?,?,?,?,1,?)').run(id,id,JSON.stringify(subscription),JSON.stringify(['1234567890abcdef']),new Date().toISOString());
  insert('device-a');
  let sent=0,status=201;
  const original=global.fetch;
  global.fetch=async(url,options)=>{
    if(String(url).endsWith('/promotions.json')) return Response.json([{id:'1234567890abcdef',merchant_name:'Example',bank:'Bank',benefit_summary:'20% de descuento con QR',terms:{ends_on:'2099-12-31'},promotion_days:['lunes','martes','miércoles','jueves','viernes','sábado','domingo']}]);
    if(String(url).endsWith('/manifest.json')) return Response.json({favorite_aliases:{}});
    assert.equal(url,endpoint);
    if(options.redirect==='error') throw new TypeError('Invalid redirect value');
    assert.equal(options.redirect,'manual');
    assert.equal(options.headers['content-encoding'],'aes128gcm');
    assert.ok(options.body.byteLength>50);
    sent++;
    return new Response('',{status});
  };
  const dispatch=async(batch='')=> (await worker.fetch(new Request('https://service.test/api/push/dispatch'+(batch?'?batch='+batch:''),{method:'POST',headers:{Authorization:'Bearer test'}}),env)).json();
  try{
    assert.equal((await dispatch()).sent,1);
    assert.equal((await dispatch()).sent,0);
    assert.equal(sent,1);
    assert.equal((await dispatch('manual-test-1')).sent,1);
    assert.equal((await dispatch('manual-test-1')).sent,0);
    assert.equal((await dispatch()).sent,0);
    insert('device-b');status=410;
    assert.equal((await dispatch()).sent,0);
    assert.equal(sql.prepare('SELECT id FROM devices WHERE id=?').get('device-b'),undefined);
    assert.equal(sql.prepare("SELECT count(*) n FROM deliveries WHERE status='expired'").get().n,1);
    insert('device-c');status=302;
    assert.equal((await dispatch()).failed,1);
    assert.equal(sql.prepare("SELECT count(*) n FROM deliveries WHERE status='failed:provider_302'").get().n,1);
  }finally{global.fetch=original;sql.close();}
});
