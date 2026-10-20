const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app-web/app.js', 'utf8');
function context() {
  const ctx = {normalizeDayName: s => String(s || '').toLowerCase(), isGenericLocationMatchedToMall: () => false};
  for (const [start, end] of [['getMapVisiblePoints','getPointPrimaryPromo'], ['getPlaceGroupKey','getBestPromoScore'], ['isReliableMapLocation','isGenericLocationMatchedToMall']]) {
    vm.runInNewContext(source.slice(source.indexOf(`function ${start}(`), source.indexOf(`function ${end}(`)), ctx);
  }
  return ctx;
}
const place = {merchant_name:'Local A', lat:-25.3, lng:-57.6, geocode_source:'official'};
test('map retains all reliable points beyond former 18/22/30/70 limits', () => {
  const ctx=context();
  const points=Array.from({length:100}, (_,i)=>({place:{...place,name:`Local ${i}`}}));
  assert.equal(ctx.getMapVisiblePoints(points).length,100);
});
test('map rejects impossible coordinates, approximate positions and online-only shops', () => {
  const ctx=context();
  for (const bad of [{lat:91}, {lng:-181}, {online_only:true}, {geocode_source:'city_approximation'}, {google_enrichment_status:'needs_review'}]) {
    assert.equal(ctx.isReliableMapLocation({...place,...bad}),false);
  }
});
test('different merchants sharing coordinates remain separately selectable', () => {
  const ctx=context();
  assert.notEqual(ctx.getPlaceGroupKey(place),ctx.getPlaceGroupKey({...place,merchant_name:'Local B'}));
  assert.equal(ctx.getPlaceGroupKey({...place,bank:'BNF'}),ctx.getPlaceGroupKey({...place,bank:'ueno'}));
});

test('location categories use the same grouping as promotion categories', () => {
  const ctx=context();
  Object.assign(ctx,{state:{activeCategory:'Todas'},PREMIUM_CATEGORY:'Club Black',getPromoCategoryGroup:p=>p.category==='Mayoristas'?'Supermercados':p.category,getFuelBrandsFromPlace:()=>[],uniquePromos:p=>[...new Map(p.map(x=>[x.id,x])).values()]});
  vm.runInNewContext(source.slice(source.indexOf('function getPromotionsForLocation('),source.indexOf('function getFuelBrandsFromPlace(')),ctx);
  const promo={id:'grutter',bank:'BNF',merchant_name:'Casa Grutter',merchant_locations_or_group:'',source_url:'official.pdf'};
  const index=new Map([['bnf|supermercados',[promo]]]);
  const actual=ctx.getPromotionsForLocation({category:'Mayoristas',bank:'BNF',merchant_name:'Casa Grutter',name:'Casa Grutter',google_name:'Casa Grutter',source_url:'official.pdf'},index);
  assert.equal(actual.length,1);
});
