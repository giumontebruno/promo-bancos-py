const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("beta-web/app.js", "utf8");
const overlay = JSON.parse(fs.readFileSync("beta-web/reviewed-map-delta.json", "utf8"));
function scoped(fetch) {
  const context = { fetch, AbortSignal };
  const start = source.indexOf("const MAP_REVIEW_URL");
  const end = source.indexOf("function appendReviewedPromotions");
  const codeEnd = source.indexOf("\n}", end) + 2;
  return vm.runInNewContext(source.slice(start,codeEnd)+"; ({loadMapReview,addReviewedRows,appendReviewedPromotions})",context);
}
const ok = data => ({ok:true,json:async()=>data});
test("reviewed rows hydrate scoped contracts and obey shared suspension policy", async () => {
  const api = scoped(async url => ok(url.includes("reviewed-map") ? overlay : {banks:["SOLAR"]}));
  const data = await api.loadMapReview();
  assert.equal(data.promotions.length,0);
  assert.equal(data.locations.length,178);
  for(const row of data.locations) assert.ok(row.promotion_ids.every(id => row.promotion_contracts[id]));
});
test("optional overlay fails closed if data or policy is unavailable", async () => {
  assert.equal(await scoped(async url => url.includes("reviewed-map") ? ok(overlay):{ok:false}).loadMapReview(),null);
  assert.equal(await scoped(async () => {throw Error("Offline")}).loadMapReview(),null);
});
test("published locations win collisions, and future live or withheld promo replaces archive campaign", () => {
  const api = scoped(() => {});
  let orig = {id:"1",lat:3}, update = {id:"1",lat:4}, added = {id:"2",lat:5};
  const lines = api.addReviewedRows([orig],[update,added,added]);
  assert.equal(lines.length,2);
  assert.equal(lines[0],orig);
  assert.equal(lines[1],added);
  const live = {id:"changed",bank:"SOLAR",merchant_name:" Copetrol ",source_verification:"unconfirmed"};
  assert.equal(api.appendReviewedPromotions([live],overlay.promotions).length,1);
});
test("release adds only the reviewed cards and geographic bindings", async () => {
  const api = scoped(async url => ok(url.includes("reviewed-map") ? overlay : {banks:["ueno bank"]}));
  const data = await api.loadMapReview();
  assert.equal(data.promotions.length,3);
  assert.equal(data.locations.length,179);
  assert.equal(data.locations.filter(row => row.bank === "Solar").length,1);
  assert.ok(data.locations.every(row => row.participation_ends_on && row.promotion_ids.length));
});
