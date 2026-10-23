(function(root) {
  'use strict';
  function today(now = new Date()) {
    const p = new Intl.DateTimeFormat('en-CA', {timeZone:'America/Asuncion',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
    return ['year','month','day'].map(k => p.find(x => x.type === k).value).join('-');
  }
  function valid(iso) { return /^\d{4}-\d{2}-\d{2}$/.test(iso || '') && !Number.isNaN(Date.parse(iso+'T12:00:00Z')) && new Date(iso+'T12:00:00Z').toISOString().slice(0,10) === iso; }
  function shift(iso, days) { if(!valid(iso)) return ''; const d=new Date(iso+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+days);return d.toISOString().slice(0,10); }
  function weekday(iso) { return new Intl.DateTimeFormat('es-PY',{weekday:'long',timeZone:'UTC'}).format(new Date(iso+'T12:00:00Z')); }
  function matches(iso, days, monthDays = [], lastDays = 0, rules = []) {
    if(!valid(iso)) return false;
    const d=new Date(iso+'T12:00:00Z'),n=d.getUTCDate(),end=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)).getUTCDate();
    if(monthDays.length || lastDays) return monthDays.includes(n) || (lastDays>0 && n>end-lastDays);
    const day=weekday(iso),norm=v=>String(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
    if(rules.length) return rules.some(r=>norm(r.day)===norm(day) && (r.ordinal===-1?n+7>end:Math.ceil(n/7)===r.ordinal));
    return days.some(x=>norm(x)===norm(day));
  }
  const api={today,valid,shift,weekday,matches}; if(typeof module==='object') module.exports=api;else root.PaybackDates=api;
})(typeof window==='object'?window:globalThis);
