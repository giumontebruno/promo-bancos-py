const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('beta-web/app.js','utf8');
const start=source.indexOf('function getDetailExclusions(');
const end=source.indexOf('\nfunction ',start+1);
const c={formatDetailText:String,extractExcludedCards:()=> 'No especificado'};
vm.createContext(c);vm.runInContext(source.slice(start,end),c);
test('all six Familiar McDonalds variants show their explicit excluded cards',()=>{
 const rows=JSON.parse(fs.readFileSync('public/promotions.json')).filter(p=>p.bank==='Familiar' && p.merchant_name.startsWith("McDonald's -"));
 assert.equal(rows.length,6);
 for(const row of rows){
  const result=c.getDetailExclusions(row);
  assert.match(result,/empresariales, Gourmet Cards ni Movil Cards/);
  assert.doesNotMatch(result,/No especificado/);
 }
});
test('unrelated merchants retain existing structured or fallback exclusions',()=>{
 assert.equal(c.getDetailExclusions({bank:'Familiar',merchant_name:'Other',raw_detail:'No participan tarjetas especiales.'}),'No especificado');
 assert.equal(c.getDetailExclusions({bank:'Familiar',merchant_name:'Other',terms:{exclusions:['Visa']}}),'Visa');
});
