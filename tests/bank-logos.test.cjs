const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const catalog = JSON.parse(fs.readFileSync('public/promotions.json', 'utf8'));

for (const [folder, route] of [['app-web', 'app-web'], ['beta-web', 'beta']]) {
  test(folder + ' provides usable logo assets and renders no empty image', () => {
    const source = fs.readFileSync(folder + '/app.js', 'utf8');
    const block = (name) => source.match(new RegExp('^function ' + name + '\\([^]*?^}', 'm'))[0];
    const base = 'https://example.test/promo-bancos-py/' + route + '/';
    const context = {
      URL, bankLogoBase: base, escapeHtml: String, escapeAttribute: String,
      getBankLabel: String, getPromoCategoryGroup: () => 'Otros',
    };
    vm.runInNewContext(source.match(/^const bankThemes = \{[^]*?^\};/m)[0] + '\n' +
      block('getBankTheme') + '\n' + block('renderBankBar'), context);
    for (const bank of new Set(catalog.map(p => p.bank))) {
      const img = context.renderBankBar({bank}).match(/<img src="([^"]+)" data-bank-logo/);
      // Missing themes should show the bank name, not a broken icon.
      if (!img) {
        assert.ok(context.renderBankBar({bank}).includes('<strong>' + bank + '</strong>'));
        continue;
      }
      assert.ok(img[1].startsWith(base + 'assets/logos/'));
      const rel = img[1].slice(base.length);
      const asset = fs.readFileSync(folder + '/' + rel);
      if (rel.endsWith('.svg')) assert.match(asset.toString('utf8'), /<svg\b/);
      if (rel.endsWith('.png')) assert.equal(asset.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
      if (rel.endsWith('.webp')) assert.equal(asset.subarray(8, 12).toString(), 'WEBP');
    }
    for (const bank of ['Atlas', 'BNF', 'Bancop', 'Basa', 'Continental', 'Coop. Universitaria',
      'Familiar', 'GNB', 'Interfisa', 'Itaú', 'Solar', 'Sudameris']) {
      assert.match(context.renderBankBar({bank}), /<img src="[^"]+" data-bank-logo/);
    }
    assert.doesNotMatch(context.renderBankBar({bank:'No catalogado'}), /<img/);
  });
}
