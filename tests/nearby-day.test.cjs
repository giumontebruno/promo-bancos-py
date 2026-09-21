const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function setup() {
  const source = fs.readFileSync('app-web/app.js', 'utf8');
  const context = {
    state: { activeDay: 'hoy', query: '', promotions: [] },
    shouldShowPromotion: p => !p.expired,
    matchesBank: () => true,
    matchesCategory: () => true,
    matchesQuery: () => true,
    normalizeDayName: text => text.toLowerCase(),
    getPromoCategoryGroup: p => p.category,
    getMonthDays: p => p.monthDays || [],
    getParaguayMonthDay: () => 21,
    getOrdinalWeekdayRules: () => [],
    passesOrdinalDayRule: () => true,
    getTodayInParaguay: () => 'lunes',
    inferPromotionDaysFromText: p => p.days,
  };
  for (const [start, end] of [
    ['appliesToSelectedDay', 'isTodayOrdinalWeekday'],
    ['buildNearbyPromoIndex', 'getPromotionsForLocation'],
  ]) {
    vm.runInNewContext(source.slice(source.indexOf(`function ${start}(`), source.indexOf(`function ${end}(`)), context);
  }
  return context;
}

test('nearby Hoy uses the Paraguay weekday and calendar dates', () => {
  const c = setup();
  assert.equal(c.matchesNearbyDay({ days: ['lunes'] }), true);
  assert.equal(c.matchesNearbyDay({ days: ['jueves'] }), false);
  assert.equal(c.matchesNearbyDay({ days: ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'] }), true);
  assert.equal(c.matchesNearbyDay({ monthDays: [21] }), true);
  assert.equal(c.matchesNearbyDay({ monthDays: [24] }), false);
  c.state.activeDay = 'jueves';
  assert.equal(c.matchesNearbyDay({ days: ['jueves'] }), true);
  assert.equal(c.matchesNearbyDay({ days: ['lunes'] }), false);
});

test('map source index excludes other weekdays even with a search query', () => {
  const c = setup();
  c.state.query = 'farmacia';
  c.state.promotions = [
    { id: 'monday', bank: 'BNF', category: 'Farmacias', days: ['lunes'] },
    { id: 'thursday', bank: 'BNF', category: 'Farmacias', days: ['jueves'] },
    { id: 'expired', bank: 'BNF', category: 'Farmacias', days: ['lunes'], expired: true },
  ];
  assert.equal(JSON.stringify([...c.buildNearbyPromoIndex().values()].flat().map(p => p.id)), '["monday"]');
  c.state.activeDay = 'jueves';
  assert.equal(JSON.stringify([...c.buildNearbyPromoIndex().values()].flat().map(p => p.id)), '["thursday"]');
});
