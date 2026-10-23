const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('beta-web/app.js','utf8');
const promo={id:'offer',bank:'Itaú',merchant_name:'Shop',source_url:'https://bank.example/terms.pdf'};
const branch={id:'a',name:'Shop branch',merchant_name:'Shop',bank:'Itaú',source_url:promo.source_url,lat:-25.3,lng:-57.6,geocode_source:'official',address:'First street',place_id:'verified-id'};
function context(){
 const c={selectedDateIso:()=>"2026-10-23",state:{locations:[],activeCategory:'Club Black',location:null},PREMIUM_CATEGORY:'Club Black',
 normalizeDayName:s=>String(s||'').toLowerCase(),isGenericLocationMatchedToMall:()=>false,
 uniquePromos:p=>p,hasPremiumVariant:()=>false,isActivePromotion:()=>true,
 preferBetterPlace:(a,b)=>b,getPlaceDisplayName:p=>p.name,
 escapeHtml:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;'),
 renderIcon:()=>'<svg aria-hidden="true"></svg>',els:{dialog:{open:true}},detailLocationState:null};
 c.escapeAttribute=c.escapeHtml;
 vm.createContext(c);
 for(const name of ['isReliableMapLocation','getPlaceGroupKey','getPromotionsForLocation','getDetailPlaces','getMapsUrl','formatPlaceAddress','renderDetailDestination','renderDetailLocations','loadDetailLocations','openDetailMap']){
  let start=source.indexOf(`function ${name}(`);
  if(source.slice(start-6,start)==='async ')start-=6;
  let end=source.indexOf('\nfunction ',start+1);
  const asyncEnd=source.indexOf('\nasync function ',start+1);if(asyncEnd>=0 && (end<0||asyncEnd<end))end=asyncEnd;
  vm.runInContext(source.slice(start,end),c);
 }
 return c;
}
test('detail branches use exact offer eligibility independent of current UI filters',()=>{
 const c=context();c.state.locations=[branch,{...branch,id:'other-bank',bank:'Other'},{...branch,id:'other-doc',source_url:'https://bank.example/other.pdf'},{...branch,id:'other-merchant',merchant_name:'Different',name:'Different'}];
 assert.deepEqual(Array.from(c.getDetailPlaces(promo),p=>p.id),['a']);
 assert.equal(c.state.activeCategory,'Club Black');
});
test('unverified, approximate, online and invalid-coordinate destinations cannot become routes',()=>{
 const c=context();
 for(const invalid of [{lat:91},{lng:181},{qa_hold:true},{needs_review:true},{online_only:true},{geocode_source:'city_approximation'},{geocode_source:''},{google_enrichment_status:'needs_review'}]){
  c.state.locations=[{...branch,...invalid}];assert.equal(c.getDetailPlaces(promo).length,0);
 }
});
test('duplicate branch records are deduplicated but distinct destinations stay separate',()=>{
 const c=context();c.state.locations=[branch,{...branch,id:'dup'},{...branch,id:'b',place_id:'second-id',address:'Second street'}];
 assert.equal(c.getDetailPlaces(promo).length,2);
});
test('multiple branches require choice before routes; source context selects exact branch',async()=>{
 const c=context();c.state.locations=[branch,{...branch,id:'b',place_id:'second-id'}];c.loadLocations=async()=>{};
 const node={};c.els.dialogContent={querySelector:()=>node};
 for(const placeId of ['', 'b','unknown']){
  const ctx={promo,placeId,places:[],loading:true};c.detailLocationState=ctx;await c.loadDetailLocations(ctx);
  assert.equal(ctx.selectedKey,placeId==='b'?c.getPlaceGroupKey(c.state.locations[1]):'');
  assert.match(node.innerHTML,/for="detailBranch"/);
  if(placeId!=='b')assert.doesNotMatch(node.innerHTML,/data-detail-map|class="detail-directions"/);
 }
});
test('single verified branch is usable without requesting GPS',async()=>{
 const c=context();c.state.locations=[branch];c.navigator={geolocation:{getCurrentPosition(){throw Error('GPS must not be requested');}}};c.loadLocations=async()=>{};
 const node={};c.els.dialogContent={querySelector:()=>node};const ctx={promo,places:[],loading:true};c.detailLocationState=ctx;
 await c.loadDetailLocations(ctx);assert.equal(ctx.selectedKey,c.getPlaceGroupKey(branch));assert.match(node.innerHTML,/Cómo llegar/);assert.match(node.innerHTML,/First street/);
});
test('directions use exact coordinates and place ID, with optional existing origin',()=>{
 const c=context();const ctx={places:[branch],selectedKey:c.getPlaceGroupKey(branch)};
 const html=c.renderDetailDestination(ctx);assert.match(html,/target="_blank" rel="noopener noreferrer"/);
 const url=new URL(c.getMapsUrl(branch));assert.equal(url.searchParams.get('destination'),'-25.3,-57.6');assert.equal(url.searchParams.get('destination_place_id'),'verified-id');assert.equal(url.searchParams.get('travelmode'),'driving');assert.equal(url.searchParams.has('origin'),false);
 c.state.location={lat:-25,lng:-57};assert.equal(new URL(c.getMapsUrl(branch)).searchParams.get('origin'),'-25,-57');
});
test('no locations gives an explained source fallback, never a disabled or guessed route',()=>{
 const c=context();const html=c.renderDetailLocations({places:[]});assert.match(html,/ubicación verificada/);assert.match(html,/data-scroll-source/);assert.doesNotMatch(html,/disabled|google.com|data-detail-map/);
});
test('failed branch fetch is retryable and stale dialog completion cannot replace current content',async()=>{
 const c=context();const node={innerHTML:'unchanged'};c.els.dialogContent={querySelector:()=>node};c.loadLocations=async()=>{throw Error('offline');};
 const ctx={promo,places:[],loading:true};c.detailLocationState=ctx;await c.loadDetailLocations(ctx);assert.match(node.innerHTML,/data-detail-location-retry/);
 let finish;c.loadLocations=()=>new Promise(r=>finish=r);node.innerHTML='new dialog';const pending=c.loadDetailLocations(ctx);c.detailLocationState={};finish();await pending;assert.equal(node.innerHTML,'new dialog');
});
test('closing dialog before branch fetch finishes does not update content',async()=>{
 const c=context();let finish;c.loadLocations=()=>new Promise(r=>finish=r);c.els.dialogContent={querySelector(){throw Error('closed dialog update');}};
 const ctx={promo,places:[],loading:true};c.detailLocationState=ctx;const pending=c.loadDetailLocations(ctx);c.els.dialog.open=false;finish();await pending;
});
test('map action preserves filters and passes exact verified point without GPS',()=>{
 const c=context();c.state.locations=[branch];c.state.query='kept';c.state.activeDay='lunes';c.state.activeBank='Other';c.detailLocationState={promo,selectedKey:c.getPlaceGroupKey(branch)};
 let selected,closed=false,rendered=false,focused=false;c.enrichNearbyPoint=p=>p;c.els.dialog.close=()=>closed=true;c.render=()=>rendered=true;c.selectNearbyPlace=(key,point)=>selected={key,point};c.document={querySelector:()=>({focus(){focused=true;},scrollIntoView(){}})};
 c.openDetailMap();assert.ok(closed&&rendered&&focused);assert.equal(c.state.activeView,'nearby');assert.equal(c.state.query,'kept');assert.equal(c.state.activeBank,'Other');assert.equal(c.state.activeDay,'lunes');assert.equal(selected.point.place.id,'a');assert.equal(selected.point.promos[0].id,'offer');
});
test('stale selection and injection strings cannot create a route',()=>{
 const c=context();c.state.locations=[{...branch,qa_hold:true}];c.detailLocationState={promo,selectedKey:c.getPlaceGroupKey(branch)};c.render=()=>{throw Error('must not open map');};c.openDetailMap();
 const unsafe={...branch,name:'<img src=x onerror=alert(1)>',address:'<script>bad</script>'};const html=c.renderDetailDestination({places:[unsafe],selectedKey:c.getPlaceGroupKey(unsafe)});assert.doesNotMatch(html,/<img|<script>/);assert.match(html,/&lt;script>/);
});
test('Ajos is not assigned an arbitrary branch from the real catalog',()=>{
 const c=context();const promos=JSON.parse(fs.readFileSync('public/promotions.json','utf8'));const data=JSON.parse(fs.readFileSync('public/locations.json','utf8'));c.state.locations=Array.isArray(data)?data:data.locations;
 const ajos=promos.find(p=>p.id==='27d2e79d2dc2d30b');assert.ok(ajos);assert.equal(c.getDetailPlaces(ajos).length,0);
});
test('keyboard/native branch change updates links without opening a map or external page',()=>{
 const c=context();const node={};c.detailLocationState={places:[branch],selectedKey:''};let handler;c.els.dialogContent={addEventListener:(type,fn)=>handler=fn,querySelector:()=>node};
 const start=source.indexOf('els.dialogContent.addEventListener("change",');const end=source.indexOf('els.dialogContent.addEventListener("input",',start);
 vm.runInContext(source.slice(start,end),c);handler({target:{id:'detailBranch',value:c.getPlaceGroupKey(branch)}});
 assert.match(node.innerHTML,/destination=-25.3%2C-57.6/);assert.match(node.innerHTML,/data-detail-map/);
 handler({target:{id:'detailBranch',value:''}});assert.doesNotMatch(node.innerHTML,/data-detail-map/);
});
test('detail preserves monetary qualifiers, full conditions and selected variant context',()=>{
 const c=context();const p={...promo,merchant_name:'Shop <special>'};c.state.promotions=[p];c.state.locations=[branch];c.state.uenoLevel=1;c.window={};
 Object.assign(c,{getVariantByKey:()=>({kind:'base'}),isFavoritePromotion:()=>false,getSelectedUenoLevelDetails:()=>null,getEstimatedSavings:()=>({refundCap:1000000}),getPromoTitle:p=>p.merchant_name,getBankLabel:b=>b,getPromoCategoryGroup:()=> 'Tiendas',getDisplayBenefit:()=> '20% reintegro',getDisplayDays:()=> 'Lunes',getDisplayValidity:()=> 'Hasta diciembre',formatGuarani:()=> 'Gs. 1.000.000',isUenoPowerPromo:()=>false,renderDetailRows:()=>'<div>Tarjetas y exclusiones completas</div>',formatLastUpdated:()=>'',safeSourceUrl:s=>s});
 c.els.dialogContent={};c.els.dialog.showModal=()=>{};let loaded;c.loadDetailLocations=ctx=>loaded=ctx;
 const start=source.indexOf('function openDetail(');vm.runInContext(source.slice(start,source.indexOf('async function loadPromotions(',start)),c);
 c.openDetail('offer','base');const html=c.els.dialogContent.innerHTML;
 assert.match(html,/Shop &lt;special>/);assert.match(html,/id="promoDetailTitle"/);assert.match(html,/Sujeto a compra, tarjeta y saldo disponible/);assert.match(html,/Tarjetas y exclusiones completas/);assert.match(html,/data-calculator-variant="base"/);assert.equal(loaded.promo,p);
 c.getEstimatedSavings=()=>({refundCap:0,unconfirmed:true});c.openDetail('offer');assert.doesNotMatch(c.els.dialogContent.innerHTML,/Ahorro máximo estimado/);
});
