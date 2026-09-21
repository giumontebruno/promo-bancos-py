const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app-web/app.js','utf8');

test('search ignores bank and category but empty search respects them', () => {
  const ctx = {state:{query:'farmacia',activeBank:'BNF',activeCategory:'Combustible'}, PREMIUM_CATEGORY:'Black', getPromoCategoryGroup:p=>p.category};
  vm.runInNewContext(source.slice(source.indexOf('function matchesBank('),source.indexOf('function sectionPromotions(')),ctx);
  const promo = {bank:'Itaú',category:'Farmacias'};
  assert.equal(ctx.matchesBank(promo),true);
  assert.equal(ctx.matchesCategory(promo),true);
  ctx.state.query='';
  assert.equal(ctx.matchesBank(promo),false);
  assert.equal(ctx.matchesCategory(promo),false);
});

test('financing restricted to a weekday does not enter today discounts', () => {
  const ctx = {state:{activeCategory:'Farmacias',activeDay:'hoy'},PREMIUM_CATEGORY:'Black',getTodayInParaguay:()=> 'lunes',getTodayLabel:()=> 'Hoy', isOtherCitiesOnly:()=>false,isEveryDayPromotion:()=>false,isInstallmentsOnly:p=>p.installments,sortByDayDisplayPriority:()=>0};
  vm.runInNewContext(source.slice(source.indexOf('function sectionPromotions('),source.indexOf('function sortPremiumPromotions(')),ctx);
  const sections = ctx.sectionPromotions([{id:'asismed',installments:true}]);
  assert.equal(sections[0][1].length,0);
  assert.equal(sections.find(s=>s[0].startsWith('Cuotas'))[1][0].id,'asismed');
});

function favoriteContext(api) {
  const text = fs.readFileSync('app-web/beta-client.js','utf8');
  const ctx = {current:{email:'owner@test.invalid',favorites:[]},changed(){},event(){},api};
  vm.runInNewContext(text.slice(text.indexOf('const favoriteWrites'),text.indexOf('async function level(')),ctx);
  return ctx;
}

test('favorite confirmation is immediate and a failed save is rolled back', async () => {
  let reject;
  const ctx = favoriteContext(()=>new Promise((_,r)=>{reject=r;}));
  const pending = ctx.favorite('abc',true);
  assert.equal(ctx.current.favorites.includes('abc'),true);
  await new Promise(setImmediate);
  reject(new Error('offline'));
  await assert.rejects(pending);
  assert.equal(ctx.current.favorites.includes('abc'),false);
});

test('rapid favorite changes restore last confirmed state after failures', async () => {
  const ctx = favoriteContext(async()=>{throw new Error('offline');});
  const first=ctx.favorite('abc',true), second=ctx.favorite('abc',false), third=ctx.favorite('abc',true);
  await Promise.allSettled([first,second,third]);
  assert.equal(ctx.current.favorites.includes('abc'),false);
});
