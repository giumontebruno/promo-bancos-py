const {test} = require('node:test');
const assert = require('node:assert/strict');
async function fixture() {
 const {assessHealth,EXPECTED_SOURCES} = await import('../scripts/maintenance-health.mjs');
 const now = new Date('2026-10-30T16:00:00Z');
 const promotions = EXPECTED_SOURCES.filter(b => b !== 'Zeta').map(bank => ({id: bank, bank}));
 const sources = Object.fromEntries(EXPECTED_SOURCES.map(bank => [bank, {status: 'fetched', records: 1, checked_at: now.toISOString(), last_successful_fetch_at: now.toISOString()}]));
 sources.Zeta = {status:'blocked', records:0, coverage_complete:false, attempted_at:now.toISOString()};
 return {assessHealth, input:{now, promotions, previous:promotions, sources, manifest:{generated_at:now.toISOString(), promotion_count:promotions.length}}};
}
test('new explicitly blocked zero source warns but does not veto healthy existing catalog', async()=>{
 const {assessHealth,input}=await fixture();const result=assessHealth(input);
 assert.equal(result.safe_to_commit,true);assert.equal(result.healthy,false);
 assert.ok(result.warnings.some(w=>w.includes('Zeta: blocked')));
});
test('zero source exception does not erase previously populated new bank',async()=>{
 const {assessHealth,input}=await fixture(); input.previous=[...input.previous,{id:'old-zeta',bank:'Zeta'}];
 assert.equal(assessHealth(input).safe_to_commit,false);
});
test('legacy bank cannot use explicit empty exception',async()=>{
 const {assessHealth,input}=await fixture();input.promotions=input.promotions.filter(p=>p.bank!=='GNB');
 input.previous=input.promotions; input.manifest.promotion_count=input.promotions.length;
 input.sources.GNB={...input.sources.Zeta};assert.equal(assessHealth(input).safe_to_commit,false);
});
test('fresh retrieval does not pretend pending source has completed review',async()=>{
 const {assessHealth,input}=await fixture();input.sources.Basa.status='partial';input.sources.Basa.checked_at='2026-10-10T00:00:00Z';
 const result=assessHealth(input);assert.equal(result.safe_to_commit,true);
 assert.ok(result.warnings.some(w=>w.includes('Basa: no complete successful extraction')));
 assert.ok(!result.warnings.some(w=>w.includes('Basa: no complete successful retrieval')));
});
