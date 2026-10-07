const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app-web/app.js', 'utf8');
const campaign = 'aaaaaaaaaaaaaaaa';
const variants = [
  { id: 'bbbbbbbbbbbbbbbb', campaign_id: campaign, bank: 'Familiar', merchant_name: 'Comercio', verified_cards: 'Visa Platinum', benefit_summary: '25% de reintegro', promotion_days: ['jueves'], terms: { ends_on: '2026-12-31' } },
  { id: 'cccccccccccccccc', campaign_id: campaign, bank: 'Familiar', merchant_name: 'Comercio', verified_cards: 'Visa Oro', benefit_summary: '20% de reintegro', promotion_days: ['jueves', 'viernes'], terms: { ends_on: '2026-12-31' } },
];
function front(ids = [campaign]) {
  const saved = [], syncs = [];
  const ctx = { state: { promotions: variants, favorites: new Set(ids), favoriteAliases: {}, activeView: 'favorites' }, window: {}, STORAGE_KEYS: { favorites: 'favorites' }, saveStoredJson: (_, value) => saved.push(value), syncFavoriteAlerts: () => syncs.push([...ctx.state.favorites]), render() {}, els: {} };
  vm.runInNewContext(source.slice(source.indexOf('function favoriteKey('), source.indexOf('function matchesSelectedDay(')), ctx);
  vm.runInNewContext(source.slice(source.indexOf('function toggleFavorite('), source.indexOf('function getCategories(')), ctx);
  return { ctx, saved, syncs };
}
test('a legacy favorite selects all campaign variants and either heart toggles the whole campaign', () => {
  const { ctx, saved, syncs } = front();
  assert.ok(variants.every(ctx.matchesActiveView));
  ctx.toggleFavorite(variants[0].id);
  assert.ok(variants.every(p => !ctx.isFavoritePromotion(p)));
  ctx.toggleFavorite(variants[1].id);
  assert.ok(variants.every(ctx.isFavoritePromotion));
  assert.deepEqual([...ctx.state.favorites], [campaign]);
  assert.equal(saved.length, 2);
  assert.deepEqual(syncs, [[], [campaign]]);
});
test('variant and historical alias favorites collapse without discarding unrelated favorites', () => {
  const { ctx } = front();
  ctx.state.favoriteAliases = { old: 'older', older: variants[0].id };
  const normalized = ctx.normalizeFavoriteIds(['old', variants[0].id, variants[1].id, campaign, 'other']);
  assert.deepEqual([...normalized], [campaign, 'other']);
  ctx.state.favoriteAliases = { a: 'b', b: 'a' };
  assert.doesNotThrow(() => ctx.normalizeFavoriteIds(['a']));
});
test('account toggles use one campaign write and pass obsolete IDs for atomic cleanup', () => {
  const { ctx } = front([variants[0].id, variants[1].id]);
  const calls = [];
  ctx.PaybackBeta = ctx.window.PaybackBeta = { current: { favorites: [variants[0].id, variants[1].id] }, favorite: (...args) => { calls.push(args); return Promise.resolve(); } };
  ctx.toggleFavorite(variants[1].id);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], campaign);
  assert.equal(calls[0][1], false);
  assert.deepEqual(calls[0][2], variants.map(p => p.id));
});
test('today favorite count counts the campaign only once', () => {
  const { ctx } = front();
  Object.assign(ctx, { isActivePromotion: () => true, appliesToSelectedDay: () => true, PaybackPush: { enabled: () => false }, escapeHtml: value => value || '' });
  vm.runInNewContext(source.slice(source.indexOf('function renderFavoriteAlerts('), source.indexOf('function syncFavoriteAlerts(')), ctx);
  assert.match(ctx.renderFavoriteAlerts(), /1 favoritos disponibles hoy/);
});
test('notifications keep legacy favorites, combine only due variants, and retain eligibility', async () => {
  const { favoriteNotifications } = await import('../server/schedule.js');
  const thursday = new Date('2026-10-08T15:00:00Z');
  for (const favorites of [[campaign], variants.map(p => p.id), ['old']]) {
    const due = favoriteNotifications(variants, favorites, { old: variants[0].id }, 1, thursday);
    assert.equal(due.length, 1);
    assert.match(due[0].benefit, /25% de reintegro \(Visa Platinum\)/);
    assert.match(due[0].benefit, /20% de reintegro \(Visa Oro\)/);
  }
  const friday = favoriteNotifications(variants, [campaign], {}, 1, new Date('2026-10-09T15:00:00Z'));
  assert.equal(friday.length, 1);
  assert.equal(friday[0].benefit, '20% de reintegro (Visa Oro)');
  assert.deepEqual(favoriteNotifications(variants, [campaign], {}, 1, new Date('2026-10-10T15:00:00Z')), []);
});
test('expired and financing-only offers cannot create duplicate or misleading alerts', async () => {
  const { favoriteNotifications } = await import('../server/schedule.js');
  const promos = [...variants, { ...variants[0], id: 'dddddddddddddddd', benefit_summary: '50% de reintegro', terms: { ends_on: '2026-09-30' } }, { ...variants[0], id: 'eeeeeeeeeeeeeeee', benefit_summary: '6 cuotas sin intereses' }];
  const due = favoriteNotifications(promos, [campaign], {}, 1, new Date('2026-10-08T15:00:00Z'));
  assert.equal(due.length, 1);
  assert.doesNotMatch(due[0].benefit, /50%|cuotas/);
  assert.equal(favoriteNotifications([variants[0], { ...variants[0] }], [campaign], {}, 1, new Date('2026-10-08T15:00:00Z'))[0].benefit, '25% de reintegro (Visa Platinum)');
});
test('failed or rapid account changes restore the original equivalent favorite IDs', async () => {
  const betaSource = fs.readFileSync('app-web/beta-client.js', 'utf8');
  const ctx = { current: { email: 'owner@test.invalid', favorites: variants.map(p => p.id) }, changed() {}, event() {}, api: async () => { throw new Error('offline'); } };
  vm.runInNewContext(betaSource.slice(betaSource.indexOf('const favoriteWrites'), betaSource.indexOf('async function level(')), ctx);
  const first = ctx.favorite(campaign, false, variants.map(p => p.id));
  const second = ctx.favorite(campaign, true);
  const third = ctx.favorite(campaign, false);
  await Promise.allSettled([first, second, third]);
  assert.deepEqual([...ctx.current.favorites], variants.map(p => p.id));
});

test('source conflicts are withheld from automated discount notifications', async () => {
  const { favoriteNotifications } = await import('../server/schedule.js');
  const conflicted = variants.map(p => ({...p,source_warning:'PDF and listing disagree'}));
  assert.deepEqual(favoriteNotifications(conflicted,[campaign],{},1,new Date('2026-10-08T15:00:00Z')),[]);
});
