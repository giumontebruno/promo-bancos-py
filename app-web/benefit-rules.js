(function (root) {
  "use strict";
  const moneyPattern = /(?:Gs\.?|G\.|guaran[ií]es)\s*([0-9]+(?:[. ,][0-9]{3})*)/gi;
  function normalize(value) {
    return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }
  function explicitLimits(text) {
    const result = [];
    const labels = /(?:tope|l[ií]mite)(?:\s+(?:m[aá]ximo|mensual|semanal|diario))?\s+(?:de\s+)?(?:compra|reintegro)|reintegro\s+m[aá]ximo|(?:compra|monto)\s+m[ií]nimo/gi;
    const matches = [...String(text || "").matchAll(labels)];
    matches.forEach((match, index) => {
      const evidence = text.slice(match.index, matches[index + 1]?.index ?? text.length).split(";")[0];
      const amounts = [...evidence.matchAll(moneyPattern)];
      if (amounts.length !== 1) return;
      const label = normalize(match[0]);
      result.push({ kind: label.includes("minimo") ? "minimum" : label.includes("reintegro") ? "refund" : "purchase",
        amount: Number(amounts[0][1].replace(/\D/g, "")), evidence,
        period: normalize(evidence).match(/mensual|semanal|diario/)?.[0] || null });
    });
    return result;
  }
  function uniqueLimit(limits, kind) {
    const values = [...new Set(limits.filter((limit) => limit.kind === kind).map((limit) => Number(limit.amount)))];
    return values.length === 1 ? values[0] : 0;
  }
  function calculate({ percent, purchaseCap = 0, refundCap = 0, minimum = 0, amount = null }) {
    const rate = Number(percent);
    if (!Number.isFinite(rate) || rate <= 0 || rate > 100) return { estimated: 0, capped: false, belowMinimum: false };
    const spend = amount == null ? purchaseCap : Number(amount);
    if (!Number.isFinite(spend) || spend < 0) return { estimated: 0, capped: false, belowMinimum: false };
    const belowMinimum = spend > 0 && spend < minimum;
    const eligible = purchaseCap ? Math.min(spend, purchaseCap) : spend;
    const gross = Math.round(eligible * rate / 100);
    return { estimated: belowMinimum ? 0 : refundCap ? Math.min(gross, refundCap) : gross,
      capped: (purchaseCap > 0 && spend > purchaseCap) || (refundCap > 0 && gross > refundCap), belowMinimum };
  }
  function normalizeText(value) {
    let text = String(value || "").replace(/\s+/g, " ").trim();
    if (text && text === text.toUpperCase()) text = text.toLowerCase();
    const brands = { visa: "Visa", mastercard: "Mastercard", bnf: "BNF", qr: "QR", pos: "POS",
      "apple pay": "Apple Pay", "google pay": "Google Pay", "personal bank": "Personal Bank" };
    for (const [name, formatted] of Object.entries(brands)) text = text.replace(new RegExp(`\\b${name}\\b`, "gi"), formatted);
    text = text.replace(/,\s*\./g, ".").replace(/(\d)\s+%/g, "$1%");
    return text.charAt(0).toUpperCase() + text.slice(1);
  }
  const api = { explicitLimits, uniqueLimit, calculate, normalizeText };
  root.PaybackBenefits = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);
