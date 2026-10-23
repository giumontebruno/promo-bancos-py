const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('beta-web/app.js','utf8');

test('search and empty search both respect bank and category', () => {
  const ctx = {state:{query:'farmacia',activeBank:'BNF',activeCategory:'Combustible'}, PREMIUM_CATEGORY:'Black', getPromoCategoryGroup:p=>p.category};
  vm.runInNewContext(source.slice(source.indexOf('function matchesBank('),source.indexOf('function sectionPromotions(')),ctx);
  const promo = {bank:'Itaú',category:'Farmacias'};
  assert.equal(ctx.matchesBank(promo),false);
  assert.equal(ctx.matchesCategory(promo),false);
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

