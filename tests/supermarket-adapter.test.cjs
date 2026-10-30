const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../beta-web/app.js'), 'utf8');

// Minimal immutable reproduction from public/promotions.json and locations.json
// inspected 2026-10-30. This tests identity, not ongoing campaign eligibility.
const url = 'https://www.bnf.gov.py/uploads/Promocion_Reintegro_Frigorificos_2026_OCT_4204e066ab.pdf';
const promo = {id:'41f18a27d2ea14dc', bank:'BNF', merchant_name:'POLLOS DON JUAN', source_url:url};
const place = {id:'loc-bnf-0dc1f4912fddbb84', bank:'BNF', merchant_name:'POLLOS DON JUAN', merchant_brand:'POLLOS DON JUAN', source_url:url, google_name:'Pollos Don Juan - Don Juan Gourmet'};
function context(promotions = [promo]) {
  const controls = {pilotEnabled:{checked:true}, pilotCard:{value:'Visa Oro BNF'}, pilotChannel:{value:'pos-bancard'}, pilotAmount:{value:'100000'}};
  const ctx = {
    state:{promotions, locations:[place], activeDay:'viernes'},
    document:{getElementById:id=>controls[id]},
    PaybackEligibility:{verified:()=>null},
    PaybackSupermarkets:{evaluate:(_promo, context)=>context},
    isSupermarketPilotPromo:()=>true,
    normalizeDayName:value=>String(value||'').toLowerCase(),
    uniquePromos:rows=>[...new Map(rows.map(row=>[row.id,row])).values()],
    PREMIUM_CATEGORY:'Premium',
    isActivePromotion:()=>true, selectedDateIso:()=> '2026-10-30', appliesToSelectedDay:()=>true,
    getNearbyLocalName:item=>item.google_name, isGenericNearbyName:()=>false,
    formatPlaceAddress:()=> 'Boggiani 5928', getPlaceGroupKey:item=>item.id,
  };
  for (const name of ['getPromotionsForLocation','withNearbyPlaceContext','getSupermarketAssessment']) {
    const start = source.indexOf(`function ${name}(`);
    assert.notEqual(start, -1);
    const end = source.indexOf('\nfunction ',start+1);
    vm.runInNewContext(source.slice(start,end === -1 ? undefined : end),ctx);
  }
  return ctx;
}

test('map display-name enrichment preserves verified branch participation through original ID',()=>{
  const ctx=context();
  const enriched=ctx.withNearbyPlaceContext(promo,place);
  assert.notEqual(enriched.merchant_name,promo.merchant_name);
  assert.equal(enriched._sourceMerchantName,promo.merchant_name);
  // Demonstrate why revalidating the display-only name was incorrect.
  assert.equal(ctx.getPromotionsForLocation(place,new Map([['pilot',[enriched]]]),'Todas').length,0);
  const result=ctx.getSupermarketAssessment(enriched);
  assert.equal(result.branch.match,true);
  assert.equal(result.branch.source,url);
});

test('adapter preserves source name when original record is not in the loaded list',()=>{
  const ctx=context([]);
  assert.equal(ctx.getSupermarketAssessment(ctx.withNearbyPlaceContext(promo,place)).branch.match,true);
});

test('map adaptation does not invent participation for another merchant',()=>{
  const other={...promo,id:'other',merchant_name:'OTRO COMERCIO'};
  const ctx=context([other]);
  assert.equal(ctx.getSupermarketAssessment(ctx.withNearbyPlaceContext(other,place)).branch.match,false);
});
