const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../app-web/app.js'),'utf8');
const ctx={isGenericLocationMatchedToMall:()=>false};
vm.runInNewContext(source.slice(source.indexOf('function isPreciseNearbyPoint('),source.indexOf('function isGenericLocationMatchedToMall(')),ctx);
const place={lat:-25.3,lng:-57.6,geocode_source:'official_operator_reviewed',google_confidence:'high'};
test('QA hold excludes map and precise nearby navigation even with official or high-confidence metadata',()=>{
 for(const source of ['official_operator_reviewed','google_places_text_search']){
  const held={...place,geocode_source:source,qa_hold:true};
  assert.equal(ctx.isReliableMapLocation(held),false);
  assert.equal(ctx.isPreciseNearbyPoint({place:held}),false);
 }
});
test('needs_review excludes both paths; unaffected verified point remains usable',()=>{
 assert.equal(ctx.isReliableMapLocation({...place,needs_review:true}),false);
 assert.equal(ctx.isPreciseNearbyPoint({place:{...place,needs_review:true}}),false);
 assert.equal(ctx.isReliableMapLocation(place),true);
 assert.equal(ctx.isPreciseNearbyPoint({place}),true);
});
