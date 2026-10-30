/* Conservative shared pilot. Evidence is supplied by the reviewed adapter, never inferred
   from brand proximity or geocoding. Missing evidence is not a negative eligibility rule. */
(function(root) {
  const norm = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();
  function evaluate(promo, context = {}) {
    const missing = [], denied = [];
    const proof = context.evidence;
    if (context.dateMatches === false) denied.push('La fecha o el día no aplica.');
    else if (context.dateMatches !== true) missing.push('Confirmar fecha y día.');
    if (!proof || !proof.source || promo.source_warning || promo.source_verification === 'unconfirmed') missing.push('Condiciones completas sin verificar.');
    if (!context.card) missing.push('Elegí una tarjeta exacta.');
    else if (proof?.cards?.length) {
      if (proof.uncertainCards?.some(card => norm(card) === norm(context.card))) missing.push('La fuente no aclara el beneficio y tope de esta tarjeta.');
      else if (!proof.cards.some(card => norm(card) === norm(context.card))) denied.push('La tarjeta no está incluida en estas condiciones verificadas.');
    } else missing.push('Confirmar tarjeta exacta en las bases.');
    if (!context.channel) missing.push('Elegí la forma de pago.');
    else if (proof?.channels?.length) {
      if (proof.excludedChannels?.includes(context.channel)) denied.push('La forma de pago no aplica.');
      else if (!proof.channels.includes(context.channel)) missing.push('La fuente no confirma esta forma de pago.');
    } else missing.push('Confirmar forma de pago en las bases.');
    if (!context.branch) missing.push('Confirmar sucursal adherida; un punto en el mapa no prueba participación.');
    else if (context.branch.match === false) denied.push('La sucursal no está vinculada a esta promoción.');
    else if (context.branch.match !== true || !context.branch.source) missing.push('Falta procedencia de la participación de esta sucursal.');
    if (!Number.isFinite(context.amount) || context.amount <= 0) missing.push('Ingresá el monto de compra.');
    else if (proof && Number.isFinite(proof.minimum) && context.amount < proof.minimum) denied.push('La compra no alcanza el mínimo.');
    const validPercent = Number.isFinite(proof?.percent) && proof.percent > 0 && proof.percent <= 100;
    const validCaps = proof && ['purchaseCap','refundCap'].every(key => proof[key] == null || (Number.isFinite(proof[key]) && proof[key] >= 0));
    if (!validPercent) missing.push('Porcentaje sin confirmar.');
    if (!validCaps) missing.push('Topes inválidos o ambiguos.');
    if (!Number.isFinite(proof?.minimum) || proof.minimum < 0) missing.push('Confirmar mínimo de compra o su ausencia.');
    // Available monthly/account caps cannot be derived from published maximums.
    if (proof?.period && (!Number.isFinite(context.remainingCap) || context.remainingCap < 0)) missing.push('Confirmar saldo del tope compartido; no consultamos tus consumos.');
    let estimate = null;
    if (!denied.length && proof && Number.isFinite(context.amount) && context.amount > 0 && validPercent && validCaps) {
      if (proof.purchaseCap > 0 || proof.refundCap > 0) {
        estimate = Math.round(Math.min(context.amount, proof.purchaseCap || Infinity) * proof.percent / 100);
        if (proof.refundCap > 0) estimate = Math.min(estimate, proof.refundCap);
        if (Number.isFinite(context.remainingCap)) estimate = Math.min(estimate, Math.max(0,context.remainingCap));
      } else missing.push('Confirmar topes antes de estimar el ahorro.');
    }
    if (proof?.additionalConditionsVerified !== true) missing.push('Revisá las demás condiciones de las bases.');
    return {status: denied.length ? 'not_applies' : missing.length ? 'needs_confirmation' : 'applies', reasons: [...denied, ...missing], estimate, source: proof?.source || null};
  }
  function sourceSummary(sources) {
    if (!sources || !Object.keys(sources).length) return 'No pudimos comprobar el estado de las fuentes. La fecha del catálogo no confirma cada promoción.';
    const incomplete = Object.entries(sources).filter(([,entry]) => entry.status !== 'fetched');
    return incomplete.length ? 'Fuentes con actualización incompleta: ' + incomplete.map(([bank,entry]) => `${bank} (${entry.status === 'failed' ? 'falló' : 'parcial'}; última extracción completa ${String(entry.checked_at || 'sin fecha').slice(0,10)})`).join('; ') + '. Confirmá las bases antes de comprar.' : 'La extracción de las fuentes terminó; no confirma disponibilidad ni consumos de tu cuenta.';
  }
  const api = {evaluate,sourceSummary};
  if (typeof module === 'object' && module.exports) module.exports = api; else root.PaybackSupermarkets = api;
})(typeof window === 'undefined' ? globalThis : window);
