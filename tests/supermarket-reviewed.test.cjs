const {test}=require('node:test');const assert=require('node:assert/strict');
const reviews=require('../beta-web/supermarket-reviewed.js'),engine=require('../beta-web/supermarket-eligibility.js');
const promo=require('../public/promotions.json').find(p=>p.id==='6bdaac371ae91d39');
const context=card=>({evidence:reviews.verified(promo,card),card,channel:'pos-bancard',amount:2000000,dateMatches:true});
test('real supermarket has usable exact card options and traceable official PDF',()=>{assert.equal(reviews.cards(promo).length,8);assert.match(reviews.provenance.source_pdf,/EL%20PAIS/);assert.match(reviews.provenance.source_sha256,/^[a-f0-9]{64}$/);});
test('actual source card groups receive different caps; unknown consumption is not promised',()=>{for(const [card,cap] of [['Visa Platinum Familiar',300000],['Visa Oro Familiar',200000]]){const r=engine.evaluate(promo,context(card));assert.equal(r.estimate,cap);assert.equal(r.status,'needs_confirmation');}});
test('InterExa is unresolved and QR ambiguity is not a fabricated exclusion',()=>{assert.equal(engine.evaluate(promo,context('Mastercard InterExa Familiar')).estimate,null);const r=engine.evaluate(promo,{...context('Visa Oro Familiar'),channel:'qr'});assert.equal(r.status,'needs_confirmation');assert.ok(r.reasons.some(x=>x.includes('no confirma esta forma')));});
test('expired date and wrong card remain explicit negatives',()=>{assert.equal(engine.evaluate(promo,{...context('Visa Oro Familiar'),dateMatches:false}).status,'not_applies');assert.equal(engine.evaluate(promo,context('Gourmet Familiar')).status,'not_applies');});
test('source or raw terms changes invalidate reviewed rules rather than inheriting them',()=>{for(const patch of [{raw_detail:promo.raw_detail+' changed'},{source_url:'https://example.test'},{original_source_text:promo.original_source_text+' changed'},{promotion_days:['lunes']}])assert.equal(reviews.verified({...promo,...patch},'Visa Oro Familiar'),null);});
test('official branch address has no fabricated coordinates',()=>{const b=reviews.verified(promo).branch;assert.equal(b.address,'Antequera y 25 de mayo, Asunción');assert.equal(b.lat,undefined);assert.equal(b.lng,undefined);});

const superseis=require('../public/promotions.json').find(p=>p.id==='657860c088e9922b');
const denis=require('../public/locations.json').locations.find(p=>p.id==='loc-bba38ccaba');
test('one explicit Familiar branch links to existing independent geography, not the whole chain',()=>{
 const link=reviews.branchLink(superseis,denis);assert.ok(link);assert.equal(link.geographicSource,denis.source_url);assert.notEqual(link.source,denis.source_url);
 assert.equal(reviews.branchLink(superseis,{...denis,id:'other-branch'}),null);
 assert.equal(reviews.branchLink(superseis,{...denis,qa_hold:true}),null);
 assert.equal(reviews.branchLink(superseis,{...denis,lat:denis.lat+0.01}),null);
 assert.equal(reviews.branchOffers(denis,[superseis],'2026-10-30').length,1);
 assert.equal(reviews.branchOffers(denis,[superseis],'2026-12-26').length,0);
});
test('shared list/map engine preserves exact card/cap decision and only removes branch uncertainty',()=>{
 const c={...context('Visa Platinum Familiar'),evidence:reviews.verified(superseis,'Visa Platinum Familiar')};
 const list=engine.evaluate(superseis,c),map=engine.evaluate(superseis,{...c,branch:reviews.branchLink(superseis,denis)});
 assert.equal(list.estimate,map.estimate);assert.equal(map.estimate,300000);assert.equal(list.status,'needs_confirmation');assert.equal(map.status,'needs_confirmation');
 assert.equal(list.reasons.length,map.reasons.length+1);
 for(const channel of ['qr','online']) assert.equal(engine.evaluate(superseis,{...c,channel}).status,'needs_confirmation');
});
