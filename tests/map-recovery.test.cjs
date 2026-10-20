const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app-web/app.js','utf8');
const block=(a,b)=>source.slice(source.indexOf(a),source.indexOf(b));
test('a failed locations download is retryable and never becomes an empty loaded map',async()=>{
 let response={ok:false};
 const c={state:{locations:[],locationsLoaded:false},LOCATIONS_URL:'/locations',fetch:async()=>response};
 vm.runInNewContext(block('async function loadLocations(','function toggleFavorite('),c);
 await assert.rejects(c.loadLocations());
 assert.equal(c.state.locationsLoaded,false);assert.equal(c.state.locationsStatus,'error');
 response={ok:true,json:async()=>({})};await assert.rejects(c.loadLocations());
 assert.equal(c.state.locationsLoaded,false);
 response={ok:true,json:async()=>({locations:[{merchant_name:'Test fixture',lat:null,lng:null}]})};
 await c.loadLocations();assert.equal(c.state.locationsLoaded,true);assert.equal(c.state.locationsStatus,'ready');
 assert.equal(c.state.locations[0].lat,null);
});
test('GPS success followed by download failure displays loading error rather than zero promotions',()=>{
 const c={state:{location:{lat:-25.3,lng:-57.6},locationsLoaded:false,locationsStatus:'error',locationStatus:'error'},els:{statusText:{},countText:{},results:{}}};
 vm.runInNewContext(block('function renderNearbyView(','function getNearbyActiveFilterText('),c);
 c.renderNearbyView();assert.match(c.els.results.innerHTML,/No pudimos cargar/);assert.match(c.els.results.innerHTML,/Reintentar carga/);assert.doesNotMatch(c.els.results.innerHTML,/Sin locales|0 ubicaciones/);
 c.state.locationsStatus='loading';c.state.locationStatus='loading';c.renderNearbyView();assert.match(c.els.results.innerHTML,/Cargando el mapa/);
});
test('geolocation errors distinguish permission denial, timeout and unavailable position',async()=>{
 for(const [code,status] of [[1,'denied'],[2,'unavailable'],[3,'timeout']]){
  const c={state:{},render:()=>{},navigator:{geolocation:{getCurrentPosition:(ok,fail)=>fail({code})}}};
  vm.runInNewContext(block('async function requestLocation(','async function requestNearbyLocationAutomatically('),c);
  await c.requestLocation();assert.equal(c.state.locationStatus,status);
 }
});
test('valid card variants remain visible when no verified map coordinates exist',()=>{
 const promos=JSON.parse(fs.readFileSync('public/promotions.json','utf8')).filter(p=>['99544f5b9adac703','18e6109610e8dd1b'].includes(p.id));
 assert.equal(promos.length,2);
 const c={state:{locationsLoaded:true,locationStatus:'ready'},els:{statusText:{},countText:{},results:{}},getNearbyPromoPoints:()=>[],KNOWN_LOCAL_POINTS:[{}],getBankTheme:()=>'',getPointPrimaryPromo:()=>null,uniquePromos:p=>p,buildNearbyPromoIndex:()=>new Map([['itau|combustible',promos]]),escapeHtml:s=>s,getNearbyActiveFilterText:()=> 'Itaú · Combustible · Lunes',renderNearbyPromoGroups:p=>p.map(x=>x.id).join('|')};
 vm.runInNewContext(block('function renderNearbyView(','function getNearbyActiveFilterText('),c);
 c.renderNearbyView();assert.match(c.els.countText.textContent,/2 beneficios/);
 for(const p of promos)assert.ok(c.els.results.innerHTML.includes(p.id));
 assert.match(c.els.results.innerHTML,/sin ubicación en el mapa/);
 assert.equal(c.els.statusText.textContent,'Sin ubicación verificada');
 assert.doesNotMatch(c.els.results.innerHTML,/\d+(?:\.\d+)?\s+km\b|class="map-stage"|Cerca de tu ubicación/);
});
test('reviewed stations only match approved card IDs within participation dates',()=>{
 const c={state:{},isActivePromotion:p=>p.terms.ends_on>='2026-10-20',uniquePromos:p=>p};
 vm.runInNewContext(block('function getPromotionsForLocation(','function getFuelBrandsFromPlace('),c);
 const place={promotion_ids:['classic','premium'],participation_ends_on:'2026-10-26'};
 const index=new Map([['itau|combustible',[{id:'classic'},{id:'premium'},{id:'wednesday'}]]]);
 assert.equal(c.getPromotionsForLocation(place,index).length,2);
 c.isActivePromotion=p=>p.terms.ends_on>='2026-10-27';assert.equal(c.getPromotionsForLocation(place,index).length,0);
});
