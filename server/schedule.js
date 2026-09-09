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
  const summary = String(promo.benefit_summary || '');
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
  if (percentages.length !== 1 || Number(percentages[0].replace('%', '')) > 100) return '';
  if (!/reintegro|descuento/i.test(summary)) return '';
  return `${percentages[0]} de ${/reintegro/i.test(summary) ? 'reintegro' : 'descuento'}`;
}
