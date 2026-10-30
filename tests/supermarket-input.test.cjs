const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('typing purchase amount refreshes estimates without blur and coalesces edits',()=>{
 const src=fs.readFileSync('beta-web/app.js','utf8');const start=src.indexOf('let supermarketAmountTimer = null;');assert.ok(start>=0);
 const callbacks=new Map(),events={};let id=0,renders=0,resets=0;
 const ctx={document:{getElementById:()=>({addEventListener:(event,fn)=>events[event]=fn})},clearTimeout:i=>callbacks.delete(i),setTimeout:fn=>{callbacks.set(++id,fn);return id;},resetNearbySelection:()=>resets++,render:()=>renders++};
 vm.runInNewContext(src.slice(start),ctx);events.input();events.input();events.input();assert.equal(callbacks.size,1);assert.equal(renders,0);[...callbacks.values()][0]();assert.equal(renders,1);assert.equal(resets,1);
});
test('pilot fields have explicit stable accessible names',()=>{const html=fs.readFileSync('beta-web/index.html','utf8');for(const [id,label] of [['pilotCard','Tarjeta exacta'],['pilotChannel','Forma de pago'],['pilotAmount','Compra en guaraníes']])assert.ok(html.includes(`id="${id}" aria-label="${label}"`));});
