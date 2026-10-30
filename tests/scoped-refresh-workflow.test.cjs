const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
test('explicit GNB repair marker scopes push refresh but keeps default all-bank refresh', () => {
  const workflow = readFileSync('.github/workflows/refresh-promotions.yml', 'utf8');
  assert.ok(workflow.includes("github.event_name == 'push' && contains(github.event.head_commit.message, '[refresh:gnb]') && 'gnb' || ''"));
  assert.match(workflow, /if \[ "\$REFRESH_SOURCE" = "gnb" \]; then\s+xvfb-run -a python promo_backend\/run_all.py gnb\s+else\s+xvfb-run -a python promo_backend\/run_all.py\s+fi/);
  assert.ok(workflow.includes('GEOCODE_LIMIT: "0"'));
  assert.ok(workflow.includes("github.event_name == 'push' && '0' || '60'"));
});
