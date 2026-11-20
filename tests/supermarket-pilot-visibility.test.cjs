const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

for (const surface of ['app-web','beta-web']) {
  const html = fs.readFileSync(path.join(__dirname, '..', surface, 'index.html'), 'utf8');
  const script = fs.readFileSync(path.join(__dirname, '..', surface, 'app.js'), 'utf8');
  test(`${surface}: purchase pilot controls are inert unless explicitly enabled`, () => {
    const template = html.match(/<template id="supermarketPilotTemplate" data-enabled="false">([\s\S]*?)<\/template>/);
    assert.ok(template);
    const live = html.replace(template[0], '');
    for (const id of ['pilotEnabled','pilotCard','pilotChannel','pilotAmount','pilotReset']) {
      assert.ok(template[1].includes(`id="${id}"`));
      assert.ok(!live.includes(`id="${id}"`));
    }
    for (const id of ['searchInput','bankSelect','categorySelect','cardSelect']) assert.ok(live.includes(`id="${id}"`));
    const hook = script.slice(script.indexOf('const supermarketPilotTemplate ='), script.indexOf('for (const id of ["pilotEnabled"'));
    for (const [flag, expected] of [['false',0],['true',1]]) {
      let mounted = 0;
      const content = {cloneNode: deep => { assert.equal(deep,true); return {}; }};
      vm.runInNewContext(hook, {document:{getElementById: () => ({dataset:{enabled:flag},content,replaceWith:()=>mounted++})}});
      assert.equal(mounted,expected);
    }
    const filter = script.match(/function matchesSupermarketPilot\(promo\) \{[\s\S]*?\n\}/)?.[0];
    const assessment = script.match(/function getSupermarketAssessment\(promo\) \{[\s\S]*?\n\}/)?.[0];
    const context = {document:{getElementById:()=>null}};
    vm.runInNewContext(`${filter}\n${assessment}`,context);
    assert.equal(context.matchesSupermarketPilot({category:'restaurants'}),true);
    assert.equal(context.getSupermarketAssessment({category:'supermercados'}),null);
  });
}
