(function(root){
 'use strict';
 function firstName(account){return String(account?.givenName||'').trim()||String(account?.name||'').trim().split(/\s+/)[0]||'';}
 function next({today,items,key,eligible,shift,horizon=90}){
  const limit=Math.max(1,Math.min(90,horizon));
  for(let offset=1;offset<=limit;offset++){
   const date=shift(today,offset),seen=new Set(),matches=[];
   for(const item of items){const id=key(item);if(!seen.has(id)&&eligible(item,date)){seen.add(id);matches.push(item);}}
   if(matches.length)return {date,items:matches,horizon:limit};
  }
  return {date:null,items:[],horizon:limit};
 }
 function purchaseCaps(promo){return (promo.terms?.limits||[]).filter(l=>l.kind==='purchase'&&Number(l.amount)>0&&l.currency&&/compra/i.test(l.evidence||'')).map(l=>({amount:Number(l.amount),currency:l.currency,period:l.period||null,evidence:l.evidence}));}
 const api={firstName,next,purchaseCaps};if(typeof module==='object')module.exports=api;else root.PaybackProfile=api;
})(typeof window==='object'?window:globalThis);
