const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const stem='https://www.ueno.com.py/wp-content/uploads/2026/10/Campana-Tu-sueldo-esta-llegando-y-tu-50-tambien-_-OCT-2026';
for(const app of ['app-web','beta-web']){
 const s=fs.readFileSync(`${app}/app.js`,'utf8'),a=s.indexOf('function isDisplayablePromotion('),b=s.indexOf('\nfunction ',a+1),c={normalizeDayName:x=>String(x||'').toLowerCase()};vm.runInNewContext(s.slice(a,b),c);
 test(`${app}: personalized campaign cannot reappear from old or future-dated cached rows`,()=>{for(const v of ['v2','v3'])for(const ends_on of ['2026-10-31','2026-11-01'])assert.equal(c.isDisplayablePromotion({bank:'ueno bank',source_url:stem+v+'.pdf',benefit_summary:'50% reintegro;40%',terms:{ends_on}}),false);});
 test(`${app}: unrelated ueno offers remain visible`,()=>assert.equal(c.isDisplayablePromotion({bank:'ueno bank',source_url:'https://www.ueno.com.py/wp-content/uploads/2026/10/supermercados.pdf',benefit_summary:'20% reintegro'}),true));
 test(`${app}: app script cache key changed for financial safety release`,()=>assert.match(fs.readFileSync(`${app}/index.html`,'utf8'),/app\.js\?v=bank-sources-20261030/));
}
