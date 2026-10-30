const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const root=require('node:path').resolve(__dirname,'..');
const src=fs.readFileSync(root+'/app-web/app.js','utf8');
const all=JSON.parse(fs.readFileSync(root+'/public/promotions.json','utf8'));
const manifest=JSON.parse(fs.readFileSync(root+'/public/manifest.json','utf8'));
const campaign='2e507b9fe5140149',old='4170fdc63d3858cd';
const offers=all.filter(p=>p.bank==='Atlas'&&p.campaign_id===campaign);
function ctx(promotions=all, aliases=manifest.favorite_aliases||{}){
 const c={state:{uenoLevel:1,promotions,favorites:new Set([old]),favoriteAliases:aliases,activeView:'favorites'},window:{},STORAGE_KEYS:{favorites:'favorites'},saveStoredJson(){},syncFavoriteAlerts(){},render(){},els:{},normalizeDayName:x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),isUenoPowerPromo:()=>false,PaybackBenefits:require(root+'/app-web/benefit-rules.js')};
 for(const name of ['getPromoVariants','percentNumber','getMainBenefit','getSelectedUenoLevelDetails','getEstimatedSavings']){
  const start=src.indexOf('function '+name+'('),next=src.indexOf('\nfunction ',start+1);vm.runInNewContext(src.slice(start,next),c);
 }
 vm.runInNewContext(src.slice(src.indexOf('function favoriteKey('),src.indexOf('function matchesSelectedDay(')),c);
 vm.runInNewContext(src.slice(src.indexOf('function toggleFavorite('),src.indexOf('function getCategories(')),c);
 c.state.favorites=c.normalizeFavoriteIds(c.state.favorites); // Same normalization as loadPromotions and beta-account.
 return c;
}
test('normalized catalog contains exactly three Atlas offers with original campaign identity',()=>{
 assert.equal(offers.length,3);
 assert.equal(new Set(offers.map(p=>p.id)).size,3);
 assert.deepEqual(offers.map(p=>p.benefit_summary).sort(),['15% de reintegro','20% de reintegro','Hasta 18 cuotas sin intereses'].sort());
 for(const p of offers){assert.equal(p.terms.starts_on,'2026-10-23');assert.equal(p.terms.ends_on,'2026-10-23');assert.equal(p.category,'Viajes');}
});
test('historical favorite resolves through actual manifest and selects all three offers',()=>{
 assert.equal(offers.length,3);
 const c=ctx();assert.deepEqual([...c.normalizeFavoriteIds([old,campaign,...offers.map(p=>p.id),'unrelated'])],[campaign,'unrelated']);
 assert.ok(offers.every(p=>c.isFavoritePromotion(p)));
 c.toggleFavorite(offers[0].id);assert.ok(offers.every(p=>!c.isFavoritePromotion(p)));
 c.toggleFavorite(offers[2].id);assert.ok(offers.every(p=>c.isFavoritePromotion(p)));
 assert.deepEqual([...c.state.favorites],[campaign]);
});
test('normalized variants calculate 15% vs20%, minimum/cap, and zero monetary saving for financing',()=>{
 assert.equal(offers.length,3);const c=ctx();
 for(const [benefit,rate,max] of [['15% de reintegro',15,1800000],['20% de reintegro',20,2400000],['Hasta 18 cuotas sin intereses',0,0]]){
  const p=offers.find(p=>p.benefit_summary===benefit),v=c.getPromoVariants(p)[0];
  assert.equal(v.benefit,benefit);
  assert.equal(c.getEstimatedSavings(p,8000000,v).refundCap,8000000*rate/100);
  assert.equal(c.getEstimatedSavings(p,15000000,v).refundCap,max);
  assert.equal(c.getEstimatedSavings(p,null,v).refundCap,max);
  if(rate){assert.equal(c.getEstimatedSavings(p,7999999,v).refundCap,0);assert.equal(c.getEstimatedSavings(p,7999999,v).belowMinimum,true);}
 }
 const premium=offers.find(p=>p.offer_kind==='premium');assert.match(premium.verified_cards,/Signature delSol/);
});
const musicCampaign='6835e9541687c3e5',musicIds=['933d29a51e9f853a','dea403e299553e77','252153f5abe9bcd1'];
// Regression data is an immutable reviewed snapshot, not a promise that an expired
// campaign remains verified in the daily catalog forever. See fixture provenance.
const music=JSON.parse(fs.readFileSync(root+'/tests/fixtures/music-hall-reviewed-20261024.json','utf8'));
const musicAliases=Object.fromEntries([musicCampaign,...musicIds].map(id=>[id,musicCampaign]));
test('reviewed Music Hall snapshot preserves variant IDs and historical favorites',()=>{
 assert.equal(music.length,3);
 assert.deepEqual(music.map(p=>p.id).sort(),[...musicIds].sort());
 assert.equal(music.some(p=>p.id===musicCampaign),false,'old placeholder must be archived, not duplicate live campaign');
 const c=ctx(music,musicAliases);c.state.favorites=new Set([musicCampaign]);
 assert.deepEqual([...c.normalizeFavoriteIds([musicCampaign,...musicIds,'unrelated'])],[musicCampaign,'unrelated']);
 assert.ok(music.every(p=>c.isFavoritePromotion(p)));
 c.toggleFavorite(musicIds[1]);assert.ok(music.every(p=>!c.isFavoritePromotion(p)));
 c.toggleFavorite(musicIds[2]);assert.ok(music.every(p=>c.isFavoritePromotion(p)));
 assert.deepEqual([...c.state.favorites],[musicCampaign]);
});
test('Music Hall preserves audio restrictions and financing has no monetary saving',()=>{
 const c=ctx(music,musicAliases),rows=musicIds.map(id=>music.find(p=>p.id===id));
 assert.ok(rows.every(Boolean));
 const [base,audio,financing]=rows;
 assert.match(base.benefit_summary,/15%.*excepto equipos de audio/i);
 assert.match(audio.benefit_summary,/5%.*equipos de audio/i);
 assert.equal(financing.benefit_summary,'Hasta 12 cuotas sin intereses');
 for(const p of rows){assert.equal(p.source_verification,'official_document');assert.equal(p.source_warning||'','');}
 assert.equal(c.getEstimatedSavings(financing,1000000,c.getPromoVariants(financing)[0]).refundCap,0);
});

test('daily Music Hall catalog never restores reviewed identity to unconfirmed offers',()=>{
 for(const p of all.filter(p=>musicIds.includes(p.id))){
  if(p.source_verification==='official_document') assert.equal(p.campaign_id,musicCampaign);
  else assert.notEqual(p.campaign_id,musicCampaign,'uncertain source must not be silently promoted by a regression fixture');
 }
});
