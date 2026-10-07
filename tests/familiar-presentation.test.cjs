const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app-web/app.js','utf8');
const context={state:{uenoLevel:1},PaybackBenefits:require('../app-web/benefit-rules.js'),getSelectedUenoLevelDetails:()=>null,
  normalizeDayName:s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()};
vm.createContext(context);
for(const name of ['getMainBenefit','getBenefitLines','getEstimatedSavings','percentNumber','getPromoVariants','isInstallmentsOnly']){
  const start=source.indexOf(`function ${name}(`);
  const end=source.indexOf('\nfunction ',start+1);
  vm.runInContext(source.slice(start,end),context);
}
const rows=JSON.parse(fs.readFileSync('tests/fixtures/familiar-variants.json','utf8'));
const byMerchant=name=>rows.filter(r=>r.bank==='Familiar'&&r.merchant_name===name);

test('Paraná shows 30%, exact refund and independent financing without savings',()=>{
  const parana=byMerchant('PARANÁ HOGAR');
  assert.equal(parana.length,3);
  const cash=parana.find(r=>r.percentages.length);
  assert.equal(context.getBenefitLines(cash,context.getPromoVariants(cash)[0])[0],'30% reintegro');
  assert.equal(context.getEstimatedSavings(cash,null,context.getPromoVariants(cash)[0]).refundCap,3000000);
  for(const installment of parana.filter(r=>!r.percentages.length)){
    assert.equal(context.isInstallmentsOnly(installment),true);
    assert.equal(context.getEstimatedSavings(installment).refundCap,0);
  }
});
test('Familiar base and Platinum have separate percentages, sections and caps',()=>{
  const town=byMerchant('DON TOWN');
  assert.equal(town.length,2);
  for(const promo of town){
    const variant=context.getPromoVariants(promo)[0];
    const premium=variant.kind==='premium';
    assert.equal(context.getBenefitLines(promo,variant)[0],premium?'25% reintegro':'20% reintegro');
    assert.equal(context.getEstimatedSavings(promo,null,variant).refundCap,premium?200000:120000);
  }
});
test('QR bonus stays explicit and never increases the unconditional estimate',()=>{
  for(const promo of byMerchant('CEROGRADO-PLAZA NORTE')){
    const variant=context.getPromoVariants(promo)[0];
    assert.match(context.getBenefitLines(promo,variant)[0],/\+ 5% con QR/);
    assert.equal(context.getEstimatedSavings(promo,null,variant).refundCap,variant.kind==='premium'?2500000:2000000);
  }
});
test('financing cannot show refund cap without a valid monetary percentage',()=>{
  const promo={bank:'Familiar',benefit_type:'cuotas_sin_intereses',benefit_summary:'Hasta 12 cuotas sin intereses',terms:{limits:[{kind:'refund',amount:3000000}]}};
  assert.equal(context.getEstimatedSavings(promo).refundCap,0);
});

test('unstructured card variants never imply an unlimited refund',()=>{
  const promo={bank:'Continental',benefit_summary:'20% reintegro',terms:{limits:[{kind:'purchase',amount:2000000}]}};
  const savings=context.getEstimatedSavings(promo,3000000,{kind:'premium',benefit:'25% reintegro'});
  assert.equal(savings.refundCap,0);
  assert.equal(savings.unconfirmed,true);
  assert.match(source,/if \(savings.unconfirmed\)/);
});

const reviews=JSON.parse(fs.readFileSync('data/reviewed_card_offers.json','utf8'));
const reviewedOffers=(bank,merchant)=>reviews.filter(r=>r.bank===bank&&r.merchant_name===merchant).flatMap(r=>r.offers.map(o=>({...o,bank:r.bank,merchant_name:r.merchant_name,terms:{limits:context.PaybackBenefits.explicitLimits(o.raw_detail)}})));
test('Moet scoped variants retain the shared 2m purchase limit',()=>{
  const offers=reviewedOffers('Continental','Moet Hennesy');
  assert.equal(offers.length,2);
  for(const promo of offers){
    const variant=context.getPromoVariants(promo)[0];
    const savings=context.getEstimatedSavings(promo,3000000,variant);
    assert.equal(savings.purchaseCap,2000000);
    assert.equal(savings.refundCap,variant.kind==='premium'?500000:400000);
    assert.equal(savings.capped,true);
  }
});
test('Sudameris ordinary and premium discounts stay separate from financing',()=>{
  for(const merchant of ['CONCEPTS LA CUADRITA','TATANO POSADA BOUTIQUE']){
    const offers=reviewedOffers('Sudameris',merchant);
    assert.equal(offers.length,3);
    assert.deepEqual(offers.filter(p=>!context.isInstallmentsOnly(p)).map(p=>context.getPromoVariants(p)[0].benefit),merchant.startsWith('CONCEPTS')?['20% de reintegro','25% de reintegro']:['20% de descuento','25% de descuento']);
    assert.equal(offers.filter(context.isInstallmentsOnly).length,1);
  }
});
test('Itau wallet bonus is explicit but excluded from unconditional savings',()=>{
  for(const promo of reviewedOffers('Itaú','Fuschia')){
    const variant=context.getPromoVariants(promo)[0];
    assert.match(context.getBenefitLines(promo,variant)[0],/Google Pay o Apple Pay/);
    assert.equal(context.getEstimatedSavings(promo,1000000,variant).refundCap,promo.effective_percent*10000);
  }
});
test('source conflicts suppress numeric estimates until verified',()=>{
  const promo={bank:'Familiar',benefit_summary:'25% de reintegro',source_warning:'Listado y PDF difieren'};
  assert.equal(context.getEstimatedSavings(promo,1000000).unconfirmed,true);
});
