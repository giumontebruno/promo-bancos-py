const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app-web/app.js','utf8');
const block=(start,end)=>source.slice(source.indexOf(start),source.indexOf(end));
test('cached formatters still change validity at Paraguay midnight',()=>{
 let now='2026-10-20T02:59:59Z',constructs=0;
 class Clock extends Date {constructor(...args){super(...(args.length?args:[now]));}}
 const c={Date:Clock,Intl:{DateTimeFormat:function(...args){constructs++;return new Intl.DateTimeFormat(...args);}}};
 vm.runInNewContext(block('const dateTimeFormatters =','function getTodayInParaguay(')+block('function isActivePromotion(','function shouldShowPromotion('),c);
 const ended={terms:{ends_on:'2026-10-19'}},future={terms:{starts_on:'2026-10-20',ends_on:'2026-10-20'}};
 assert.equal(c.isActivePromotion(ended),true);assert.equal(c.isActivePromotion(future),false);
 now='2026-10-20T03:00:00Z';assert.equal(c.isActivePromotion(ended),false);assert.equal(c.isActivePromotion(future),true);assert.equal(constructs,1);
});
test('text memoization preserves normalization and bounds retained source text',()=>{
 const c={};vm.runInNewContext(block('const normalizedTextCache =','function loadStoredJson('),c);
 const expected=v=>String(v||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace('miercoles','miércoles').replace('sabado','sábado').trim();
 for(const v of ['  MIÉRCOLES ','SÁBADO','Itaú','KAISEKI',null,'Á'.repeat(60000)])assert.equal(c.normalizeDayName(v),expected(v));
 for(let i=0;i<17000;i++)c.normalizeDayName(`${i} `+'Á'.repeat(300));
 assert.ok(vm.runInNewContext('normalizedTextCacheSize<=2000000 && normalizedTextCache.size<=16000',c));
});
test('typing updates the value immediately and renders only the latest query after composition',()=>{
 const listeners={},pending=new Map();let next=0,renders=0;
 const c={els:{searchInput:{addEventListener:(name,fn)=>listeners[name]=fn}},state:{query:'',activeView:'search'},resetNearbySelection:()=>{},setTimeout:fn=>{pending.set(++next,fn);return next;},clearTimeout:id=>pending.delete(id),render:()=>renders++};
 vm.runInNewContext(block('let searchRenderTimer =','els.results.addEventListener('),c);
 for(const value of ['K','Ka','Kaiseki'])listeners.input({target:{value}});
 assert.equal(c.state.query,'Kaiseki');assert.equal(renders,0);assert.equal(pending.size,1);
 listeners.compositionstart();assert.equal(pending.size,0);
 listeners.input({target:{value:'Kaiseki á'},isComposing:true});assert.equal(pending.size,0);
 listeners.compositionend({target:{value:'Kaiseki á'}});assert.equal(pending.size,1);
 [...pending.values()][0]();assert.equal(renders,1);assert.equal(c.state.query,'Kaiseki á');
});
test('sort memoization expires between renders and respects changed levels',()=>{
 let rate=10,calls=0;
 const c={getEstimatedSavings:()=>{calls++;return {percent:rate}},isInstallmentsOnly:()=>false};
 vm.runInNewContext(block('let sortInfoCache =','function sortByBenefitValue('),c);
 const p={};vm.runInNewContext('sortInfoCache=new WeakMap()',c);
 assert.equal(c.getSortInfo(p).savings.percent,10);c.getSortInfo(p);assert.equal(calls,1);
 rate=30;vm.runInNewContext('sortInfoCache=new WeakMap()',c);assert.equal(c.getSortInfo(p).savings.percent,30);assert.equal(calls,2);
});

test('clearing restores the same list but filters, data updates and midnight invalidate it',()=>{
 let day='2026-10-19',renders=0;
 const els=Object.fromEntries(['results','statusText','countText','bankTabs','categoryTabs','dayTabs'].map(k=>[k,{innerHTML:''}]));
 const c={els,state:{activeView:'today',query:'',activeBank:'Todos'},searchRenderTimer:0,sortInfoCache:null,clearTimeout:()=>{},getDateTimeFormatter:()=>({format:()=>day}),renderResults:()=>{renders++;els.results.innerHTML=c.state.activeBank+':'+c.state.query;}};
 vm.runInNewContext(block('let searchResetSnapshot =','function renderResults('),c);
 c.render();c.state.query='K';c.render(true);c.state.query='';c.render(true);
 assert.equal(els.results.innerHTML,'Todos:');assert.equal(renders,2);
 c.state.activeBank='BNF';c.render();c.state.query='K';c.render(true);c.state.query='';c.render(true);
 assert.equal(els.results.innerHTML,'BNF:');assert.equal(renders,4);
 day='2026-10-20';c.render(true);assert.equal(renders,5);
 c.render();assert.equal(renders,6);
});
