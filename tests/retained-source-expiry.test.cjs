const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
for(const app of ['app-web','beta-web']){
 const source=fs.readFileSync(`${app}/app.js`,'utf8');const a=source.indexOf('function isActivePromotion('),b=source.indexOf('\nfunction shouldShowPromotion(',a);
 const ctx={getDateTimeFormatter:()=>({format:()=> '2026-11-02'})};vm.runInNewContext(source.slice(a,b),ctx);
 test(`${app}: stale retained rows expire without a new deployment`,()=>{
   const p={source_verification:'official_document',terms:{ends_on:'2999-12-31'}};
   for(const stamp of ['2020-01-01T00:00:00Z','invalid'])assert.equal(ctx.isActivePromotion({...p,source_retention_expires_at:stamp}),false);
   assert.equal(ctx.isActivePromotion({...p,source_retention_expires_at:'2999-12-31T00:00:00Z'}),true);
   assert.equal(ctx.isActivePromotion(p),true);
 });
}
