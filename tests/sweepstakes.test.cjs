const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('verified sweepstakes never enter savings even when their conditions mention discounts',()=>{
 const source=fs.readFileSync('app-web/app.js','utf8');
 const start=source.indexOf('function isDisplayablePromotion(');
 const end=source.indexOf('\nfunction ',start+10);
 const context={};vm.runInNewContext(source.slice(start,end),context);
 assert.equal(context.isDisplayablePromotion({benefit_type:'sorteo',benefit_summary:'Sin descuento ni premio garantizado',raw_detail:'20% unrelated mention'}),false);
});
