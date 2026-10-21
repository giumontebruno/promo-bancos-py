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
 Object.assign(c,{nearbyMapState:{renderId:0},cleanupNearbyMaps:()=>{}});
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
 Object.assign(c,{nearbyMapState:{renderId:0},cleanupNearbyMaps:()=>{}});
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

test('branch eligibility requires bank, official PDF and merchant, never brand alone',()=>{
 const c={state:{activeCategory:'Todas'},PREMIUM_CATEGORY:'Premium',normalizeDayName:x=>String(x||'').toLowerCase(),uniquePromos:p=>[...new Map(p.map(x=>[x.id,x])).values()],hasPremiumVariant:()=>true};
 vm.runInNewContext(block('function getPromotionsForLocation(','function getFuelBrandsFromPlace('),c);
 const place={bank:'BNF',merchant_name:'Shop',source_url:'https://bnf.example/terms.pdf'};
 const a={id:'right',bank:'BNF',merchant_name:'Shop',source_url:place.source_url};
 const wrongBank={...a,id:'wrong-bank',bank:'Other'};
 const wrongDocument={...a,id:'wrong-document',source_url:'https://bnf.example/another.pdf'};
 const wrongShop={...a,id:'wrong-shop',merchant_name:'Different shop'};
 const index=new Map([['all',[a,wrongBank,wrongDocument,wrongShop]]]);
 assert.deepEqual(Array.from(c.getPromotionsForLocation(place,index),p=>p.id),['right']);
 assert.equal(c.getPromotionsForLocation({...place,bank:'Varios'},index).length,0);
 assert.equal(c.getPromotionsForLocation({...place,merchant_name:'Farmacias'},index).length,0);
});
test('Google place IDs shared by different merchants do not merge their branches',()=>{
 const c={normalizeDayName:x=>String(x||'').toLowerCase()};
 vm.runInNewContext(block('function getPlaceGroupKey(','function getBestPromoScore('),c);
 const a={place_id:'same-mall',merchant_name:'Shop A'},b={...a,merchant_name:'Shop B'};
 assert.notEqual(c.getPlaceGroupKey(a),c.getPlaceGroupKey(b));
 assert.equal(c.getPlaceGroupKey(a),c.getPlaceGroupKey({...a,bank:'Other'}));
});
