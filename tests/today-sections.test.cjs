const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('unfiltered home keeps every daily promotion instead of selecting five', () => {
  const source = fs.readFileSync('app-web/app.js', 'utf8');
  const context = {
    state: {activeView: 'today', activeBank: 'Todos', activeCategory: 'Todas', query: ''},
    sectionPromotions: promos => [['Hoy', promos, 'featured']],
    buildHomeSections: () => { throw new Error('Truncated home must not be used'); },
  };
  vm.runInNewContext(source.slice(source.indexOf('function buildResultSections('), source.indexOf('function buildSearchSections(')), context);
  const promos = Array.from({length: 12}, (_, i) => ({id: String(i)}));
  promos.push({id: 'f0b8d88ff2a85ff1', merchant_name: 'Punto Farma'});
  const sections = context.buildResultSections(promos);
  assert.equal(sections[0][1].length, 13);
  assert.equal(sections[0][1].at(-1).merchant_name, 'Punto Farma');
});
