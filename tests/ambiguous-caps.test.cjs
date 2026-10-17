const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('unresolved card-specific limits never become an uncapped savings estimate',()=>{
  const source=fs.readFileSync('app-web/app.js','utf8');
  const context={state:{uenoLevel:1},getSelectedUenoLevelDetails:()=>null,percentNumber:()=>20,getMainBenefit:()=> '20%',PaybackBenefits:{calculate:()=>{throw Error('Ambiguous limit must not be calculated');}}};
  vm.runInNewContext(source.slice(source.indexOf('function getEstimatedSavings('),source.indexOf('function getDetailRows(')),context);
  const result=context.getEstimatedSavings({bank:'Itaú',terms:{limits:[{kind:'purchase',amount:3000000},{kind:'purchase',amount:500000}]}},1000000);
  assert.equal(result.unconfirmed,true);
  assert.equal(result.refundCap,0);
});
