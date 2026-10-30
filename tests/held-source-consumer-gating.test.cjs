const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const rows=JSON.parse(fs.readFileSync('public/promotions.json','utf8'));
for(const app of ['app-web','beta-web']){
 const source=fs.readFileSync(`${app}/app.js`,'utf8');const a=source.indexOf('function isActivePromotion('),b=source.indexOf('\nfunction shouldShowPromotion(',a);const ctx={};vm.runInNewContext(source.slice(a,b),ctx);
 test(`${app}: every retained unconfirmed source is excluded even inside a valid purchase window`,()=>{
  for(const row of rows.filter(r=>r.source_verification==='unconfirmed')) assert.equal(ctx.isActivePromotion({...row,terms:{starts_on:'2026-01-01',ends_on:'2026-12-31'}},'2026-10-30'),false,`${row.bank}:${row.id}`);
 });
 test(`${app}: source-conflict hold is independent of dates and benefit amounts`,()=>{
  for(const benefit_summary of ['30% reintegro','Hasta12cuotas sinintereses'])assert.equal(ctx.isActivePromotion({benefit_summary,source_verification:'unconfirmed',terms:{ends_on:'2999-12-31'}},'2026-10-30'),false);
 });
}
