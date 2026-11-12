const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('Farmacenter details retain source payment restrictions and sequential mechanism',()=>{
 const source=fs.readFileSync('beta-web/app.js','utf8');
 const start=source.indexOf('function extractAdditionalInfo(');
 const end=source.indexOf('\nfunction ',start+1);
 const c={formatDetailText:String};vm.createContext(c);vm.runInContext(source.slice(start,end),c);
 const rows=JSON.parse(fs.readFileSync('public/promotions.json')).filter(p=>p.bank==='GNB'&&p.merchant_name==='Farmacenter'&&p.terms.starts_on==='2026-11-02');
 assert.equal(rows.length,5);
 for(const row of rows){
  const text=c.extractAdditionalInfo(row,row.raw_detail);
  assert.match(text,/No participan tarjetas de débito ni crédito Visa/);
  assert.match(text,/importe final facturado después del descuento en caja/);
  assert.match(text,/titular y adicionales/);
  assert.match(row.source_document_url,/farmacenter-oct\.pdf$/);
 }
});
