const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
for(const app of ['app-web','beta-web']) test(`${app} preserves first-purchase restriction instead of daily recurrence`,()=>{
 const s=fs.readFileSync(`${app}/app.js`,'utf8'),a=s.indexOf('function getDisplayDays('),b=s.indexOf('\nfunction ',a+1),ctx={};vm.runInNewContext(s.slice(a,b),ctx);
 assert.equal(ctx.getDisplayDays({day_text:'Primera compra elegible',promotion_days:[],validity:'Desde2026-01-16hasta2026-12-31'}),'Solo primera compra elegible');
});
