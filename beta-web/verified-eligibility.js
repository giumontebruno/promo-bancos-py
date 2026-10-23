const BNF='https://www.bnf.gov.py/uploads/Promocion_Reintegro_Frigorificos_2026_OCT_4204e066ab.pdf';
const CONT='https://www.bancontinental.com.py/api/comercios?_limit=-1';
const evidence={
 '41f18a27d2ea14dc':{bank:'BNF',source:BNF,percent:30,cards:['Visa Oro BNF','Visa Platinum BNF'],tier:'premium',purchaseCap:1000000,refundCap:300000,period:'mensual por cuenta',payment:'POS Bancard / Infonet, sin cuotas'},
 '41f18a27d2ea14dc-7b402b51':{bank:'BNF',source:BNF,percent:20,cards:['Visa Clásica BNF'],tier:'base',purchaseCap:1000000,refundCap:200000,period:'mensual por cuenta',payment:'POS Bancard / Infonet, sin cuotas'},
 '1342c43e226a7553':{bank:'Continental',source:CONT,percent:25,cards:['Privilege Continental'],tier:'premium',purchaseCap:500000,period:'semanal por cuenta',payment:'POS Dinelco físico; no app, online ni POS virtual',sourceRecord:1261}
};
function verified(p){const e=evidence[p.id];if(!e||p.bank!==e.bank||p.source_url!==e.source||!new RegExp('^'+e.percent+'%').test(p.benefit_summary))return null;return {...e,cards:[...e.cards]};}
function apply(promos){return promos.map(p=>{const e=verified(p);if(!e)return p;return {...p,verified_cards:e.cards,offer_kind:e.tier==='premium'?'premium':'base',offer_label:e.cards.join(' / '),eligibility_source:e.source};});}
function cards(p,variant){
 const scoped=variant?.cards || ((!variant?.kind || p.offer_kind===variant.kind) ? (p.verified_cards || p.terms?.cards) : null);
 const list=Array.isArray(scoped)?scoped:typeof scoped==='string'?[scoped]:[];
 const clean=list.map(x=>String(x).trim()).filter(x=>x.length>0&&x.length<=140&&!/[\d]+\s*%|\bGs[. ]|\b(?:viernes|lunes|martes|miércoles|jueves|sábado|domingo|vigencia|compra|reintegro|descuento|sucursal|condiciones)\b/i.test(x));
 return clean.length===list.length&&clean.length?[...new Set(clean)].join('; '):'Tarjetas válidas sin confirmar; consultá las bases';
}
const api={verified,evidence,apply,cards};if(typeof module==='object')module.exports=api;else window.PaybackEligibility=api;
