const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
test('explicit GNB/Basa repair markers scope push refresh but keep default all-bank refresh', () => {
  const workflow = readFileSync('.github/workflows/refresh-promotions.yml', 'utf8');
  for (const bank of ['gnb', 'basa']) {
    assert.ok(workflow.includes(`github.event_name == 'push' && contains(github.event.head_commit.message, '[refresh:${bank}]') && '${bank}'`));
  }
  assert.ok(workflow.includes("&& 'basa' || '' }}"));
  assert.match(workflow, /if \[ -n "\$REFRESH_SOURCE" \]; then\s+xvfb-run -a python promo_backend\/run_all.py "\$REFRESH_SOURCE"\s+else\s+xvfb-run -a python promo_backend\/run_all.py\s+fi/);
  assert.ok(workflow.includes('GEOCODE_LIMIT: "0"'));
  assert.ok(workflow.includes("github.event_name == 'push' && '0' || '60'"));
});
