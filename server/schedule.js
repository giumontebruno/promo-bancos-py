const DAYS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
export function todayParts(now = new Date()) {
  const formatted = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Asuncion', year: 'numeric', month: '2-digit', day: '2-digit' }).format(now);
  const date = new Date(`${formatted}T12:00:00Z`);
  return { iso: formatted, day: date.getUTCDate(), weekday: DAYS[date.getUTCDay()], date };
}
export function isDue(promo, now = new Date()) {
  const today = todayParts(now);
  const terms = promo.terms || {};
  if (!terms.ends_on || terms.conflicting_dates || terms.ends_on < today.iso || (terms.starts_on && terms.starts_on > today.iso)) return false;
  if (promo.month_days?.length) return promo.month_days.includes(today.day);
  if (promo.ordinal_weekdays?.length) {
    return promo.ordinal_weekdays.some(rule => rule.day === today.weekday && (rule.ordinal === -1
      ? new Date(today.date.getTime() + 7 * 86400000).getUTCMonth() !== today.date.getUTCMonth()
      : Math.ceil(today.day / 7) === rule.ordinal));
  }
  return (promo.promotion_days || []).includes(today.weekday);
}
export function notificationBenefit(promo, level) {
  if (promo.source_warning) return ''; // Do not notify disputed benefits as confirmed offers.
  const summary = String(promo.benefit_summary || '').replace(/\s+/g, ' ').trim();
  if (promo.bank === 'ueno bank' && promo.level_rules) {
    const rows = promo.level_benefits?.filter(row => row.level === level) || [];
    if (rows.length === 1) return `${rows[0].percent}% de reintegro · Nivel ${level}`;
    const match = promo.level_rules.match(new RegExp(`nivel\\s*${level}\\s*[:\\-]?\\s*(\\d{1,2})\\s*%`, 'i'));
    if (match) return `${match[1]}% de reintegro · Nivel ${level}`;
    const all = promo.level_rules.match(/nivel\s*1\s+al\s+5\s*:?\s*(\d{1,2})\s*%/i);
    if (all) return `${all[1]}% de reintegro`;
    return '';
  }
  const percentages = [...new Set((summary.match(/\d{1,3}\s*%/g) || []).map(s => s.replace(/\s/g, '')))];
  if (!percentages.length || percentages.some(value => Number(value.replace('%', '')) > 100)) return '';
  if (!/reintegro|descuento|ahorro|pago con qr/i.test(summary) || summary.length > 350) return '';
  // Preserve payment and product qualifiers instead of promising the highest rate to everyone.
  return promo.campaign_id && promo.verified_cards ? `${summary} (${promo.verified_cards})` : summary;
}

export function favoriteNotifications(promotions, savedIds, aliases = {}, level = 1, now = new Date()) {
  const favoriteKey = promo => promo.campaign_id || promo.id;
  const keys = new Map(promotions.map(promo => [promo.id, favoriteKey(promo)]));
  const favorites = new Set(savedIds.map(original => {
    let id = original;
    const seen = new Set();
    while (aliases[id] && !seen.has(id)) {
      seen.add(id);
      id = aliases[id];
    }
    return keys.get(id) || id;
  }));
  const campaigns = new Map();
  for (const promo of promotions) {
    const key = favoriteKey(promo);
    if (!favorites.has(key) || !isDue(promo, now)) continue;
    const benefit = notificationBenefit(promo, level);
    if (!benefit) continue;
    const entry = campaigns.get(key) || { promo, benefits: new Set() };
    entry.benefits.add(benefit);
    campaigns.set(key, entry);
  }
  // Group only offers due today and keep every card/payment qualifier. A campaign
  // gets one line even when several variants are eligible on the same date.
  return [...campaigns.values()].map(({ promo, benefits }) => ({ promo, benefit: [...benefits].join(' / ') }));
}

