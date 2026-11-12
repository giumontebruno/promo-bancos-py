const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('beta-web/app.js','utf8');
const context={formatDetailText:String};
vm.createContext(context);
for(const name of ['formatCapsText','getDetailExclusions']) {
 const start=source.indexOf(`function ${name}(`);
 const end=source.indexOf('\nfunction ',start+1);
 vm.runInContext(source.slice(start,end),context);
}
const bnf=JSON.parse(fs.readFileSync('public/promotions.json')).filter(p=>p.bank==='BNF' && p.terms?.starts_on?.startsWith('2026-11'));
test('BNF details preserve exact tier caps and shared account/category scope',()=>{
 assert.equal(bnf.length,65);
 for(const promo of bnf) {
  assert.equal(context.formatCapsText(promo),promo.caps_and_minimums,promo.id);
  assert.match(context.formatCapsText(promo),/titular y sus adicionales/);
  assert.match(context.formatCapsText(promo),/forma conjunta/);
 }
});
test('BNF exclusions retain processors as well as debit and installments',()=>{
 for(const promo of bnf) {
  const text=context.getDetailExclusions(promo);
  assert.match(text,/débito/);
  assert.match(text,/cuotas/);
  assert.match(text,/otras procesadoras/);
  assert.match(text,/Dinelco, Cabal, Pagopar/);
 }
});
