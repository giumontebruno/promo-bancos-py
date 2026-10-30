const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
for(const app of ['app-web','beta-web']){
const s=fs.readFileSync(`${app}/app.js`,'utf8'),a=s.indexOf('function isDisplayablePromotion('),b=s.indexOf('\nfunction ',a+1),ctx={normalizeDayName:x=>String(x||'').toLowerCase()};vm.runInNewContext(s.slice(a,b),ctx);
const row={id:'95a62440aa5e167b',bank:'Continental',merchant_name:'Contimarket - 25%',source_url:'https://www.bancontinental.com.py/api/comercios?_limit=-1',benefit_summary:'25% reintegro',raw_detail:'25% de reintegro. Vigente el 28 octubre de 2026. Además, todos los días: 12 cuotas.'};
test(`${app}: captured Oct28 discount cannot appear Oct30 from daily financing`,()=>assert.equal(ctx.isDisplayablePromotion(row),false));
test(`${app}: future Nov4 offer is not blocked by historical ID`,()=>assert.equal(ctx.isDisplayablePromotion({...row,raw_detail:row.raw_detail.replace('28 octubre','4 noviembre')}),true));
test(`${app}: separate daily financing survives`,()=>assert.equal(ctx.isDisplayablePromotion({...row,merchant_name:'Contimarket.com',benefit_summary:'12 cuotas sin intereses'}),true));
}
